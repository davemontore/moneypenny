"""Caret-context reading and deterministic text insertion policy."""

import logging
import threading
from collections.abc import Callable, Iterable
from typing import Any


logger = logging.getLogger("moneypenny")

FocusContextProvider = Callable[[], tuple[object | None, bool]]
TextContextProvider = Callable[[int], str | None]


def _is_sentence_start(preceding_text: str) -> bool:
    """Return whether a caret follows a document, line, or sentence boundary."""
    if not preceding_text:
        return True

    trailing_whitespace = preceding_text[len(preceding_text.rstrip()):]
    if "\n" in trailing_whitespace or "\r" in trailing_whitespace:
        return True

    significant = preceding_text.rstrip().rstrip('"\'”’)]}')
    return not significant or significant[-1] in ".!?"


def _matches_protected_initial_text(
    text: str,
    lexical_start: int,
    protected_initial_texts: Iterable[str],
) -> bool:
    for protected in protected_initial_texts:
        if not protected or not text.startswith(protected, lexical_start):
            continue
        end = lexical_start + len(protected)
        if end == len(text) or not text[end].isalnum():
            return True
    return False


def _lowercase_title_cased_first_word(
    text: str,
    protected_initial_texts: Iterable[str] = (),
) -> str:
    """Undo sentence-initial casing without damaging intentional casing."""
    start = next(
        (index for index, character in enumerate(text) if character.isalpha()),
        None,
    )
    if start is None:
        return text
    if _matches_protected_initial_text(text, start, protected_initial_texts):
        return text

    end = start
    while end < len(text) and (text[end].isalpha() or text[end] in "'’"):
        end += 1
    word = text[start:end]
    letters = [character for character in word if character.isalpha()]
    if word == "I" or word.casefold().startswith(("i'", "i’")):
        return text
    if word == "A" or (
        len(letters) > 1
        and letters[0].isupper()
        and all(character.islower() for character in letters[1:])
    ):
        return text[:start] + text[start].lower() + text[start + 1:]
    return text


def prepare_text_for_insertion(
    text: str,
    preceding_text: str | None,
    protected_initial_texts: Iterable[str] = (),
) -> tuple[str, str]:
    """Choose separator and capitalization from text immediately before the caret.

    ``preceding_text`` is ``None`` when the focused editor does not expose its
    caret. In that case capitalization is retained and no separator is invented.
    ``protected_initial_texts`` carries deterministic corrections whose exact
    written form must survive continuation capitalization handling.
    """
    if text.startswith("\n"):
        return "", text
    if preceding_text is None:
        return "", text

    prefix = "" if not preceding_text or preceding_text[-1].isspace() else " "
    if _is_sentence_start(preceding_text):
        return prefix, text
    return prefix, _lowercase_title_cased_first_word(
        text,
        protected_initial_texts,
    )


_uia_context_warning_logged = False
_uia_warning_lock = threading.Lock()


def _warn_uia_once() -> None:
    global _uia_context_warning_logged
    with _uia_warning_lock:
        if _uia_context_warning_logged:
            return
        _uia_context_warning_logged = True
    logger.warning(
        "Focused editor did not expose caret text; preserving transcript capitalization",
        exc_info=True,
    )


def read_text_before_caret(
    focus_context_provider: FocusContextProvider,
    max_chars: int = 256,
    automation: Any = None,
) -> str | None:
    """Read nearby text without changing the focused editor or clipboard."""
    try:
        initial_identity, is_secure = focus_context_provider()
        if initial_identity is None or is_secure:
            return None

        if automation is None:
            import uiautomation as automation

        with automation.UIAutomationInitializerInThread():
            control = automation.GetFocusedControl()
            if control is None or control.IsPassword:
                return None
            pattern = control.GetPattern(automation.PatternId.TextPattern)
            if pattern is None:
                return None
            selections = pattern.GetSelection()
            if len(selections) != 1:
                return None

            preceding = selections[0].Clone()
            preceding.MoveEndpointByRange(
                automation.TextPatternRangeEndpoint.End,
                preceding,
                automation.TextPatternRangeEndpoint.Start,
                waitTime=0,
            )
            preceding.MoveEndpointByUnit(
                automation.TextPatternRangeEndpoint.Start,
                automation.TextUnit.Character,
                -max_chars,
                waitTime=0,
            )
            text = preceding.GetText(-1)

        final_identity, final_is_secure = focus_context_provider()
        if final_is_secure or final_identity != initial_identity:
            return None
        return text
    except Exception:
        _warn_uia_once()
        return None


class CaretContextProbe:
    """Run at most one bounded, best-effort caret-context read at a time."""

    def __init__(
        self,
        provider: TextContextProvider,
        timeout_seconds: float = 0.15,
    ):
        self._provider = provider
        self._timeout_seconds = timeout_seconds
        self._lock = threading.Lock()
        self._in_flight = False

    def read(self, max_chars: int = 256) -> str | None:
        with self._lock:
            if self._in_flight:
                return None
            self._in_flight = True

        completed = threading.Event()
        outcome: dict[str, str | None] = {}

        def run_probe() -> None:
            try:
                outcome["text"] = self._provider(max_chars)
            except Exception:
                logger.exception("Caret-context probe failed")
                outcome["text"] = None
            finally:
                with self._lock:
                    self._in_flight = False
                completed.set()

        threading.Thread(
            target=run_probe,
            name="MoneyPennyCaretContextProbe",
            daemon=True,
        ).start()
        if not completed.wait(self._timeout_seconds):
            return None
        return outcome.get("text")
