# MoneyPenny v3.1.1 Upgrade Plan

This file is the durable handoff for the correction-and-latency upgrade. Update
the checkboxes and session log whenever work pauses so a later session can
resume without reconstructing decisions from chat history.

## Outcome

Make personal vocabulary, spoken punctuation, and exact spellings predictable
without slowing ordinary Groq dictation. Republish only after the acceptance
suite and live dictation checklist pass.

## Baseline (2026-08-12)

- Public `v3.1.0` release returned to draft with zero downloads.
- 56 local history samples measured.
- No-cleanup fast path: 41 samples, 0.87 seconds average.
- Remote-cleanup path: 15 samples, 1.51 seconds average.
- Current dictionary is only a soft transcription prompt (maximum 50 terms / 600 characters).
- Routine spoken punctuation can trigger a second Groq chat request.

## Design rules

1. Ordinary dictation gets one transcription request and no cleanup request.
2. Exact user corrections run locally and deterministically.
3. Routine punctuation commands run locally and deterministically.
4. User text such as `the word colon` must be protected from command parsing.
5. A contextual AI call is allowed only for genuinely ambiguous cases.
6. Raw, corrected, and final stages remain observable in local history/logging.
7. Existing `lexicon.txt` users migrate without losing vocabulary.

## Phases

### Phase 1 — Correction foundation

- [x] Add a persistent exact-correction store separate from preferred vocabulary.
- [x] Match longer phrases first, case-insensitively, on whole-word boundaries.
- [x] Preserve the exact capitalization and symbols in the replacement value.
- [x] Apply corrections immediately after transcription and before command parsing.
- [x] Add deterministic punctuation-collision normalization (`:.` → `:`, etc.).
- [x] Add GUI fields for **Heard as** → **Type as** rules.
- [x] Add import-safe example corrections without publishing personal entries.

### Phase 2 — Local spoken-command parser

- [x] Define protected literal forms: `the word colon`, `say colon`, and equivalents.
- [x] Parse unambiguous single commands locally: comma, period, question mark,
      exclamation point, colon, semicolon, new line, and new paragraph.
- [x] Parse paired commands locally: quotes and parentheses.
- [x] Normalize spacing around inserted punctuation.
- [x] Keep the current remote cleaner available behind an explicit fallback setting.

The correction-recognition proposal has been scoped separately in
`CORRECTION_LEARNING_SCOPE.md`. A constrained, confirm-before-saving version is
feasible; arbitrary edits across every Windows application are not reliably
observable from global key events alone.

### Phase 3 — Ambiguity routing

- [ ] Detect collisions between command vocabulary and personal vocabulary
      (`colon` / `Colin`) without globally replacing either word.
- [ ] Pass relevant dictionary and correction context to the ambiguity resolver.
- [ ] Invoke the resolver only when deterministic rules cannot decide safely.
- [ ] Record why an ambiguity call was made and how long it took.

### Phase 4 — Latency work

- [ ] Reuse persistent HTTP connections for transcription and optional cleanup.
- [ ] Record capture-finalization, upload/transcription, local-correction,
      ambiguity, and typing timings separately.
- [ ] Evaluate connection warm-up and streaming only after the deterministic
      fast path is stable.
- [ ] Keep ordinary cloud dictation at or below the 0.87-second baseline average.

### Phase 5 — Release candidate

- [ ] Run unit, syntax, dependency, packaging, and secret checks.
- [x] Build a private Windows release candidate.
- [ ] Complete the live acceptance checklist below on this machine.
- [ ] Review the transcript history for regressions and unexpected replacements.
- [ ] Publish `v3.1.1` only after every required case passes repeatedly.

## Required acceptance cases

Each case must pass at least five consecutive times in natural sentences.

| Spoken intent | Required output |
| --- | --- |
| Whisper Flow | Wispr Flow |
| C sharp | C# |
| My friend Colin sent this | My friend Colin sent this |
| Add a colon | Add a colon |
| Send this colon | Send this: |
| The word colon | The word colon |
| This is quoted (using quote commands) | “This is quoted” or "This is quoted" |
| This was meant to end with a colon | This was meant to end with a colon |
| Heading colon | Heading: |
| Ordinary sentence without commands | Unchanged wording; no second API call |

Also verify that no final text contains punctuation collisions such as `:.`,
`,.`, `?:`, `,:,`, doubled terminal marks, or punctuation outside a closing quote.

## Session log

### 2026-08-25 — Local punctuation and quote repair

