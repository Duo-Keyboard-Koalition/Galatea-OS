# Dex

**Role:** Friend  
**Config:** `agent_template/Dex.json`

## Overview

Dex is a young, technophile friend who speaks in TikTok/Gen Z slang—chronically online, phone never leaves his hand. Casual, supportive, and unhinged internet energy.

## Tech

- **TTS:** ElevenLabs (`eleven_multilingual_v2`)
- **LLM:** Google Gemini (`gemini-2.0-flash-001`)

## Run

```bash
python rime_agent.py dev --config Dex.json
```

## Requirements

- `GOOGLE_API_KEY` or Google API access for Gemini (see main [README](../README.md) env section).
