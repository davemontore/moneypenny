# DECISIONS.md

Significant project decisions, with date, reason, and practical consequence.

---

## 2026-08-25 — Common punctuation commands must not depend on a cleanup model

**Decision:** Parse paired quotes and common verbal punctuation locally before
the optional contextual cleanup pass. Preserve explicit literal forms such as
"the word comma", "a colon", and "say colon". Migrate the retired Groq cleanup
model from `llama-3.1-8b-instant` to `openai/gpt-oss-20b` for remaining
ambiguities.

**Reason:** Groq shut down `llama-3.1-8b-instant` on August 16, 2026. The app's
safe raw-text fallback then made every punctuation request appear to succeed
while leaking the spoken commands into the final text. A deterministic local
path keeps core dictation behavior available through model retirement, network
failure, missing credentials, and Cleanup Off mode.

**Practical consequence:** `quote ... end quote`, the existing quote variants,
single punctuation commands, line breaks, parentheses, and slashes add no
network latency. Literal and unmatched forms can still reach contextual cleanup
when enabled. Existing saved model settings migrate automatically.

Sources: https://console.groq.com/docs/deprecations and
https://console.groq.com/docs/models

---

## 2026-08-13 — One universal line break; never type bare Enter

**Decision:** `new line`, `newline`, and `new paragraph` all produce the same
soft line break typed as Shift+Enter. MoneyPenny never types a bare Enter. Say
any line-break command twice for a blank line.

**Reason:** Bare Enter can submit chat-style text boxes, and per-application
behavior would force the user to classify every focused editor before speaking.
Fast cleanup models are also inconsistent about emitting one newline versus
two, so code must enforce the exact mechanics.

**Practical consequence:** Documents receive soft breaks rather than true
paragraph marks—an acceptable trade for one composable command that cannot
accidentally send a message. Local parsing handles routine commands; contextual
cleanup only resolves remaining ambiguity.

---

## 2026-08-12 — Context-aware cleanup replaces punctuation heuristics

**Decision:** Raw speech recognition is followed by a selective Groq `llama-3.1-8b-instant` cleanup pass. Commands-only mode is the default: ordinary dictation returns immediately, while transcripts containing likely verbal punctuation receive contextual cleanup. Off and Always modes remain available. The cleaner returns the raw transcript unchanged when its call fails.

**Reason:** Deterministic word replacement cannot reliably distinguish a punctuation command from literal prose such as "the word comma." Whisper's transcription prompt guides spelling and style but does not execute instructions. A fast language-model pass is the established solution used by modern Wispr Flow alternatives.

**Alternatives considered:** Continue expanding regular-expression heuristics (inherently ambiguous and produced punctuation collisions); rely on Whisper punctuation alone (does not consistently handle spoken quotation commands); use a local cleanup model (slower and more setup on this computer).

**Practical consequence:** Ordinary cloud dictation makes no additional request. Likely verbal commands make one additional small Groq request; if it fails, MoneyPenny types the raw transcript instead. Raw and final text are retained locally in the History tab for testing and troubleshooting.

Sources: https://github.com/zachlatta/freeflow and https://github.com/jgvilchezc/flow

---

## 2026-08-12 — Ship a branded Windows executable for taskbar identity

**Decision:** Build a windowed on-folder `MoneyPenny.exe` with the project icon embedded and target that executable from the Start Menu and pinned taskbar shortcuts. The executable receives the same `MoneyPenny.VoiceTyping` AppUserModelID as its shortcuts and receives the project folder through `--app-dir`, preserving existing settings, lexicon, history, and logs.

**Reason:** On this Windows 11 build, a Python-hosted Tk window continued to display and group under Python even when its window icon, shortcut icon, and shortcut AppUserModelID were correct. A real executable gives Windows an application-owned icon and process identity.

**Practical consequence:** `Install MoneyPenny.bat` and `Fix MoneyPenny Taskbar Icon.bat` produce the branded executable through the pinned PyInstaller build configuration. Runtime remains an on-folder build, avoiding one-file extraction overhead.

Tagged versions are also built on GitHub's Windows runner and published as `MoneyPenny-Windows-x64.zip`. Ordinary users can therefore extract and run `MoneyPenny.exe` without installing Python; the source installer remains available to contributors.

---

## 2026-08-09 — Installation is isolated and user data stays local

**Decision:** MoneyPenny now installs tested component versions into a private `.venv` folder through `Install MoneyPenny.bat`. Both launchers use that environment. `settings.json` and `lexicon.txt` are local user data and are excluded from Git; a public `lexicon.example.txt` provides a safe starter.

**Reason:** A fresh GitHub ZIP previously depended on users knowing how to run `pip`, modified whichever Python installation happened to be active, and publicly included one user's dictionary. A shared app should be reproducible without publishing or overwriting personal data.

**Alternatives considered:** Continue installing globally from the headless launcher (easy to drift and can affect other Python tools); package a standalone `.exe` now (larger release process and not required for this milestone).

**Practical consequence:** A friend installs or repairs MoneyPenny by double-clicking one file. The first setup takes longer and uses disk space inside `.venv`, but it does not alter other Python projects. Existing personal dictionaries are preserved.

---

## 2026-08-08 — Groq added as a cloud transcription provider (CORRECTED)

**Decision:** Groq was added to MoneyPenny as a cloud provider option alongside OpenRouter, using the `whisper-large-v3-turbo` model.

**Reason:** Initially this same day, Groq appeared to be geo-blocked from Thailand (website access denied in one browser) and was ruled out. That turned out to be wrong — Dave accessed console.groq.com in a different browser and obtained an API key. Groq's speed-focused infrastructure makes it the best candidate to close the gap with Wispr Flow.

**Alternatives considered:** Staying on OpenRouter only (works, ~1.2–2.4s per dictation); Deepgram or AssemblyAI (not needed if Groq performs).

**Practical consequence:** Settings now has a Cloud Provider selector (Groq / OpenRouter), separate API key fields for each, and a Groq model field. Both providers remain available; switching is one click. Lesson: a website failing in one browser is not proof of a geo-block — test another browser before ruling out a service.

---

## 2026-08-08 — Cloud transcription via OpenRouter (completed)

**Decision:** MoneyPenny transcribes through OpenRouter using the `openai/gpt-transcribe` model when Cloud mode is selected in Settings.

**Reason:** Local models (even `tiny.en`) were too slow on the user's hardware; cloud transcription offloads the work to remote servers.

**Practical consequence:** The app needs an internet connection and a valid OpenRouter API key in Cloud mode. Local mode remains available as an offline fallback. Measured transcription time from Thailand: roughly 1.2–2.4 seconds per dictation, plus typing time.
