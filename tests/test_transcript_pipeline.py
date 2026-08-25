import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from voice_to_text import (
    CorrectionTracker,
    ExactCorrections,
    MoneyPennyApp,
    Settings,
    TranscriptCleaner,
    TranscriptHistory,
    Transcriber,
    apply_spoken_punctuation,
    normalize_punctuation_collisions,
)


class FakeSettings:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


class SettingsMigrationTests(unittest.TestCase):
    def test_retired_cleanup_model_is_migrated_and_saved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            path.write_text(
                json.dumps({"cleanup_model": "llama-3.1-8b-instant"}),
                encoding="utf-8",
            )

            with patch("voice_to_text.SETTINGS_FILE", path):
                settings = Settings()

            self.assertEqual(
                settings.get("cleanup_model"),
                "openai/gpt-oss-20b",
            )
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["cleanup_model"], "openai/gpt-oss-20b")


class CorrectionTrackerTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.context = (10, 20)
        self.tracker = CorrectionTracker(clock=lambda: self.now)

    def type_key(self, name, **modifiers):
        self.tracker.handle_key(name, self.context, now=self.now, **modifiers)
        self.now += 0.05

    def finish(self):
        self.now += CorrectionTracker.IDLE_SECONDS
        return self.tracker.poll(self.context, now=self.now)

    def test_immediate_backspace_and_retype_suggests_whole_word(self):
        self.tracker.arm("The app Adds", self.context, now=self.now)
        for _ in "Adds":
            self.type_key("backspace")
        for character in "adds":
            self.type_key(character)

        self.assertEqual(self.finish(), ("Adds", "adds"))

    def test_spacing_correction_expands_to_complete_words(self):
        self.tracker.arm("I use Alot.", self.context, now=self.now)
        for _ in "Alot.":
            self.type_key("backspace")
        for character in "a lot.":
            self.type_key("space" if character == " " else character)

        self.assertEqual(self.finish(), ("Alot", "a lot"))

    def test_ordinary_typing_after_transcript_cancels(self):
        self.tracker.arm("Published text", self.context, now=self.now)
        self.type_key("space")
        self.type_key("n")

        self.assertIsNone(self.finish())
        self.assertFalse(self.tracker.active)

    def test_navigation_or_window_change_cancels(self):
        self.tracker.arm("Wrong", self.context, now=self.now)
        self.type_key("left")
        self.assertFalse(self.tracker.active)

        self.tracker.arm("Wrong", self.context, now=self.now)
        self.tracker.handle_key("backspace", (99, 20), now=self.now)
        self.assertFalse(self.tracker.active)

    def test_expired_window_does_not_suggest(self):
        self.tracker.arm("Wrong", self.context, now=self.now)
        self.now += CorrectionTracker.WINDOW_SECONDS + 0.01
        self.type_key("backspace")

        self.assertIsNone(self.finish())

    def test_retyping_same_text_does_not_suggest(self):
        self.tracker.arm("Fine", self.context, now=self.now)
        self.type_key("backspace")
        self.type_key("e")

        self.assertIsNone(self.finish())

    def test_shift_and_caps_lock_are_reconstructed(self):
        self.tracker.arm("lower", self.context, now=self.now)
        for _ in "lower":
            self.type_key("backspace")
        self.type_key("u", shift=True)
        for character in "pper":
            self.type_key(character)

        self.assertEqual(self.finish(), ("lower", "Upper"))

    def test_punctuation_only_edit_is_rejected(self):
        self.tracker.arm("Hello.", self.context, now=self.now)
        self.type_key("backspace")
        self.type_key(",")

        self.assertIsNone(self.finish())