- Fresh history reproduced `quote ... end quote` leaking into final text.
- The log identified Groq HTTP 404 for the retired
  `llama-3.1-8b-instant` cleanup model as the immediate cause.
- Added and tested a local command parser, including the exact reported
  sentence, protected literal forms, spacing, and adjacent punctuation.
- Migrated old settings to Groq's recommended `openai/gpt-oss-20b` replacement;
  a live cleanup request succeeded with the new model.
- Scoped correction recognition as a constrained confirm-before-save feature
  in `CORRECTION_LEARNING_SCOPE.md`.
- Built candidate 3 and installed its executable in `dist/MoneyPenny`.
- Candidate 3 started in Cloud mode, loaded the private vocabulary and five
  exact corrections, and reported Ready.
- Automated verification: 27 tests pass, syntax compilation passes, the frozen
  build succeeds, and the installed executable hash matches candidate 3.

### 2026-08-25 — Correction-recognition trial

- Implemented the constrained 10-second Backspace-and-retype detector described
  in `CORRECTION_LEARNING_SCOPE.md`.
- Whole-word diff expansion prevents dangerous character-only rules such as
  `A` → `a`; suggestions remain bounded to five words and 80 characters.
- The detector cancels on ordinary typing, navigation, modifiers, focus/window
  changes, mouse input, a second dictation, or timeout.
- Detectable Win32 password controls are excluded; the feature remains
  independently disabled from Settings for custom controls that do not expose
  secure-field state.
- Every candidate requires a GUI confirmation before `corrections.json` changes.
- Automated verification increased to 36 passing tests, including confirmed
  suggestion persistence through the existing exact-correction store.
- Candidate 4 was built, hash-verified into `dist/MoneyPenny`, and started with
  the correction monitor active in Cloud mode.
- The user explicitly approved pushing, merging, and publishing the completed
  update on 2026-08-25 after reviewing the live behavior.

### 2026-08-12 — Plan created

- Release converted to draft; repository and tag preserved.
- Root cause confirmed: MoneyPenny has vocabulary biasing but no exact correction rules.
- Baseline latency calculated from local transcript history.
- Work started on branch `codex/v3.1.1-correction-pipeline`.
- Phase 1 implemented with 17 passing tests.
- A 1,000-rule correction set averaged approximately 0.003 ms per transcript.
- Private candidate 2 packaged and launched from `build/v3.1.1-candidate2`.
- Candidate loaded seven preferred vocabulary terms and five private correction rules.
- Active candidate at handoff: PID 12440, Cloud mode, Right Ctrl hotkey.
- First two candidate dictations averaged 0.73 seconds (0.70–0.75 seconds),
  used no cleanup request, and matched the speaker's wording accurately.
- User feedback at pause: accuracy is good and transcription feels very fast.

## Pause checkpoint — resume here

Repository state:

- Branch: `codex/v3.1.1-correction-pipeline`
- Phase 1 commit: `e95f378` (`Add deterministic correction pipeline`)
- Public `v3.1.0` release remains a draft; do not republish it.
- Private candidate executable:
  `build/v3.1.1-candidate4/dist/MoneyPenny/MoneyPenny.exe`
- The candidate is intentionally using the project folder for private settings,
  vocabulary, corrections, history, and logs.

Working behavior:

- Preferred vocabulary remains a soft transcription hint.
- Exact corrections are local, deterministic, whole-phrase, longest-first,
  case-insensitive on input, and preserve exact output spelling/symbols.
- The live private correction file contains variants for Wispr Flow and C#.
- `Colin` is present as preferred vocabulary, not as an unconditional correction,
  because globally replacing `colon` would break the punctuation command.
- Common punctuation commands and paired quotation forms now run locally before
  optional cleanup; `quote ... end quote` is covered explicitly.
- Saved `llama-3.1-8b-instant` cleanup settings migrate automatically to
  `openai/gpt-oss-20b`.
- Twenty-seven tests pass; a 1,000-rule correction benchmark averaged 0.003 ms.

Next-session task order:

1. Read this file and confirm the active branch before editing.
2. Run the five-repeat live punctuation acceptance matrix with candidate 3 and
   review the resulting history for false command replacements.
3. Preserve the local fast path and route only genuinely ambiguous remnants to
   AI cleanup.
4. Do not add an unconditional `colon` → `Colin` correction.
5. Prototype correction recognition only within the safety constraints in
   `CORRECTION_LEARNING_SCOPE.md`.
6. Do not push, tag, or publish until the live acceptance matrix passes.
