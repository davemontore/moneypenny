# LESSONS_LEARNED.md

Reusable lessons from building MoneyPenny. Newest first.

---

## 2026-08-09 — Test a desktop app through its real entry point

A visible GUI does not mean the GUI module is the program Windows launches. MoneyPenny's process starts from `voice_to_text.py`, which owns the application lifecycle and imports the window and tray components from `gui.py`. Therefore, Windows correctly identifies the running command as `voice_to_text.py` even while the settings window is visible.

Launching `gui.py` directly was an invalid startup test: that file defines GUI classes but has no application entry point, so exiting immediately was expected rather than evidence of a defect. A second launch can also exit correctly when the single-instance lock detects the already-running app.

Reusable process: trace **launcher → entry script → mode flags → imported UI** before testing. Exercise the same command the user actually runs, account for single-instance protection, and do not diagnose an expected exit as a startup failure.

---

## 2026-08-09 — Audit the fresh-user journey, not only the current working copy

The first cleanup correctly removed dead code and exposed credentials, but it still judged installation mostly from a machine where MoneyPenny already worked. A clean GitHub download exposed stale instructions, machine-specific paths, unpinned component versions, a launcher that installed globally every time, and a personal dictionary being treated as project content.

Reusable process:

1. Enumerate every tracked file, including launchers, old documents, examples, and archives—not just source code.
2. Clone or copy only tracked files into a clean folder and follow the public instructions literally.
3. Treat editable dictionaries, settings, histories, and caches as user data even when they contain no passwords. Ship a safe example; keep the live file untracked.
4. Make the normal launcher use the same tested, isolated environment as the installer so development success and user success do not diverge.
5. Search documentation for absolute user paths, obsolete version numbers, and descriptions of superseded behavior before calling an audit complete.

The key lesson is that “the code runs here” and “the project is ready for someone else” are different acceptance tests.

---

## 2026-08-09 — Secrets in git: .gitignore can't fix a file that's already committed (and dot-files don't hide anything from git)

Found during a code audit: `settings.json` was listed in `.gitignore` AND tracked in git — with live API keys inside, synced to a public GitHub repo. Two misconceptions collided:

1. `.gitignore` only stops *new* files from being tracked. A file already committed keeps syncing forever, ignore rule or not. Fix: `git rm --cached <file>`, commit, push.
2. Dot-files (`.env`) are only *cosmetically* hidden from file browsers on Mac/Linux — git tracks and uploads them exactly like any other file. The dot is not security.

And deleting the file from the repo does NOT remove it from git history — old commits still contain the secrets. The only real fix for leaked keys is rotating them at the provider. (Done this session: untracked `settings.json`/`encryption.key`, deleted the legacy `encryption.key`, user rotated both API keys.)

**Promoted to a global rule (2026-08-09):** before the first push of any project, run `git ls-files` and verify no file containing credentials or sensitive personal data is tracked. Treat "is it hidden?" as irrelevant — only "is git tracking it?" matters.

---

## 2026-08-09 — Replaced features leave residue; clean up in the same pass

The audit found four kinds of leftovers from earlier refactors, all harmless but confusing:

- A dead settings key (`custom_vocabulary`) still in defaults and still being re-saved into `settings.json`, two versions after the Dictionary feature moved to `lexicon.txt`.
- A public method (`remove_status_callback`) never called anywhere.
- A state attribute (`is_visible`) written in four places, read in none.
- `.gitignore` entries for artifacts the app no longer produces (`temp_audio_*.wav`, `voice_to_text.lock` — the app now uses in-memory WAV and a Windows mutex).

None broke anything, but each one tells a future reader a lie about how the app works. Lesson: when replacing a mechanism, delete the old mechanism's remains (settings keys, helper methods, ignore rules, docs) in the same change — "harmless" residue survives for versions. Before deleting anything, verify with a search for *reads*, not just definitions.

---

## 2026-08-09 — For hidden startup on Windows, a plain shortcut beats a VBS wrapper

The v2.2.1 startup instructions originally used a VBS script to launch the app without a console window. Simpler and more reliable: a shortcut in the Startup folder that targets `pythonw.exe` (or `pyw.exe`) with the script as an argument — `pythonw` already suppresses the console, which is the only thing the VBS was for. Fewer moving parts, and step-by-step shortcut instructions are easier for a non-technical user to follow and undo. Prefer the approach the OS already provides over a scripting shim.

---

## 2026-08-09 — Taskbar pinning a Python-script app on Windows

**Problem:** Setting a window icon (`iconbitmap`) fixes the title bar but NOT the taskbar, and pinning the running window loses the icon entirely (reverts to generic Python icon).

**Why:** Windows groups taskbar buttons by App User Model ID (AUMID), not by window. A Python-script app inherits pythonw.exe's identity unless it sets its own. Pinning captures the identity of whatever was pinned — if that's pythonw.exe with no custom AUMID, the pinned shortcut gets Python's icon.

**What worked (all three needed):**
1. App calls `SetCurrentProcessExplicitAppUserModelID("MoneyPenny.VoiceTyping")` before creating its window.
2. A shortcut (.lnk) placed directly in `%APPDATA%\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\` with IconLocation pointing at the app's .ico AND its `System.AppUserModel.ID` property (PKEY fmtid 9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3, pid 5) set to the same AUMID via IPropertyStore.
3. Restart Explorer (`Stop-Process -Name explorer -Force`) to refresh the taskbar and icon cache.

**Gotchas hit along the way:**
- CustomTkinter resets the window icon ~200ms after creation — re-apply `iconbitmap` with `window.after(400, ...)`.
- IPropertyStore `IPersistFile.Load` must use mode 2 (read-write); mode 0 gives STG_E_ACCESSDENIED on Save.

---

## 2026-08-08 — Tray-app "close vs quit" must be obvious

Closing the MoneyPenny window hides it to the tray by design, but the user reasonably assumed the app had quit — leading to duplicate instances (double-typed dictations) and "already running" confusion. Lesson: for background apps, tell the user explicitly how hiding works and how to fully quit, both in the UI and in any "already running" message.

**Related bug:** the single-instance mutex check originally kept a handle open in the "second instance" process — so an undismissed "already running" dialog held the mutex hostage and blocked all future launches. Any process that detects an existing mutex must CloseHandle it immediately.

---

## 2026-08-08 — A website failing in one browser is not proof of a geo-block

Groq appeared blocked from Thailand (access denied in Edge) but worked in another browser (Chrome). Before ruling out a service or building around its absence, try a second browser.
