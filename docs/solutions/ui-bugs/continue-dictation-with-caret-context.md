---
title: Continue Dictation Using Caret Context
date: 2026-08-26
category: ui-bugs
module: voice_to_text
problem_type: ui_bug
component: frontend
symptoms:
  - Every new dictation began with sentence-style capitalization even when inserted into the middle of an unfinished sentence.
  - Existing whitespace before the caret could be duplicated by the application's unconditional leading space.
root_cause: logic_error
resolution_type: code_fix
severity: medium
related_components: [service_layer]
tags: [caret-context, capitalization, text-insertion, windows-uia, focus-safety, secure-input, graceful-fallback]
---

# Continue Dictation Using Caret Context

## Problem

MoneyPenny treated each recording as an independent sentence. When a user removed terminal punctuation, left the caret after an existing sentence fragment, and resumed dictation, the first recognized word stayed capitalized and the output always gained another leading space.

## Symptoms

- Continuing `I stayed  ` with `And then I left.` produced an uppercase `And` even though the insertion was mid-sentence.
- The unconditional separator could add a third space when the editor already contained two spaces before the caret.
- Treating all insertions as continuations would be equally wrong at a document start, after a line break, or after `.`, `!`, or `?`.

## What Didn't Work

- Transcript text alone cannot reveal whether the active caret is at a sentence boundary. The same recognized phrase may be a new sentence or a continuation depending on the editor state.
- Clipboard-based inspection or synthetic caret movement would mutate user state and introduce visible side effects.
- An unbounded accessibility call can hang behind a misbehaving editor provider and delay future dictations.
- Blind lowercasing can damage intentional forms such as `NASA`, `OpenAI`, the pronoun `I`, or a confirmed Exact correction such as `Alice`.

## Solution

Read a small amount of text before the focused caret through Windows UI Automation without moving the caret or touching the clipboard (`insertion_context.py`). Validate the foreground-window and focused-control identity before and after the read; return unknown if focus changes, the field is secure, the selection is unsupported, or the provider raises an error.

Run that read in a capacity-one daemon probe with a short deadline. If a provider times out, later dictations do not create more blocked probe threads; they immediately use the conservative fallback until the original probe finishes (`insertion_context.py`, `tests/test_insertion_context.py`).

Apply a deterministic insertion policy after modifiers are released and immediately before typing (`voice_to_text.py`):

```python
preceding_text = _get_text_before_caret()
prefix, text = prepare_text_for_insertion(
    text,
    preceding_text,
    protected_initial_texts=protected_initial_texts,
)
type_text_with_breaks(self.keyboard_controller, prefix + text)
```

The context probe and deterministic insertion policy remain implemented and
covered as a future target-aware capability. In the current release,
`CARET_CONTEXT_ENABLED` is false because browser message fields exposed
surrounding application text as if it were editor content. Runtime dictation
therefore treats caret context as unknown, preserves transcription
capitalization, and adds no inferred leading separator.

Exact corrections applied to the first lexical token carry protection metadata into insertion preparation so their stored written form remains literal (`voice_to_text.py`, `tests/test_transcript_pipeline.py`). Typing and correction-recognition arming occur before history and status callbacks, reducing the window in which application UI work can steal focus.

The packaged Windows build explicitly lists the lazily imported `uiautomation` dependency in `MoneyPenny.spec`; runtime dependencies are pinned in `requirements.txt`.

## Why This Works

When enabled for a verified target, capitalization becomes a property of the
actual insertion point rather than the recording boundary. The policy remains
deterministic and independently testable, while the editor integration is
best-effort and bounded.

The current fallback preserves the recognizer's capitalization and inserts no
whitespace. This avoids typing based on stale, inaccessible, secure, or
ambiguous context and avoids inventing indentation.

The repository test suite covers continuation casing, sentence boundaries,
unknown-context whitespace, exact-correction protection, secure-field handling,
focus changes, provider errors, timeouts, and busy-probe behavior.

## Prevention

- Keep editor inspection non-mutating, time-bounded, and capacity-limited.
- Revalidate focus identity around any accessibility read used to influence typing.
- Treat inaccessible, secure, changing, or ambiguous editor state as unknown and fall back conservatively.
- Carry exact-output intent across later formatting stages instead of reconstructing it from capitalization heuristics.
- Test both policy boundaries and integration failures: missing patterns, multiple selections, password fields, focus changes, exceptions, timeouts, and unsupported editors.
- When an optional dependency is imported lazily, add it to both runtime requirements and the packager's hidden imports.

## Related Issues

- [Guarantee Exact Transcript Corrections Without Partial or Cascading Rewrites](../logic-errors/deterministic-exact-transcript-corrections.md) documents the literal-output contract preserved by insertion preparation.
- [Bound Correction Learning to Confirmed Direct Edits](../design-patterns/bound-correction-learning-to-confirmed-direct-edits.md) uses the same cancel-don't-guess approach for cross-application focus state.
