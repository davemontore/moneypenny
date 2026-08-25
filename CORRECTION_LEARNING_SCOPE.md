# Correction Recognition Scope

## Implemented trial — 2026-08-25

The bounded correction-recognition feature is implemented. MoneyPenny can
reliably learn a direct backspace-and-retype correction made immediately after
it types text. It cannot safely infer every mouse selection, caret move, editor
autocorrection, or rich-text change across all Windows applications from a
global keyboard hook alone.

Automatic, silent database writes remain intentionally disabled. An accidental
edit would become a permanent exact-correction rule and could corrupt future
dictation. The safe product is **detect, suggest, confirm, then save**.

## Trial behavior

1. After MoneyPenny types a transcript, retain in memory for 10 seconds:
   the final text, timestamp, and foreground window identity.
2. Observe only non-injected keystrokes during that short window. Do not keep a
   general-purpose keystroke history.
3. Support the reliable first case: the user immediately presses Backspace to
   replace the end of the newly typed text, without moving the caret or changing
   windows.
4. Derive a single bounded `heard as` -> `type as` diff. Reject empty,
   multi-region, punctuation-only, very long, or structurally ambiguous diffs.
5. Show a small confirmation such as `Learn Adds -> adds?`. Save only after the
   user confirms, using the existing `ExactCorrections` store.
6. Record the originating raw/final transcript and the confirmed rule in local
   diagnostics so a bad suggestion can be explained and removed.

## Later coverage

Windows UI Automation could inspect selections and text values in some native
and browser controls, extending recognition to mid-sentence corrections. It is
not universal: Outlook editors, web apps, Electron apps, remote desktops, and
custom controls expose different or incomplete accessibility state. This
should be an optional adapter, not a dependency of the MVP.

An explicit **Learn last correction** hotkey is a useful fallback for edits the
automatic detector cannot reconstruct. It can ask the user to confirm the
before/after phrase instead of guessing.

## Safety and privacy gates

- Never monitor beyond the short post-transcript window.
- Cancel on window change, mouse click, navigation key, selection shortcut, or
  a second dictation.
- Do not activate in password/secure fields when that state can be detected.
- Keep candidate edits in memory; persist only confirmed correction pairs.
- Allow correction recognition to be disabled independently of dictation.
- Rate-limit suggestions and make every learned rule removable in Dictionary.

## Acceptance cases

- [x] `Adds` immediately changed with Backspace to `adds` suggests `Adds -> adds`.
- [x] A correction after 10 seconds creates no suggestion.
- [x] A window switch, click, arrow key, or selection cancels detection.
- [x] Ordinary typing after the transcript does not create a rule.
- [x] Rejected suggestions do not alter `corrections.json`.
- [x] Confirmed suggestions persist and apply through the existing
  exact-correction pipeline on the next matching dictation.
