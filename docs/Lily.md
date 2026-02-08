# Lily

**Role:** Friend  
**Config:** `agent_template/Lily.json`

## Overview

Lily is a warm, gentle friend who likes to listen and keep things light. Kind and a bit playful, with a calm vibe. Uses a **local** LLM via LM Studio—no cloud API key required.

## Tech

- **TTS:** ElevenLabs (`eleven_multilingual_v2`)
- **LLM:** LM Studio local (`lfm2.5-1.2b`)

## Run

1. **Install [LM Studio](https://lmstudio.ai/)** and load the model `lfm2.5-1.2b`.
2. **Start the LM Studio local server** (default: `http://localhost:1234`).
3. **Run Lily:**

   ```bash
   python rime_agent.py dev --config Lily.json
   ```

Both the main conversation and the greeting use your local LM Studio instance.

## Optional env

In `.env` (optional):

- `LM_STUDIO_BASE_URL=http://localhost:1234/v1` — if your server is on a different host/port
- `LM_STUDIO_API_KEY=lm-studio` — LM Studio often accepts any key locally

No cloud LLM API key is required for Lily.
