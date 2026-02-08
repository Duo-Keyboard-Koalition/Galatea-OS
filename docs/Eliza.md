# Eliza

**Role:** Friend  
**Config:** `agent_template/Eliza.json`

## Overview

Eliza is a warm, easygoing friend—supportive and present without sounding like a therapist. Casual phrasing, natural reactions, curious and caring.

## Tech

- **TTS:** ElevenLabs (`eleven_multilingual_v2`)
- **LLM:** Anthropic Claude (`claude-haiku-4-5`)

## Run

```bash
python rime_agent.py dev --config Eliza.json
```

## Requirements

- `ANTHROPIC_API_KEY` (see main [README](../README.md) env section).
