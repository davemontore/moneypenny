import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from voice_to_text import TranscriptCleaner, TranscriptHistory, Transcriber


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
