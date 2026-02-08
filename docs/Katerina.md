# Katerina

**Role:** Friend  
**Config:** `agent_template/Katerina.json`

## Overview

Katerina is a Slavic-vampire–style friend—never seen the sun, dark and playful. Distinct personality with expressive, character-driven replies.

## Tech

- **TTS:** ElevenLabs (`eleven_multilingual_v2`)
- **LLM:** Google Gemini (`gemini-2.0-flash-001`)

## Run

```bash
python rime_agent.py dev --config Katerina.json
```

## Requirements

- `GOOGLE_API_KEY` or Google API access for Gemini (see main [README](../README.md) env section).
