# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Transcript transformation

### Transcript pipeline
The ordered transformation from recognized speech to emitted text, with locally observable stages that can apply exact corrections, spoken commands, optional contextual cleanup, final normalization, and caret-aware insertion preparation.

### Insertion context
Text immediately before the active caret, inspected without changing the editor or clipboard, that determines whether dictated text needs a separator and whether its first word continues an unfinished sentence.

When Insertion context is unavailable, secure, unstable, or too slow to read safely, the Transcript pipeline preserves capitalization but does not invent leading whitespace.

Insertion context is currently disabled in release builds because browser message fields can expose surrounding application text instead of only the editable field. Release builds therefore preserve transcription capitalization and add no inferred separator until target-aware validation is available.

### Preferred vocabulary
A private set of terms supplied to transcription as recognition hints; it can improve recognition but does not guarantee the final spelling, capitalization, or symbols.

### Exact correction
A user-defined mapping from a complete heard phrase to literal written output, applied deterministically once so more-specific phrases win without rewriting inside larger words or cascading through replacement text.

### Correction recognition
The short-lived process that observes a directly attributable edit to freshly emitted text and proposes, but never silently stores, an Exact correction.

### Correction suggestion
A bounded heard-to-written proposal derived by Correction recognition that has no persistent effect until the user explicitly accepts it.

### Spoken command
An unambiguous phrase whose intended punctuation, quotation, delimiter, or line-break effect is applied locally before optional contextual cleanup; explicit literal discussion of the phrase remains ordinary text.

### Contextual cleanup
An optional model-assisted transcript stage normally used for ambiguity that bounded local rules cannot safely resolve, with a user-selectable mode that can apply it to every transcript; failure preserves the already locally processed transcript.

### Soft break
A safe Shift+Enter line break that inserts layout without invoking a control's submit action. `new line` emits one Soft break, while `new paragraph` emits two to leave a blank line between paragraphs.

## Desktop lifecycle

### Primary instance
The one process allowed to own dictation hotkeys and the tray interface; later launches communicate activation intent to it and then exit.

### Activation request
A one-way request from a rejected later launch asking the Primary instance to reveal its existing interface, distinct from the ownership mechanism that prevents duplicate processes.

## Repository data

### Private runtime data
Mutable credentials, preferences, personal vocabulary, learned corrections, captured transcripts, and similar user state that belongs to a local installation rather than the shared project history.

### Safe example
A tracked starter that demonstrates the shape of Private runtime data under a distinct filename using public placeholder values rather than a user's live file.
