---
title: Restore the Primary Tray Window on a Second Launch
date: 2026-08-26
category: ui-bugs
module: voice_to_text
problem_type: ui_bug
component: frontend
symptoms:
  - Launching the app while its primary tray instance was hidden showed a dialog and exited instead of activating the existing GUI.
  - Retaining the duplicate process's opened mutex handle could extend the named object's lifetime and make later launches report a stale running instance.
root_cause: missing_workflow_step
resolution_type: code_fix
severity: medium
related_components: [service_layer]
tags: [single-instance, tray-app, window-activation, named-mutex, named-event, handle-lifetime, ui-thread-handoff, windows]
---

# Restore the Primary Tray Window on a Second Launch

## Problem

MoneyPenny must remain single-instance because two processes registering the same global hotkey can both react and type duplicate text (`voice_to_text.py:115-121`). Exclusion alone still made a normal taskbar relaunch feel broken: a second launch needed to activate the existing GUI and exit cleanly, without starting another listener or leaving a modal “already running” interaction.

Local Git history records the activation repair in commit `552a34b`, later included by the merge commit labeled PR #2. Historical dialog and handle-lifetime reports are attributed context; current code and tests are the behavioral evidence.

## Symptoms

- A second process must not reach application construction, hotkey registration, or tray startup. The entry path exits when mutex acquisition finds an existing owner (`voice_to_text.py:1924-1931`).
- Exiting alone did not satisfy the user's relaunch intent when the existing window was hidden. The current duplicate path signals activation before exit (`voice_to_text.py:1924-1927`).
- `CreateMutexW` returns the duplicate process a handle to the existing named mutex. Retaining it can extend the kernel object's lifetime after the primary exits; the current path closes it immediately (`voice_to_text.py:137-148`).
- The activation listener runs off-thread, while Tk window operations must run on the GUI thread (`voice_to_text.py:1872-1898`, `gui.py:1182-1205`).

The Windows tests verify mutex rejection and event signaling but patch `_focus_existing_window()` (`tests/test_single_instance.py:37-56`). They do not prove end-to-end desktop restoration or foreground focus.

## What Didn't Work

- A mutex alone answered “may this process start?” but could not ask the primary to reveal its hidden window.
- The historical second-process dialog left the primary hidden and made a relaunch behave unlike activation (`CHANGELOG.md`).
- Keeping the duplicate alive for a dialog amplified the handle-lifetime mistake: its handle still referenced the same kernel object and needed explicit closure (`voice_to_text.py:140-148`).
- Restoring Tk directly from a blocking listener would cross the GUI thread boundary. The wait loop and widget operations require a thread-safe handoff (`voice_to_text.py:1877-1898`, `gui.py:1198-1205`).
- Treating “restore requested” and “foreground focus obtained” as one operation hid Windows foreground restrictions. The primary restores through IPC, while the user-launched secondary separately attempts the foreground request (`voice_to_text.py:181-218`).

## Solution

### 1. Keep exclusion and handle ownership explicit

The primary creates a named mutex and retains its handle. When `CreateMutexW` reports `ERROR_ALREADY_EXISTS`, the duplicate immediately closes the handle it just opened and returns `None`; only a new mutex handle is returned to the primary (`voice_to_text.py:115-149`). Main interprets `None` as “activate and exit,” so it never constructs another app instance (`voice_to_text.py:1924-1931`).

The tests use UUID-suffixed `Local\` names to avoid real application objects and verify that the first lock yields a handle while the second is rejected (`tests/test_single_instance.py:11-43`).

### 2. Add explicit activation IPC

The primary creates an auto-reset, initially nonsignaled named event (`voice_to_text.py:156-175`). A duplicate opens that event with modify permission, sets it, closes its event handle, and then attempts the separate focus operation (`voice_to_text.py:181-218`). The event test confirms that signaling is observable through `WaitForSingleObject(..., 0)` (`tests/test_single_instance.py:44-56`).

The mutex and event have different contracts: the mutex answers whether a process may become primary; the event tells the existing primary to show its GUI.

### 3. Restore through a Tk-safe handoff

The primary runs a daemon listener that waits on the event and calls `gui.request_activation()` (`voice_to_text.py:1872-1898`). That method only sets a thread-safe flag. A recurring Tk `after()` callback polls the flag on the GUI thread and invokes `_deiconify()` there (`gui.py:1182-1205`). The background listener never directly manipulates widgets.

### 4. Attempt focus from the user-launched process

After signaling, the duplicate searches by the known window title for a bounded interval. If found, it shows or restores the window, raises it, and requests foreground status (`voice_to_text.py:221-257`). This complements the primary-side restore request.

## Why This Works

The design separates process safety from activation UX. The mutex prevents duplicate app construction and hotkey listeners (`voice_to_text.py:115-149`, `voice_to_text.py:1924-1931`); the event adds one-way activation without weakening exclusion (`voice_to_text.py:156-218`).

Immediate closure of the duplicate mutex handle preserves named-object lifetime semantics: the primary's handle remains authoritative, and the secondary does not accidentally keep the object alive (`voice_to_text.py:137-149`).

The event is auto-reset because `CreateEventW` receives false for manual reset (`voice_to_text.py:163-172`). Each observed request releases the listener once before it waits again (`voice_to_text.py:1882-1891`).

The flag-and-poll bridge respects Tk's threading boundary. The worker performs only the Windows wait and flag set; the scheduled callback clears the flag and performs GUI operations on the main thread (`voice_to_text.py:1877-1898`, `gui.py:1182-1205`).

The tests exercise real Windows named objects with isolated names, directly verifying mutex exclusion and event signaling (`tests/test_single_instance.py:11-56`). Actual focus remains source-grounded rather than end-to-end verified because the test stubs the focus helper (`tests/test_single_instance.py:49-50`). The complete Windows suite passed all 46 tests after the correction-dialog visibility regression was added.

## Prevention

- Keep three separate contracts: exclusion, activation IPC, and GUI-thread handoff.
- Whenever named-object code changes, give every returned handle a clear owner and close point. Preserve the immediate close on the duplicate mutex branch (`voice_to_text.py:137-148`).
- Add a lifecycle regression that closes the primary handle and proves a fresh acquisition succeeds if this area changes; the current tests verify rejection but not post-primary reacquisition (`tests/test_single_instance.py:31-43`).
- Keep tests isolated with unique `Local\` names and close all handles during teardown (`tests/test_single_instance.py:13-35`).
- Never call Tk methods from the listener thread; cross a thread-safe signal and execute widget work through `after()` (`gui.py:1182-1205`).
- Calibrate focus claims to verification. A real restore/focus guarantee requires a desktop-level test covering hidden and minimized states plus Windows foreground restrictions (`voice_to_text.py:221-257`).

## Related Issues

- [LESSONS_LEARNED.md](../../../LESSONS_LEARNED.md) records the original tray confusion and duplicate-handle failure, but its dialog-era UX guidance is stale.
- [README.md](../../../README.md) documents the current user-visible restore/focus behavior and hide-versus-quit distinction.
- [bound-correction-learning-to-confirmed-direct-edits.md](../design-patterns/bound-correction-learning-to-confirmed-direct-edits.md) contains an adjacent example of handing background-originated work to Tk's main thread.
