# DECISIONS.md

Significant project decisions, with date, reason, and practical consequence.

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