class CorrectionSuggestionPersistenceTests(unittest.TestCase):
    def test_confirmed_suggestion_persists_through_exact_corrections(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "corrections.json"
            app = MoneyPennyApp.__new__(MoneyPennyApp)
            app.corrections = ExactCorrections(path)

            self.assertTrue(app.accept_correction_suggestion("Alot", "a lot"))

            reloaded = ExactCorrections(path)
            corrected, applied = reloaded.apply("I use alot.")
            self.assertEqual(corrected, "I use a lot.")
            self.assertEqual(len(applied), 1)


class ExactCorrectionsTests(unittest.TestCase):
    def test_rules_persist_and_preserve_exact_written_form(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "corrections.json"
            corrections = ExactCorrections(path)
            self.assertTrue(corrections.add("Whisper Flow", "Wispr Flow"))
            self.assertTrue(corrections.add("C sharp", "C#"))

            reloaded = ExactCorrections(path)
            text, applied = reloaded.apply("whisper flow works with c SHARP.")

            self.assertEqual(text, "Wispr Flow works with C#.")
            self.assertEqual(len(applied), 2)

    def test_rules_match_whole_phrases_only(self):
        corrections = ExactCorrections(Path("missing-test-corrections.json"))
        corrections.rules = [{"heard": "colon", "written": "Colin"}]
        corrections._rebuild_matcher()

        text, applied = corrections.apply("colonial colon colonoscopy")

        self.assertEqual(text, "colonial Colin colonoscopy")
        self.assertEqual(len(applied), 1)

    def test_rules_use_longest_match_and_do_not_cascade(self):
        corrections = ExactCorrections(Path("missing-test-corrections.json"))
        corrections.rules = [
            {"heard": "Whisper", "written": "Wispr"},
            {"heard": "Whisper Flow", "written": "Wispr Flow"},
            {"heard": "Wispr Flow", "written": "changed twice"},
        ]
        corrections._rebuild_matcher()

        text, applied = corrections.apply("Whisper Flow")

        self.assertEqual(text, "Wispr Flow")
        self.assertEqual(len(applied), 1)

    def test_duplicate_heard_phrase_is_case_insensitive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            corrections = ExactCorrections(Path(temp_dir) / "corrections.json")
            self.assertTrue(corrections.add("C sharp", "C#"))
            self.assertFalse(corrections.add("c SHARP", "C Sharp"))


class PunctuationNormalizationTests(unittest.TestCase):
    def test_user_reported_end_quote_case(self):
        text, applied = apply_spoken_punctuation(
            "The quotation feature where I quote use it to do something like "
            "this end quote isn't working for some reason."
        )

        self.assertEqual(
            text,
            'The quotation feature where I "use it to do something like this" '
            "isn't working for some reason.",
        )
        self.assertEqual(len(applied), 1)

    def test_supported_quote_pair_variants(self):
        cases = {
            "Say open quote, this works close quote now.": 'Say "this works" now.',
            "Say quote this works quote now.": 'Say "this works" now.',
            "Say quote this works end quote now.": 'Say "this works" now.',
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                text, _ = apply_spoken_punctuation(raw)
                self.assertEqual(text, expected)

    def test_common_commands_are_applied_locally(self):
        text, applied = apply_spoken_punctuation(
            "First comma second period new paragraph Is this right question mark"
        )

        self.assertEqual(text, "First, second.\n\nIs this right?")
        self.assertEqual(len(applied), 4)

    def test_punctuation_inside_quotes_and_terminal_mark(self):
        text, _ = apply_spoken_punctuation(
            "quote hello comma world end quote period"
        )

        self.assertEqual(text, '"hello, world."')

    def test_automatic_punctuation_beside_commands_is_collapsed(self):
        text, _ = apply_spoken_punctuation(
            "Hello comma, world period. Is this right question mark?"
        )

        self.assertEqual(text, "Hello, world. Is this right?")

    def test_literal_punctuation_references_are_preserved(self):
        cases = (
            "I used the word comma in context.",
            "Add a colon.",
            "This was meant to end with a colon.",
            "Say colon when discussing the command.",
        )
        for raw in cases:
            with self.subTest(raw=raw):
                text, applied = apply_spoken_punctuation(raw)
                self.assertEqual(text, raw)
                self.assertEqual(applied, [])

    def test_unmatched_quote_is_left_for_ambiguity_cleanup(self):
        raw = "I said quote only once."
        text, applied = apply_spoken_punctuation(raw)
        self.assertEqual(text, raw)
        self.assertEqual(applied, [])

    def test_colon_supersedes_automatic_period(self):
        self.assertEqual(
            normalize_punctuation_collisions("He sent me this:."),
            "He sent me this:",
        )

    def test_terminal_mark_supersedes_adjacent_comma(self):
        self.assertEqual(
            normalize_punctuation_collisions("Is this right,?"),
            "Is this right?",
        )

    def test_intentional_ellipsis_is_preserved(self):
        self.assertEqual(
            normalize_punctuation_collisions("Wait... the word colon."),
            "Wait... the word colon.",
        )


class TranscriptCleanerTests(unittest.TestCase):
    def setUp(self):
        self.settings = FakeSettings(
            cleanup_mode="commands",
            groq_api_key="test-key",
            cleanup_model="llama-3.1-8b-instant",
        )
        self.cleaner = TranscriptCleaner(self.settings)

    def test_successful_cleanup_uses_established_second_pass(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": '"Working really well."'}}]
        }

        with patch("voice_to_text.requests.post", return_value=response) as post:
            text, used = self.cleaner.clean("quote working really well quote period")

        self.assertTrue(used)
        self.assertEqual(text, '"Working really well."')
        request = post.call_args
        self.assertEqual(
            request.args[0],
            "https://api.groq.com/openai/v1/chat/completions",
        )
        self.assertEqual(request.kwargs["json"]["model"], "llama-3.1-8b-instant")
        self.assertIn("the word comma", request.kwargs["json"]["messages"][0]["content"])

    def test_http_failure_falls_back_to_raw_transcript(self):
        response = Mock(status_code=429, text="rate limited")
        with (
            patch("voice_to_text.requests.post", return_value=response),
            patch("voice_to_text.logger.warning"),
        ):
            text, used = self.cleaner.clean("keep this exact text period")

        self.assertFalse(used)
        self.assertEqual(text, "keep this exact text period")
        self.assertIn("used raw transcript", self.cleaner.last_error)

    def test_unsafe_expansion_falls_back_to_raw_transcript(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": "x" * 1000}}]
        }
        with (
            patch("voice_to_text.requests.post", return_value=response),
            patch("voice_to_text.logger.warning"),
        ):
            text, used = self.cleaner.clean("short dictation period")

        self.assertFalse(used)
        self.assertEqual(text, "short dictation period")

    def test_disabled_cleanup_does_not_call_groq(self):
        cleaner = TranscriptCleaner(FakeSettings(cleanup_mode="off"))
        with patch("voice_to_text.requests.post") as post:
            text, used = cleaner.clean("raw transcript")

        post.assert_not_called()
        self.assertFalse(used)
        self.assertEqual(text, "raw transcript")

    def test_commands_mode_skips_ordinary_dictation(self):
        with patch("voice_to_text.requests.post") as post:
            text, used = self.cleaner.clean("ordinary speech without a verbal command")

        post.assert_not_called()
        self.assertFalse(used)
        self.assertEqual(text, "ordinary speech without a verbal command")

    def test_commands_mode_detects_literal_punctuation_context(self):
        self.assertTrue(self.cleaner.should_clean("I used the word comma in context"))
        self.assertTrue(self.cleaner.should_clean("Open quote, working close quote."))

    def test_always_mode_cleans_ordinary_dictation(self):
        cleaner = TranscriptCleaner(FakeSettings(cleanup_mode="always"))
        self.assertTrue(cleaner.should_clean("ordinary dictation"))


class TranscriptHistoryTests(unittest.TestCase):
    def test_history_persists_raw_and_final_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.jsonl"
            history = TranscriptHistory(path)
            history.add(
                raw="quote hello quote",
                final='"Hello"',
                mode="cloud",
                provider="groq",
                elapsed=0.72,
                cleanup_used=True,
            )

            reloaded = TranscriptHistory(path)
            entries = reloaded.get_entries()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["raw"], "quote hello quote")
            self.assertEqual(entries[0]["final"], '"Hello"')
            self.assertTrue(entries[0]["cleanup_used"])

            line = path.read_text(encoding="utf-8").strip()
            self.assertEqual(json.loads(line)["provider"], "groq")

    def test_clear_removes_persisted_history(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.jsonl"
            history = TranscriptHistory(path)
            history.add("raw", "final", "local", "local", 0.3, False)
            history.clear()

            self.assertEqual(history.get_entries(), [])
            self.assertEqual(path.read_text(encoding="utf-8"), "")


class CloudTranscriptionErrorTests(unittest.TestCase):
    def test_rejected_api_key_is_exposed_to_the_app(self):
        settings = Mock()
        lexicon = Mock()
        lexicon.get_prompt.return_value = ""
        transcriber = Transcriber(settings, lexicon)
        response = Mock(status_code=401, text='{"error":"invalid key"}')

        with (
            patch("voice_to_text.requests.post", return_value=response),
            patch("voice_to_text.logger.error"),
        ):
            result = transcriber._cloud_request(
                io.BytesIO(b"audio"),
                url="https://example.invalid/transcriptions",
                api_key="not-a-real-key",
                model="test-model",
                extra_headers={},
                provider_name="Groq",
            )

        self.assertEqual(result, "")
        self.assertEqual(
            transcriber.last_error,
            "Groq rejected the API key. Check it in Settings.",
        )


if __name__ == "__main__":
    unittest.main()
