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

- [ ] Define protected literal forms: `the word colon`, `say colon`, and equivalents.
- [ ] Parse unambiguous single commands locally: comma, period, question mark,
      exclamation point, colon, semicolon, new line, and new paragraph.
- [ ] Parse paired commands locally: quotes and parentheses.
- [ ] Normalize spacing around inserted punctuation.
- [ ] Keep the current remote cleaner available behind an explicit fallback setting.

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
- [ ] Build a private Windows release candidate.
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
- Current checkpoint: live-test Phase 1 while beginning the local spoken-command parser.
