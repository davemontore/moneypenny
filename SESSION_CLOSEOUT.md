# SESSION_CLOSEOUT.md

## Trigger

When the user says something like **"let's close out the session for the day"** (also: "wrap up for the day", "end-of-day closeout", "close it out"), run this entire checklist in order before saying goodbye. Verify every step against the actual machine state — never report a step as done unless it was actually checked.

## 1. App matches the code

- [ ] `git status` shows only the intended changes.
- [ ] If `voice_to_text.py` or `gui.py` changed since the last build, rebuild: `"Build MoneyPenny.exe.bat" --no-pause`.
- [ ] The running MoneyPenny process is the freshly built exe (`dist\MoneyPenny\MoneyPenny.exe --app-dir "<project folder>"`). Restart it if it is stale; confirm startup in `logs\moneypenny.log`.
- [ ] The Start Menu shortcut and the hidden Startup shortcut both point at the current exe and current project folder (inspect the `.lnk` targets; the app may have moved folders in the past).

## 2. Tests and logs

- [ ] `.venv\Scripts\python.exe -m unittest discover -s tests` — all tests pass (pytest is not required).
- [ ] Scan `logs\moneypenny.log` for ERROR/WARNING lines from this session; address each one or explain why it is harmless.

## 3. Documentation

- [ ] `CHANGELOG.md` — a version entry exists covering every behavior change made this session.
- [ ] `README.md` and `QuickStart-CheatSheet.md` — user-visible behavior described accurately (commands, hotkeys, versions).
- [ ] `DECISIONS.md` — significant decisions recorded with date, decision, reason, practical consequence.
- [ ] `LESSONS_LEARNED.md` — reusable lessons recorded, newest first.
- [ ] The command reference shown in the Dictionary tab (`gui.py`) matches the actual command behavior.

## 4. Safety

- [ ] `git ls-files` contains no secrets or personal data. `settings.json`, `lexicon.txt`, `transcript_history.jsonl`, and `encryption.key` must remain untracked.

## 5. Commit and publish

- [ ] Commit all changes with a clear message (never commit user data or API keys).
- [ ] Push the branch to origin.
- [ ] If `CHANGELOG.md` carries a new version header, tag it (`v3.1.1` style) and push the tag — this triggers the GitHub Actions release build that publishes `MoneyPenny-Windows-x64.zip`.
- [ ] If the `gh` CLI is available, confirm the workflow run started (`gh run list --limit 1`).

## 6. Report

Give the user a short closeout summary: what changed this session, what was tested, what was committed/pushed/released, the state of the running app, and any open follow-ups for next session.
