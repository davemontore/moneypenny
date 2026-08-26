---
title: Bound Correction Learning to Confirmed Direct Edits
date: 2026-08-26
category: design-patterns
module: voice_to_text
problem_type: design_pattern
component: service_layer
severity: medium
applies_when:
  - Inferring a reusable correction from edits made immediately after application-injected text.
  - Observing keyboard input across applications without reliable access to every control's edit history or semantic intent.
  - Persisting inferred behavior would affect future output and therefore requires explicit confirmation.
tags: [correction-learning, backspace-retype, bounded-inference, user-confirmation, context-cancellation, secure-input, whole-word-diff, cross-application]
---

# Bound Correction Learning to Confirmed Direct Edits

## Context

MoneyPenny needed to learn when a user immediately corrected freshly dictated text. A global keyboard hook can see physical key events, but it does not provide a reliable, application-independent model of document contents, selections, caret movement, editor undo behavior, mouse edits, or focus transitions. The implemented design therefore recognizes only a short, direct Backspace-and-retype correction at the original caret (`voice_to_text.py:511-519`).

Local Git history records the design in commit `552a34b`, later included by the merge commit labeled PR #2. Current source and tests—not historical acceptance statements—are the authority for the behavior documented here.

## Guidance

Use an observe–suggest–confirm–persist boundary whenever learning from global input events cannot be made universally reliable.

### Observe only a bounded direct edit

Arm recognition only after the application finishes injecting its transcript, and bind observation to the foreground window and focused control captured at that moment (`voice_to_text.py:556-566`, `voice_to_text.py:1599-1607`). The tracker allows a short edit window, requires Backspace before replacement typing, and finalizes a non-empty replacement after a brief idle interval or when the observation window expires (`voice_to_text.py:514-519`, `voice_to_text.py:599-643`).

The hook is passive and active only while the tracker is armed (`voice_to_text.py:1692-1725`). Cancel instead of guessing when context changes, the user navigates, uses unsupported modifiers or keys, starts another recording, clicks the mouse, exceeds size limits, or reaches a detectable secure control (`voice_to_text.py:583-617`, `voice_to_text.py:1539-1542`, `voice_to_text.py:1697-1718`, `voice_to_text.py:1741-1755`). Tests verify cancellation for ordinary appended typing, navigation, focus changes, and timeout (`tests/test_transcript_pipeline.py:82-104`).

Focus context comes from foreground-window and focused-control handles (`voice_to_text.py:709-749`). Standard Win32 password edits are skipped, but browser and custom controls may not expose that state; recognition remains independently disableable and refuses to arm when context inspection fails (`voice_to_text.py:750-773`, `voice_to_text.py:1700-1706`, `voice_to_text.py:1728-1739`).

### Suggest a constrained semantic correction

After the edit idles, reconstruct only the suffix implied by observed Backspaces and typed characters, then derive the smallest safe whole-word mapping from the original and corrected strings (`voice_to_text.py:619-694`). Diff expansion trims surrounding punctuation, rejects empty or unchanged pairs, requires alphanumeric content on both sides, and caps rule size (`voice_to_text.py:645-694`).

Tests verify `Adds` to `adds`, spacing correction from `Alot` to `a lot`, same-text rejection, modifier-aware reconstruction of `Upper`, and punctuation-only rejection (`tests/test_transcript_pipeline.py:64-80`, `tests/test_transcript_pipeline.py:106-128`).

### Require confirmation before persistence

A detected pair is only a suggestion. The monitor sends it through the callback path (`voice_to_text.py:1478-1480`, `voice_to_text.py:1755-1762`), and the GUI transfers that callback onto its main thread before presenting a Yes/No dialog with both forms (`gui.py:943-965`). The confirmation does not restore the tray-hidden settings window. Declining records no rule; only acceptance calls the persistence method (`gui.py:966-977`, `voice_to_text.py:1764-1769`).

The persistence boundary is tested end to end: an accepted `Alot` to `a lot` suggestion is reloaded from a temporary corrections file and then applies successfully (`tests/test_transcript_pipeline.py:131-143`). Observation alone never writes.

