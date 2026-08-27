# MoneyPenny Product Roadmap

## Installation and first run

- Publish a prebuilt `MoneyPenny-Windows-x64.zip` for each tagged GitHub release so ordinary users do not need Python.
- Keep `Install MoneyPenny.bat` as the source/developer installation path.
- Add a first-run wizard that offers **Fast cloud setup** and **Private offline setup**, tests the microphone, validates the selected provider key, and confirms the recording hotkey.
- Sign release executables when distribution grows enough to justify a Windows code-signing certificate; unsigned builds can trigger SmartScreen warnings.

## Provider experience

- Keep human provider names in the standard interface. Do not expose anonymous “API Key 1” and “API Key 2” fields.
- Show only the selected provider's key and model in standard mode:
  - **Groq: Recommended for speed**
  - **OpenRouter: More model choice**
  - **Local: Offline/private**
- Add an **Advanced** provider profile for OpenAI-compatible transcription services with editable display name, base URL, API key, and model ID.
- Treat transcription and transcript cleanup as separate capabilities. An audio-transcription model cannot automatically serve as the cleanup chat model.
- Move stored API keys from plaintext `settings.json` to Windows Credential Manager or DPAPI-backed storage.

## Models

- Present friendly local presets rather than raw model IDs:
  - **Tiny English: Fastest, lowest accuracy** (`tiny.en`)
  - **Base English: Better accuracy, slower** (`base.en`)
  - **Small English: Higher accuracy, capable CPU recommended** (`small.en`)
  - **Large V3 Turbo: GPU/high-end machine recommended** (`large-v3-turbo`)
- Download only the selected local model on demand and show download size/progress. Bundling every local model would make the installer unnecessarily large.
- Keep cloud models such as OpenAI GPT-4o Transcribe out of the local-model list; they require an API and cannot be installed as faster-whisper models.

## Dictation quality

- Add explicit pronunciation-to-output mappings, such as `Whisper Flow => Wispr Flow` and `C sharp => C#`, because the current dictionary prompt biases recognition but cannot guarantee spelling.
- Keep Commands-only cleanup as the default latency compromise and measure transcription, optional cleanup, and typing separately in diagnostics.
