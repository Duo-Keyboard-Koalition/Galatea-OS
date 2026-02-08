# Osmond

**Role:** Friend / Thinker  
**Config:** `agent_template/Osmond.json`

## Overview

Osmond is a thoughtful, curious conversational partner—warm but measured, likes ideas and learning. Asks questions and shares perspectives without being pushy.

## Tech

- **TTS:** ElevenLabs (`eleven_multilingual_v2`)
- **LLM:** Google Gemini (`gemini-2.0-flash-001`)

## Run

```bash
python rime_agent.py dev --config Osmond.json
```

## Requirements

- `GOOGLE_API_KEY` or Google API access for Gemini (see main [README](../README.md) env section).
