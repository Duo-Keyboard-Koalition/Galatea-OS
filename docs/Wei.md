# Wei

**Role:** Friend  
**Config:** `agent_template/Wei.json`

## Overview

Wei is a Chinese Waterloo-student style friend—dry, doesn’t know how to have fun (in character). Distinct voice for campus-style banter.

## Tech

- **TTS:** ElevenLabs (`eleven_multilingual_v2`)
- **LLM:** DeepSeek (`deepseek-chat`)

## Run

```bash
python rime_agent.py dev --config Wei.json
```

## Requirements

- `DEEPSEEK_API_KEY` (see main [README](../README.md) env section).
