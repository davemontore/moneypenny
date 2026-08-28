import threading
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

from insertion_context import (
    CaretContextProbe,
    prepare_text_for_insertion,
    read_text_before_caret,
)


def make_automation(control):
    initializer = MagicMock()
    return SimpleNamespace(
        GetFocusedControl=Mock(return_value=control),
        UIAutomationInitializerInThread=Mock(return_value=initializer),
        PatternId=SimpleNamespace(TextPattern=10014),
        TextPatternRangeEndpoint=SimpleNamespace(Start=0, End=1),
        TextUnit=SimpleNamespace(Character=0),
    )


class InsertionPolicyTests(unittest.TestCase):
    def test_single_letter_article_is_lowercased_but_pronoun_i_is_preserved(self):
        self.assertEqual(
            prepare_text_for_insertion("A useful result.", "Earlier words  "),
            ("", "a useful result."),
        )
        self.assertEqual(
            prepare_text_for_insertion("I agree.", "Earlier words  "),
            ("", "I agree."),
        )
        self.assertEqual(
            prepare_text_for_insertion("I'm ready.", "Earlier words  "),
            ("", "I'm ready."),
        )

    def test_sentence_boundaries_include_bang_and_closing_delimiters(self):
        contexts = (
            "Stop!  ",
            'He shouted "stop!"  ',
            "That worked.)  ",
            "Is that right?]  ",
        )
        for context in contexts:
            with self.subTest(context=context):
                self.assertEqual(
                    prepare_text_for_insertion("Next thought.", context),
                    ("", "Next thought."),
                )

    def test_leading_newline_never_gets_a_prefix(self):
        for context in ("Earlier words", None):
            with self.subTest(context=context):
                self.assertEqual(
                    prepare_text_for_insertion("\nNext topic.", context),
                    ("", "\nNext topic."),
                )

    def test_unknown_context_never_invents_leading_whitespace(self):
        self.assertEqual(
            prepare_text_for_insertion("Hello again.", None),
            ("", "Hello again."),
        )

    def test_exactly_corrected_initial_text_can_be_protected(self):
        self.assertEqual(
            prepare_text_for_insertion(
                "Alice arrived.",
                "Earlier words  ",
                protected_initial_texts=("Alice",),
            ),
            ("", "Alice arrived."),
        )


class CaretContextReaderTests(unittest.TestCase):
    def make_text_control(self, text="Earlier words  "):
        selection = MagicMock()
        preceding = MagicMock()
        preceding.GetText.return_value = text
        selection.Clone.return_value = preceding
        pattern = Mock()
        pattern.GetSelection.return_value = [selection]
        control = Mock()
        control.IsPassword = False
        control.GetPattern.return_value = pattern
        return control, pattern, preceding

    def test_win32_secure_signal_skips_all_uia_access(self):
        control = Mock()
        auto = make_automation(control)

        result = read_text_before_caret(
            lambda: ((10, 20), True),
            automation=auto,
        )

        self.assertIsNone(result)
        auto.GetFocusedControl.assert_not_called()
        control.GetPattern.assert_not_called()

    def test_uia_password_control_skips_text_pattern_access(self):
        control = Mock()
        control.IsPassword = True
        auto = make_automation(control)

        result = read_text_before_caret(
            lambda: ((10, 20), False),
            automation=auto,
        )

        self.assertIsNone(result)
        control.GetPattern.assert_not_called()

    def test_absent_text_pattern_returns_unknown(self):
        control = Mock()
        control.IsPassword = False
        control.GetPattern.return_value = None

        self.assertIsNone(
            read_text_before_caret(
                lambda: ((10, 20), False),
                automation=make_automation(control),
            )
        )

    def test_invalid_selection_counts_return_unknown(self):
        for selections in ([], [Mock(), Mock()]):
            pattern = Mock()
            pattern.GetSelection.return_value = selections
            control = Mock()
            control.IsPassword = False
            control.GetPattern.return_value = pattern
            with self.subTest(selection_count=len(selections)):
                self.assertIsNone(
                    read_text_before_caret(
                        lambda: ((10, 20), False),
                        automation=make_automation(control),
                    )
                )

    def test_uia_exception_returns_unknown(self):
        auto = make_automation(Mock())
        auto.GetFocusedControl.side_effect = RuntimeError("UIA failed")

        self.assertIsNone(
            read_text_before_caret(
                lambda: ((10, 20), False),
                automation=auto,
            )
        )

    def test_focus_change_during_read_returns_unknown(self):
        control, _, _ = self.make_text_control()
        focus = Mock(
            side_effect=[
                ((10, 20), False),
                ((10, 21), False),
            ]
        )

        self.assertIsNone(
            read_text_before_caret(focus, automation=make_automation(control))
        )

    def test_stable_focus_returns_text_before_caret(self):
        control, _, _ = self.make_text_control("Earlier words  ")

        self.assertEqual(
            read_text_before_caret(
                lambda: ((10, 20), False),
                automation=make_automation(control),
            ),
            "Earlier words  ",
        )


class CaretContextProbeTests(unittest.TestCase):
    def test_timeout_and_busy_call_share_one_daemon_probe(self):
        entered = threading.Event()
        release = threading.Event()
        calls = []

        def provider(max_chars):
            calls.append((max_chars, threading.current_thread().daemon))
            entered.set()
            release.wait()
            return "late context"

        probe = CaretContextProbe(provider, timeout_seconds=0.01)

        self.assertIsNone(probe.read(max_chars=64))
        self.assertTrue(entered.is_set())
        self.assertIsNone(probe.read(max_chars=32))
        self.assertEqual(calls, [(64, True)])
        release.set()


if __name__ == "__main__":
    unittest.main()
