# Ludia

**Role:** Girl  
**Config:** `agent_template/Ludia.json`

## Overview

Ludia is a character-driven voice agent using Rime TTS (Arcana, Celeste speaker). Default agent when no `--config` is specified.

## Tech

- **TTS:** Rime (`arcana`, speaker `celeste`)
- **LLM:** OpenAI (`gpt-4o-mini`)

## Run

```bash
python rime_agent.py dev
# or explicitly:
python rime_agent.py dev --config Ludia.json
```

## Requirements

- `OPENAI_API_KEY` for the LLM
- `RIME_API_KEY` for Rime TTS (see main [README](../README.md) env section).
