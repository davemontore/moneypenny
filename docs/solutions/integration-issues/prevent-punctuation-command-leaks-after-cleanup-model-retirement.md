---
title: Keep Spoken Commands Working When a Cleanup Model Is Retired
date: 2026-08-26
category: integration-issues
module: voice_to_text
problem_type: integration_issue
component: service_layer
symptoms:
  - Existing installations retained a retired cleanup model and silently fell back to raw transcripts.
  - Common punctuation, quote, and line-break commands could be typed literally when remote cleanup was unavailable.
root_cause: config_error
resolution_type: code_fix
severity: medium
tags: [groq-model-retirement, punctuation-commands, local-fallback, settings-migration, transcript-pipeline, literal-protection, shift-enter]
---

# Keep Spoken Commands Working When a Cleanup Model Is Retired

## Problem

Project decision records attribute the incident to Groq retiring the cleanup model stored by existing installations; the current migration code identifies that model as retired (`DECISIONS.md`, `voice_to_text.py:309-318`). MoneyPenny correctly preserved user text when cleanup failed, but spoken punctuation still depended on that optional call, so command words such as `period`, `comma`, or `new paragraph` could survive into final output (`voice_to_text.py:1134-1150`, `voice_to_text.py:1179-1198`).

Local Git history records the repair in commit `552a34b` and the subsequent merge commit labeled PR #2. Current source and tests are the behavioral authority here; remote PR state was not independently checked during this capture.

## Symptoms

- Saved known settings overwrite defaults during load, so changing only the default would leave an already-saved retired model active (`voice_to_text.py:292-307`).
- Cleanup intentionally returns its input after HTTP errors, missing credentials, malformed responses, or unsafe expansion (`voice_to_text.py:1134-1150`, `voice_to_text.py:1179-1198`; `tests/test_transcript_pipeline.py:304-328`).
- Before mechanical commands ran locally, that safe fallback also preserved spoken command tokens. The regression suite now requires `First comma second period new paragraph Is this right question mark` to become `First, second.\nIs this right?` (`tests/test_transcript_pipeline.py:216-222`).
- A bare Enter can submit a chat-style control. The output tests require every transcript newline, including consecutive breaks, to be emitted with Shift held (`tests/test_transcript_pipeline.py:404-429`).

## What Didn't Work

- Delegating deterministic mechanics to contextual cleanup coupled core syntax to a remote model. The fallback was safe for prose but could not also infer commands after the dependency failed (`voice_to_text.py:1134-1150`, `voice_to_text.py:1179-1198`).
- Changing the default model alone was insufficient because persisted settings have precedence (`voice_to_text.py:288-307`).
- Blind global replacement would corrupt literal prose. `the word comma`, `a colon`, and `say colon` must remain text, while an unmatched `quote` must not consume the transcript remainder (`tests/test_transcript_pipeline.py:238-255`).
- Emitting parsed newlines as bare Enter was unsafe in controls where Enter is an action (`voice_to_text.py:1424-1432`, `tests/test_transcript_pipeline.py:404-429`).

## Solution

Repair both configuration compatibility and the command path.

The default cleanup model is now `openai/gpt-oss-20b`. After saved settings are merged, the exact retired identifier is migrated and immediately persisted (`voice_to_text.py:267-321`). The migration test starts with an on-disk retired value and verifies both runtime selection and rewritten JSON (`tests/test_transcript_pipeline.py:30-47`). Other user-selected values are untouched.

Common spoken commands are parsed locally before optional cleanup. The command table covers punctuation, parentheses, slashes, and soft breaks; the matcher escapes phrases, orders longer alternatives first, applies token boundaries, and ignores case (`voice_to_text.py:823-855`). Paired quote forms are handled separately so their content is bounded (`voice_to_text.py:813-821`, `voice_to_text.py:898-918`).

