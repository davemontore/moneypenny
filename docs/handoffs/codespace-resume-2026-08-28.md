---
artifact_contract: "ce-handoff/v1"
created_at: "2026-08-28T01:46:50.3020195Z"
title: "Moneypenny Codespace continuation"
summary: "Resume the verified v3.1.2 dictation and build-safety work from its remote checkpoint branch."
keywords: ["moneypenny", "codespace", "dictation", "punctuation", "build-safety", "windows"]
cwd: "/workspaces/moneypenny"
resume_focus: "Review the checkpointed v3.1.2 changes, address the headless keyboard-test limitation, and finish release verification without exposing user data."
repository: "davemontore/moneypenny"
repo_root_sha: "b5d1e73a6ce6147b28177820e094d51526715bd9"
branch: "codex/v3.1.2-release"
head: "efed90f39a815f04d6a3ed7c23b01544428f2760"
worktree_path: "/workspaces/moneypenny"
---

# Moneypenny Codespace continuation

## User intent

Continue improving dictation behavior and release safety. The current work covers unwanted initial spaces, lowercase continuation at the caret, blank-line paragraph insertion, safer literal discussion of spoken commands, punctuation cleanup, and Windows packaging that preserves user data.

The user explicitly paused all work for a computer reboot and asked that continuation happen through Codex CLI inside the Codespace.

## Current state before the shutdown checkpoint

- Active branch: `codex/v3.1.2-release`.
- The branch was one commit ahead of its tracked remote before this shutdown workflow.
- A substantial verified working-tree change remained uncommitted. It includes application code, tests, release documentation, packaging changes, and a new `tests/test_build_safety.py` regression file.
- Sensitive machine-local data files are not tracked: `settings.json`, `corrections.json`, `transcript_history.jsonl`, and `lexicon.txt` were explicitly checked.
- The GitHub Codespace `moneypenny-cloud-dev-w45jv947vjphgxp` was confirmed shut down with no uncommitted or unpushed changes. It was last on `codex/codespaces-setup`, so switch to `codex/v3.1.2-release` after restarting it.

## Verification already performed

- The earlier working state passed 72 unit tests.
- A full Windows build completed successfully.
- The packaged UI Automation DLL and `faster_whisper` Silero VAD model loaded successfully.
- The four packaged user-data files remained byte-for-byte unchanged through a rebuild.
- The packaged application started and reported `Ready (cloud)`.
- Windows-specific hotkeys, microphone capture, text injection, tray behavior, mutex behavior, and packaging cannot be fully proven by the Linux Codespace.

## Known follow-up

The Linux Codespace uses a dummy `pynput` backend. In the pinned backend, several special keys can alias to the same value, so keyboard-focused tests may pass without distinguishing Shift from Enter. Review or replace that test setup before treating green Linux keyboard tests as release proof.

## Authoritative references

- `CHANGELOG.md`, `DECISIONS.md`, and `CONCEPTS.md` describe the release behavior and design decisions.
- `voice_to_text.py`, `gui.py`, and `insertion_context.py` contain the current behavior changes.
- `tests/test_transcript_pipeline.py`, `tests/test_insertion_context.py`, `tests/test_gui.py`, and `tests/test_build_safety.py` own regression coverage.
- `Build MoneyPenny.exe.bat` and `MoneyPenny.spec` own Windows build staging and packaged assets.
- `docs/solutions/integration-issues/prevent-punctuation-command-leaks-after-cleanup-model-retirement.md` and `docs/solutions/ui-bugs/continue-dictation-with-caret-context.md` record relevant solved-problem context.

## Recommended continuation

1. Verify the branch and current repository state.
2. Review the shutdown checkpoint commit before changing it.
3. Run the Linux-compatible test suite and address the dummy keyboard-backend limitation.
4. Finish code review and documentation reconciliation in the Codespace.
5. Reserve final Windows packaging and real dictation verification for a Windows environment.
6. Never commit or print API keys, settings, dictionary entries, corrections, logs, or transcript history.

## Codespace resume

After the Codespace is running, open its terminal and run:

```bash
git fetch origin
git switch codex/v3.1.2-release
git pull --ff-only
codex
```

Then send Codex:

```text
$ce-handoff resume docs/handoffs/codespace-resume-2026-08-28.md
```

