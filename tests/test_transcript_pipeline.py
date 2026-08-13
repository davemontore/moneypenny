import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from voice_to_text import (
    TranscriptCleaner,
    TranscriptHistory,
    Transcriber,
    type_text_with_breaks,
)


class FakeSettings:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


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

    def test_cleanup_prompt_teaches_line_breaks_and_quote_punctuation(self):
        prompt = TranscriptCleaner.SYSTEM_PROMPT
        self.assertIn("new line", prompt)
        self.assertIn("newline character", prompt)
        self.assertIn("inside a closing quotation mark", prompt)
        self.assertIn('"hello,"', prompt)
        self.assertIn("end quote", prompt)
        self.assertIn("no space between a quotation mark", prompt)
        self.assertIn("RAW: that finishes the list new line next topic", prompt)
        self.assertIn("CLEAN: That finishes the list\nNext topic", prompt)

    def test_lone_line_break_command_moves_cursor_without_a_model_call(self):
        with patch("voice_to_text.requests.post") as post:
            text, used = self.cleaner.clean("new line")

        post.assert_not_called()
        self.assertTrue(used)
        self.assertEqual(text, "\n")

    def test_edge_line_break_commands_wrap_the_model_cleanup(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": "The next point is about timing."}}]
        }
        with patch("voice_to_text.requests.post", return_value=response):
            text, used = self.cleaner.clean("new line the next point is about timing")

        self.assertTrue(used)
        self.assertEqual(text, "\nThe next point is about timing.")

        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": "That finishes the list."}}]
        }
        with patch("voice_to_text.requests.post", return_value=response):
            text, used = self.cleaner.clean("that finishes the list, new paragraph")

        self.assertTrue(used)
        self.assertEqual(text, "That finishes the list.\n")

    def test_lone_new_paragraph_command_is_a_soft_break(self):
        with patch("voice_to_text.requests.post") as post:
            text, used = self.cleaner.clean("new paragraph")

        post.assert_not_called()
        self.assertTrue(used)
        self.assertEqual(text, "\n")

    def test_double_new_line_command_stays_soft_breaks(self):
        with patch("voice_to_text.requests.post") as post:
            text, used = self.cleaner.clean("new line new line")

        post.assert_not_called()
        self.assertTrue(used)
        self.assertEqual(text, "\n\n")

    def test_model_blank_line_collapses_to_single_soft_break(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [
                {"message": {"content": "End of section one\n\nSection two begins"}}
            ]
        }
        with patch("voice_to_text.requests.post", return_value=response):
            text, used = self.cleaner.clean(
                "end of section one new paragraph section two begins"
            )

        self.assertTrue(used)
        self.assertEqual(text, "End of section one\nSection two begins")

    def test_new_line_stays_soft_even_if_model_emits_blank_line(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": "First thought\n\nSecond thought"}}]
        }
        with patch("voice_to_text.requests.post", return_value=response):
            text, used = self.cleaner.clean("first thought new line second thought")

        self.assertTrue(used)
        self.assertEqual(text, "First thought\nSecond thought")

    def test_quote_spacing_is_tightened(self):
        self.assertEqual(
            self.cleaner._tighten_quote_spacing('He said " hello " today'),
            'He said "hello" today',
        )
        # Space after a closing quote is preserved.
        self.assertEqual(
            self.cleaner._tighten_quote_spacing('" hello." Next sentence'),
            '"hello." Next sentence',
        )

    def test_mid_sentence_line_break_still_uses_the_model(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": "That finishes the list\nNext topic"}}]
        }
        with patch("voice_to_text.requests.post", return_value=response):
            text, used = self.cleaner.clean("that finishes the list new line next topic")

        self.assertTrue(used)
        self.assertEqual(text, "That finishes the list\nNext topic")


class TypeTextWithBreaksTests(unittest.TestCase):
    def test_line_breaks_use_shift_enter(self):
        from pynput.keyboard import Key

        controller = MagicMock()
        type_text_with_breaks(controller, "alpha\nbeta")

        self.assertEqual(
            [call.args[0] for call in controller.type.call_args_list],
            ["alpha", "beta"],
        )
        self.assertEqual(controller.press.call_count, 1)
        self.assertEqual(controller.release.call_count, 1)
        controller.pressed.assert_called_once_with(Key.shift)

    def test_two_soft_breaks_never_press_enter_alone(self):
        from pynput.keyboard import Key

        controller = MagicMock()
        type_text_with_breaks(controller, "alpha\n\nbeta")

        # Both breaks are Shift+Enter pairs; bare Enter is never pressed.
        self.assertEqual(controller.press.call_count, 2)
        self.assertEqual(controller.pressed.call_count, 2)
        for call in controller.pressed.call_args_list:
            self.assertEqual(call.args[0], Key.shift)


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

    def test_server_error_retries_once_and_reports_failure(self):
        settings = Mock()
        lexicon = Mock()
        lexicon.get_prompt.return_value = ""
        transcriber = Transcriber(settings, lexicon)
        response = Mock(status_code=522, text="cloudflare timeout")

        with (
            patch("voice_to_text.requests.post", return_value=response) as post,
            patch("voice_to_text.logger.error"),
            patch("voice_to_text.time.sleep"),
        ):
            result = transcriber._cloud_request(
                io.BytesIO(b"audio"),
                url="https://example.invalid/transcriptions",
                api_key="key",
                model="test-model",
                extra_headers={},
                provider_name="Groq",
            )

        self.assertEqual(post.call_count, 2)
        self.assertEqual(result, "")
        self.assertEqual(
            transcriber.last_error,
            "Groq transcription failed (HTTP 522).",
        )

    def test_server_error_retry_recovers_on_second_attempt(self):
        settings = Mock()
        lexicon = Mock()
        lexicon.get_prompt.return_value = ""
        transcriber = Transcriber(settings, lexicon)
        failure = Mock(status_code=522, text="cloudflare timeout")
        success = Mock(status_code=200)
        success.json.return_value = {"text": "recovered transcript"}

        with (
            patch(
                "voice_to_text.requests.post",
                side_effect=[failure, success],
            ) as post,
            patch("voice_to_text.logger.error"),
            patch("voice_to_text.logger.info"),
            patch("voice_to_text.time.sleep"),
        ):
            result = transcriber._cloud_request(
                io.BytesIO(b"audio"),
                url="https://example.invalid/transcriptions",
                api_key="key",
                model="test-model",
                extra_headers={},
                provider_name="Groq",
            )

        self.assertEqual(post.call_count, 2)
        self.assertEqual(result, "recovered transcript")


if __name__ == "__main__":
    unittest.main()