Literal-reference cues preserve punctuation words when the speaker is discussing them; otherwise the callback returns the mapped character (`voice_to_text.py:856-876`, `voice_to_text.py:920-928`). Narrow normalization then removes command-generated spacing and impossible punctuation collisions such as `:.`, `,?`, and `,.` without broad prose rewriting (`voice_to_text.py:799-810`, `voice_to_text.py:879-895`, `voice_to_text.py:928-932`).

The transcript pipeline calls local punctuation parsing before deciding whether contextual cleanup is needed (`voice_to_text.py:1571-1589`). Cleanup remains available for ambiguity, while off mode and ordinary commands-only prose can skip the remote call (`tests/test_transcript_pipeline.py:330-354`).

Finally, newline characters are emitted as Shift+Enter. The typing function splits on `\n`, types each segment, and inserts every intervening break while Shift is held (`voice_to_text.py:1424-1432`; `tests/test_transcript_pipeline.py:404-429`).

## Why This Works

Running migration after saved values are merged lets it repair the value that will actually be used. Persisting only a recognized retired identifier fixes existing installations without overwriting unrelated choices (`voice_to_text.py:292-321`).

Local parsing removes the cleanup model from the correctness path for unambiguous mechanics. A cleanup failure can still preserve input, but the value entering that optional stage has already had supported commands resolved (`voice_to_text.py:1577-1589`).

The parser remains deliberately narrower than natural-language cleanup:

- Token boundaries avoid substitutions inside larger words (`voice_to_text.py:844-855`).
- Literal cues protect discussions of punctuation (`voice_to_text.py:856-876`).
- Paired quote patterns bound intended quoted content (`voice_to_text.py:813-821`, `voice_to_text.py:910-918`).
- Unmatched ambiguous forms remain unchanged for optional contextual handling (`voice_to_text.py:898-904`, `tests/test_transcript_pipeline.py:251-255`).
- Collision normalization targets impossible or command-generated combinations while preserving intentional ellipses (`voice_to_text.py:799-810`, `tests/test_transcript_pipeline.py:269-272`).

Shift+Enter completes the safe local path at the output boundary (`voice_to_text.py:1424-1432`). The full unittest suite was rerun after the correction-dialog visibility regression was added and passed all 46 tests.

This repair does not establish production-ready coding punctuation. It proves
the documented isolated command mechanics and fallback behavior. Dense symbol
sequences, mixed prose/code dictation, and editor-specific live behavior remain
a public-release gate and require a repeatable acceptance matrix plus focused
regressions for every observed failure.

## Prevention

- Keep unambiguous, mechanical commands out of optional remote dependencies. Apply them locally before any model call and reserve contextual cleanup for ambiguity.
- When a persisted default changes, test an existing settings file and assert both runtime and saved state (`tests/test_transcript_pipeline.py:30-47`).
- Preserve the raw-input failure contract, but test the complete pipeline so graceful fallback still includes essential local mechanics (`tests/test_transcript_pipeline.py:304-380`).
- For every new spoken command, test command use, literal discussion, and collision with recognizer-supplied punctuation. Quote-like commands also need paired and unmatched cases (`tests/test_transcript_pipeline.py:191-272`).
- Treat line-break generation and emission separately: parser tests assert `\n`; output tests assert Shift+Enter and reject a bare-Enter path (`tests/test_transcript_pipeline.py:216-222`, `tests/test_transcript_pipeline.py:404-429`).

## Related Issues

- [deterministic-exact-transcript-corrections.md](../logic-errors/deterministic-exact-transcript-corrections.md) documents the adjacent exact-correction stage and the same local-mechanics boundary.
- [DECISIONS.md](../../../DECISIONS.md) records the model-retirement and universal soft-break decisions; its 2026-08-12 cleanup entry is superseded in part by the 2026-08-25 local-parser decision.
- [UPGRADE_PLAN.md](../../../UPGRADE_PLAN.md) preserves the historical investigation and acceptance record, but its pause checkpoint is stale.
- [LESSONS_LEARNED.md](../../../LESSONS_LEARNED.md) contains the project principle that models resolve context while code enforces exact mechanics.
