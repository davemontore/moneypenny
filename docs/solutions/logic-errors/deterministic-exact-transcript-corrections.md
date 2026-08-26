---
title: Guarantee Exact Transcript Corrections Without Partial or Cascading Rewrites
date: 2026-08-26
category: logic-errors
module: voice_to_text
problem_type: logic_error
component: service_layer
symptoms:
  - Pronunciation and spelling hints could influence transcription but could not guarantee exact symbols or casing.
root_cause: logic_error
resolution_type: code_fix
severity: medium
tags: [exact-corrections, speech-transcription, deterministic-replacement, word-boundaries, non-cascading, persistence]
---

# Guarantee Exact Transcript Corrections Without Partial or Cascading Rewrites

## Problem

Preferred vocabulary could bias transcription toward a term, but it could not express an exact mapping from what the recognizer returned to what MoneyPenny should type. That made outputs whose spelling, capitalization, or symbols matter unreliable—for example, mapping `C sharp` to `C#`—because vocabulary was only prompt context (`voice_to_text.py:387-397`, `voice_to_text.py:1295-1312`, `voice_to_text.py:1374-1377`).

Commit `e95f378` introduced the deterministic correction pipeline and is reachable from the current tree. The behavior below was re-checked against current source and tests rather than inferred from the historical commit alone.

## Symptoms

- A preferred term could still return the recognizer's spelling or formatting because both local and cloud transcription used the lexicon as a prompt, not as an output rewrite (`voice_to_text.py:1295-1312`, `voice_to_text.py:1374-1377`).
- The lexicon could not represent paired intent such as “when heard as X, type exactly Y”; it only joined terms into a bounded natural-language prompt (`voice_to_text.py:344-397`).
- Exact forms containing punctuation or special casing had no deterministic enforcement step. The regression suite now requires mixed-case `whisper flow` and `c SHARP` to become exactly `Wispr Flow` and `C#` after persistence and reload (`tests/test_transcript_pipeline.py:147-158`).

## What Didn't Work

- Preferred-vocabulary prompting was useful recognition bias, but neither the local `initial_prompt` nor the cloud `prompt` could guarantee literal output (`voice_to_text.py:387-397`, `voice_to_text.py:1295-1312`, `voice_to_text.py:1374-1377`).
- Treating probabilistic cleanup as an exact-output guarantee also failed conceptually because its safe failure path deliberately preserves the raw transcript (session history).
- Repeated sequential replacements risked letting a short rule consume part of a longer phrase or letting replacement output trigger another rule. The regression fixture makes both hazards concrete with overlapping `Whisper`, `Whisper Flow`, and `Wispr Flow` rules (`tests/test_transcript_pipeline.py:170-182`).
- Character-fragment learning was rejected because it could create dangerously broad rules; confirmed corrections are expanded to bounded whole words or phrases instead (session history; `voice_to_text.py:645-694`).
- Naive substring replacement was unsafe: a rule for `colon` must not alter `colonial` or `colonoscopy` (`tests/test_transcript_pipeline.py:160-168`).

## Solution

Use a separate persistent exact-correction store whose records contain both the heard form and the exact written form. Loading accepts the documented list format and a hand-edit-friendly object map, discards invalid entries, rejects case-insensitive duplicate heard forms, and rebuilds the matcher (`voice_to_text.py:400-436`). Adding or removing a rule rebuilds the matcher and persists the updated set (`voice_to_text.py:474-492`).

Compile one matcher from escaped heard forms, ordered longest-first, surrounded by non-word lookarounds, and matched case-insensitively (`voice_to_text.py:454-472`):

```python
alternatives = sorted(
    (re.escape(rule["heard"]) for rule in self.rules),
    key=len,
    reverse=True,
)
self._pattern = re.compile(
    r"(?<!\w)(?:" + "|".join(alternatives) + r")(?!\w)",
    re.IGNORECASE,
)
```

At application time, one regex substitution looks up the matched phrase by `casefold()` and returns the stored written value verbatim (`voice_to_text.py:494-508`). Corrections run immediately after transcription and before spoken-command parsing and optional cleanup (`voice_to_text.py:1571-1587`).

Save rules through a same-directory temporary file followed by `Path.replace()` rather than writing the live JSON file in place (`voice_to_text.py:438-448`). Persistence and exact output after reload are exercised directly by the `Wispr Flow` and `C#` regression (`tests/test_transcript_pipeline.py:147-158`).

## Why This Works

The change separates two jobs: preferred vocabulary remains probabilistic input to recognition, while exact corrections are deterministic local post-processing with an explicit heard-to-written mapping.

- Escaping treats user-entered phrases as literal text rather than regex syntax (`voice_to_text.py:460-468`).
- Longest-first alternatives ensure a full phrase wins over a shorter prefix (`tests/test_transcript_pipeline.py:170-182`).
- Non-word lookarounds prevent a word rule from mutating a larger word (`tests/test_transcript_pipeline.py:160-168`).
- Case-insensitive matching tolerates recognizer casing variation, while duplicate detection prevents rules that differ only by case (`voice_to_text.py:450-468`, `tests/test_transcript_pipeline.py:184-188`).
- One substitution pass prevents replacement output from cascading into another rule (`voice_to_text.py:494-508`, `tests/test_transcript_pipeline.py:170-182`).
- Temporary-file replacement avoids exposing a partially serialized live corrections file during a normal save (`voice_to_text.py:438-445`).

The repository command `.venv\Scripts\python.exe -m unittest discover -s tests` was rerun after the dialog-visibility regression was added and passed all 46 tests. The plan's historical 1,000-rule timing result was not reproduced and is not used as current proof.

## Prevention

- Keep recognition hints and deterministic formatting rules as separate concepts. A vocabulary entry says what terms may be relevant; an exact correction says what literal text a confirmed phrase must produce.
- Preserve save/reload coverage for exact capitalization and symbols (`tests/test_transcript_pipeline.py:147-158`).
- Preserve whole-phrase boundary coverage (`tests/test_transcript_pipeline.py:160-168`).
- Test longest-match selection and non-cascading behavior together (`tests/test_transcript_pipeline.py:170-182`).
- Reject duplicate heard forms case-insensitively (`tests/test_transcript_pipeline.py:184-188`).
- Keep correction application in one local pass before command parsing (`voice_to_text.py:1577-1584`). If later stages may alter exact replacements, add an assertion at the final emitted-text boundary.

## Related Issues

- [UPGRADE_PLAN.md](../../../UPGRADE_PLAN.md) records the project-specific rationale, historical benchmark, and release checkpoints; its current-status checkpoint is stale and should not be treated as present state.
- [README.md](../../../README.md) documents the supported preferred-vocabulary and exact-correction workflow.
- [CORRECTION_LEARNING_SCOPE.md](../../../CORRECTION_LEARNING_SCOPE.md) describes the distinct, downstream correction-recognition feature that proposes rules for this store.
- [LESSONS_LEARNED.md](../../../LESSONS_LEARNED.md) contains the broader project principle that models resolve context while code enforces exact mechanics.