## Why This Matters

Aggressive cancellation turns uncertainty into a missed suggestion instead of a wrong learned rule. A false negative costs one manual correction; a false positive can silently affect future dictation. Same-context checks, time limits, Backspace-first sequencing, navigation and mouse cancellation, and bounded rule derivation deliberately prefer the safer failure mode (`voice_to_text.py:556-694`, `voice_to_text.py:1741-1755`).

Separating observation from persistence preserves intent. Keystrokes may indicate an edit, but they do not prove the user wants permanent automation. The confirmation dialog exposes the proposed mapping and makes rejection a no-op (`gui.py:957-977`).

The narrow model is testable without depending on every Windows editor. The tracker accepts an explicit clock and focus context, making timeout, idle completion, and focus changes deterministic in tests (`voice_to_text.py:538-566`, `tests/test_transcript_pipeline.py:50-62`).

Secure-field handling is intentionally conservative but not overstated: standard password edits are detectable, custom controls may not be, and opt-out remains available (`voice_to_text.py:750-773`, `voice_to_text.py:1728-1739`). The full repository suite was rerun after the dialog-visibility regression was added and passed all 46 tests.

## When to Apply

- The application itself has just inserted known text and can arm observation at a precise boundary (`voice_to_text.py:1599-1607`).
- A useful correction can be expressed as a short, immediate Backspace-and-retype suffix edit without caret movement or selection (`voice_to_text.py:511-519`, `voice_to_text.py:599-617`).
- Current focus can be represented by stable window/control identity and monitored for change (`voice_to_text.py:709-768`).
- Missing an ambiguous edit is preferable to learning it incorrectly.
- The user can review a concrete before/after proposal before persistence (`gui.py:957-977`).

Do not extend this detector to infer selection replacements, mouse-driven edits, undo/redo, navigation, paste operations, cross-window edits, or arbitrary document mutations. Those interactions cancel or fall outside the accepted key model (`voice_to_text.py:524-529`, `voice_to_text.py:583-617`, `voice_to_text.py:1741-1755`). Supporting them safely requires editor-specific document and caret integration, not more guesses in a global hook.

## Examples

### Accepted whole-word correction

Given freshly injected `The app Adds`, immediate trailing replacement produces `("Adds", "adds")`, not a one-character fragment (`tests/test_transcript_pipeline.py:64-71`, `voice_to_text.py:645-694`). Persistence still waits for GUI approval (`gui.py:957-971`).

### Accepted spacing correction

Given `I use Alot.`, deleting and retyping `a lot.` produces `("Alot", "a lot")`; surrounding punctuation is excluded (`tests/test_transcript_pipeline.py:73-80`, `voice_to_text.py:681-694`).

### Canceled ordinary continuation

Given `Published text`, typing a space and `n` without first Backspacing resets the tracker and yields no suggestion (`tests/test_transcript_pipeline.py:82-88`, `voice_to_text.py:610-617`).

### Canceled navigation or focus change

Pressing Left or receiving input from a different window/control context cancels observation (`tests/test_transcript_pipeline.py:90-97`, `voice_to_text.py:587-597`). Mouse input follows the same cancel-don't-guess policy (`voice_to_text.py:1746-1750`).

### Rejected low-value edits

Retyping identical text yields no rule, and punctuation-only changes are rejected because both sides must contain alphanumeric content (`tests/test_transcript_pipeline.py:106-128`, `voice_to_text.py:648-689`).

## Related

- [deterministic-exact-transcript-corrections.md](../logic-errors/deterministic-exact-transcript-corrections.md) documents the confirmed rule store and deterministic application stage.
- [CORRECTION_LEARNING_SCOPE.md](../../../CORRECTION_LEARNING_SCOPE.md) records the project-specific scope, privacy limits, and acceptance cases.
- [UPGRADE_PLAN.md](../../../UPGRADE_PLAN.md) preserves dated implementation notes, but its pause checkpoint is stale.
- [README.md](../../../README.md) documents the supported user workflow and opt-out.
