# Rime LiveKit Agents – Technical Overview

## Project Summary

This project is a Python-based, real-time conversational AI agent system built on top of [LiveKit](https://livekit.io/) and [Rime.ai](https://www.rime.ai/). It enables hyper-realistic, character-driven voice agents that can join LiveKit audio rooms, respond to users in natural language, and speak with expressive, customizable voices. The system leverages advanced TTS (text-to-speech) models, OpenAI LLMs (large language models), and a modular plugin architecture for extensibility.

---

## Table of Contents

- [Project Summary](#project-summary)
- [Folder Structure](#folder-structure)
- [Key Components](#key-components)
- [Core Technologies](#core-technologies)
- [Setup & Installation](#setup--installation)
- [Environment Variables & API Keys](#environment-variables--api-keys)
- [Running the Agent](#running-the-agent)
- [Customization & Prompt Engineering](#customization--prompt-engineering)
- [Technical Notes](#technical-notes)
- [Demo/Deployment Tips](#demodeployment-tips)
- [References](#references)

---

## Folder Structure

```
rime-livekit-agents/
│
├── .env                  # Environment variables (API keys, URLs)
├── agent_configs.py      # Voice/personality configs and prompt engineering
├── rime_agent.py         # Main agent logic and entrypoint
├── requirements.txt      # Python dependencies
├── text_utils.py         # Custom sentence tokenizer for TTS
├── TECHNICAL_OVERVIEW.md # This technical documentation
├── README.md             # Basic project info
├── KMS/                  # (Optional) Key Management Service or logs
│   └── logs/
└── __pycache__/          # Python bytecode cache
```

---

## Key Components

### 1. `rime_agent.py`

- Main entry point for the agent.
- Handles LiveKit room connection, session management, plugin integration, and event loop.
- Integrates TTS, LLM, STT, noise cancellation, and turn detection.

### 2. `agent_configs.py`

- Defines agent personalities, TTS settings, and prompt engineering.
- Example: `"celeste"` persona with a clingy, playful, flirty university girlfriend style.
- Each persona can have unique TTS speed, model, and prompt.

### 3. `text_utils.py`

- Implements custom sentence tokenization for advanced TTS models (e.g., Arcana).

---

## Core Technologies

- **LiveKit**: Real-time audio/video infrastructure for scalable, multi-user rooms.
- **Rime.ai**: Hyper-realistic TTS models ("arcana", "mistv2").
- **OpenAI**: LLMs (e.g., GPT-4o-mini) for generating conversational responses.
- **Python 3.11+**: All orchestration and logic.
- **LiveKit Plugins**: For noise cancellation, turn detection, and TTS enhancements.

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/uw-datasci/AI-GF.git
```

### 2. Create and Activate a Virtual Environment

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download Model Files (Hugging Face / Léa)

```bash
python rime_agent.py download-files
```

This downloads **Hugging Face** models used when an agent has `provider: "huggingface"` for TTS or LLM (e.g. Léa). Models are cached locally so the agent can run TTS and LLM via the **transformers** library in-process. STT is **Silero** (local) or **OpenAI**; no Hugging Face STT. Requires `transformers` and `torch` (see `requirements.txt`).

---

## Environment Variables & API Keys

Create a `.env` file in the project root with the following keys:

```env
LIVEKIT_URL=wss://<your-livekit-server>.livekit.cloud
LIVEKIT_API_KEY=<your-livekit-api-key>
LIVEKIT_API_SECRET=<your-livekit-api-secret>

OPENAI_API_KEY=<your-openai-api-key>
RIME_API_KEY=<your-rime-api-key>

# Optional: Tavus avatar integration
TAVUS_API_KEY=<your-tavus-api-key>
TAVUS_REPLICA_ID=<your-tavus-replica-id>
```

**Required API Keys:**

- **LiveKit**: For connecting to your LiveKit Cloud or self-hosted server.
- **OpenAI**: For LLM responses (ensure your key has quota).
- **Rime.ai**: For TTS (Arcana, Mistv2, etc.).
- **Tavus** (optional): For avatar video integration.

**Note:**

- Do **not** surround values with quotes unless the value contains spaces.
- If you see quota errors, check your OpenAI or Rime.ai usage and billing.

---

## Running the Agent

### 1. Console Mode (Debugging)

Run the agent in console mode for local testing:

```bash
python rime_agent.py console
```

### 2. LiveKit Mode (Production/Demo)

Connects the agent to a LiveKit room:

```bash
python rime_agent.py dev
```

- Ensure all required environment variables are set in `.env`.
- The agent will join the specified LiveKit room and respond to participants.

### 3. Stopping the Agent

- Press `Ctrl + C` in the terminal to stop the agent at any time.

---

## Customization & Prompt Engineering

### Prompt format (agent_template JSON)

The system prompt can be a plain string or an object with `type` and `content`:

- **String:** `"personality_prompt": "You are Katerina..."`
- **URL:** `"personality_prompt": { "type": "URL", "content": "https://example.com/prompt.txt" }`
- **File path:** `"personality_prompt": { "type": "File Path", "content": "prompts/katerina.txt" }` (relative to project root)

Use `content` or `Content`; `type` is one of: `String`, `URL`, `File Path`.

### TTS and STT in agent JSON

**tts** has top-level `provider`, `model`, `url`, and a nested **voice_options** object for provider-specific options. **stt** uses the same top-level shape.

```json
"tts": {
  "provider": "elevenlabs",
  "model": "eleven_multilingual_v2",
  "url": null,
  "voice_options": { "voice_id": "...", "optimize_streaming_latency": 3 }
},
"stt": { "provider": "openai", "model": "gpt-4o-mini-transcribe", "url": null }
```

- **provider / model / url:** same as before.
- **tts.voice_options:** ElevenLabs `voice_id`, `model_id`, `optimize_streaming_latency`; Kokoro `voice`, `speed`, `base_url`; Rime `speaker`, `speed_alpha`, `reduce_latency`, `max_tokens`.

**Local / embedded models (no API):** For **Silero**, TTS and STT run **locally inside the agent process** (torch.hub). For **Hugging Face**, TTS and LLM can run in-process (transformers). STT is **Silero** (local) or **OpenAI** (cloud); Hugging Face STT was removed.

- **Chrystèle** (Silero TTS/STT, local LLM): `"tts": { "provider": "silero", "voice_options": { "language": "en", "speaker": "lj_16khz" } }`, `"stt": { "provider": "silero", "language": "en" }`, `"vad": { "provider": "silero", "model": "silero_vad" }`. TTS and STT use snakers4/silero-models (torch.hub) in-process. LLM can be LM Studio (OpenAI-compatible URL) or another local server.
- **Léa** (Hugging Face TTS/LLM, local): `"tts"` and `"llm"` use `"provider": "huggingface"` with Hugging Face Hub model IDs (see `plugins/hf_tts.py`, `plugins/hf_llm.py`). STT uses **OpenAI** (or set `"stt": { "provider": "silero" }` for local). Run `python rime_agent.py download-files` once to cache HF models. No API for TTS/LLM—models run locally in the agent.

**Alternative (OpenAI-compatible servers):** You can use local servers (e.g. Ollama, Whisper API, Kokoro) and `"provider": "openai"` with `"url": "http://localhost:..."` in the agent JSON. Those are still local but run in a separate process; Silero and Hugging Face run embedded in the agent with no separate server.

### VAD in agent JSON

**vad** configures Voice Activity Detection (when the user is speaking). It supports `provider` and `model`; optionally `onnx_file_path` for a custom ONNX file when using Silero.

```json
"vad": { "provider": "silero", "model": "silero_vad" }
```

- **provider:** `"silero"` (default) or `"huggingface"`. Silero is used for all agents today; when `provider` is `"huggingface"`, the config is in place for a future HF VAD plugin.
- **model:** Identifier for the VAD model. For Silero, use `"silero_vad"`—this is the bundled ONNX model (`silero_vad.onnx`) from livekit-plugins-silero (snakers4/silero-vad). If omitted, the same default is used.
- **onnx_file_path** (optional): Path to a custom Silero VAD ONNX file; if set, this file is loaded instead of the bundled model.

**Chrystèle** uses `"vad": { "provider": "silero", "model": "silero_vad" }`. **Léa** can use `"provider": "huggingface"` for future HF VAD alignment.

### Expressive TTS tags (LiveKit / Rime)

To make agents sound livelier, use tags like `<laugh>`, `<sigh>`, `<mmm>`, `<whis>...</whis>` in `personality_prompt` and `intro_phrase`. They work best with **Rime Arcana** TTS; other engines may ignore them. See **[docs/LIVEKIT_TTS_TAGS.md](docs/LIVEKIT_TTS_TAGS.md)** for the full list and usage.

- Edit `agent_configs.py` to:
  - Add new personas (copy the `"celeste"` config and modify).
  - Change TTS speed (`"speed_alpha"`), model, or speaker.
  - Update the `llm_prompt` for different conversational styles.
  - Adjust `intro_phrase` for custom greetings.

**Example:**

```python
"celeste": {
    "tts_options": {
        "model": "arcana",
        "speaker": "celeste",
        "speed_alpha": 1.0,  # 1.0 = normal speed
        ...
    },
    "llm_prompt": "...",
    "intro_phrase": "hey cutie... <laugh> I was just thinking about you. what are you up to?",
}
```

- Lower `"speed_alpha"` if TTS is too fast for avatar sync.

---

## Technical Notes

- **Dependencies:**
  - Uses a forked version of `livekit-plugins-rime` for improved Arcana support (see `requirements.txt`).
  - All audio processing, TTS, and LLM calls are asynchronous for low latency.
- **Plugins:**
  - Noise cancellation (`livekit-plugins-noise-cancellation`)
  - Turn detection (`livekit-plugins-turn-detector`)
- **Extensibility:**
  - Add new plugins, voices, or logic by extending the agent/session classes.
- **Microphone Selection:**
  - By default, uses the system default input device.
  - To change, modify the code to set the desired device index using `sounddevice` or relevant library.

---

## Demo/Deployment Tips

- **For Demos:**

  - Highlight real-time, character-driven voice interaction.
  - Show expressive TTS and persona switching.
  - Demonstrate easy customization via `agent_configs.py`.
  - Explain integration with LiveKit for scalable audio rooms.

- **For Production:**
  - Deploy on a cloud VM or service (e.g., Render, AWS, Azure).
  - Use secure storage for API keys.
  - Monitor usage and quotas for OpenAI and Rime.ai.
  - Optionally, connect a web or mobile frontend via LiveKit APIs.

---

## Troubleshooting

- **Quota Errors:**
  - If you see `insufficient_quota` or 429 errors, check your OpenAI or Rime.ai account usage and billing.
- **Audio Sync Issues:**
  - If TTS audio is faster than the avatar, lower `"speed_alpha"` in `agent_configs.py`.
- **Missing Dependencies:**
  - Re-run `pip install -r requirements.txt` in your activated virtual environment.
- **Microphone Issues:**
  - Ensure your preferred input device is set as default, or modify the code to select a specific device.

---

## References

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/overview/)
- [Rime.ai](https://www.rime.ai/)
- [LiveKit Cloud](https://livekit.io/cloud)
- [OpenAI Platform](https://platform.openai.com/)
- [Tavus](https://www.tavus.io/) (if using avatar video)

---

_This document provides a comprehensive technical overview and setup guide for the Rime LiveKit Agents project. For further details, see the codebase and README._
