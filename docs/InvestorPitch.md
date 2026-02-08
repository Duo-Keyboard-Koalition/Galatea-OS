# Investor Pitch

**Role:** Founder  
**Config:** `agent_template/InvestorPitch.json`

## Overview

The **Investor Pitch** agent speaks as the founder of UW-Crushes presenting to investors. It uses the full pitch deck as its knowledge base—problem, solution, market, product, business model, adoption, competition, team, financials, and the ask. Serious, professional, and concise.

## Tech

- **TTS:** ElevenLabs (`eleven_multilingual_v2`)
- **LLM:** Google Gemini (`gemini-2.0-flash-001`)

## Generate the config

The agent prompt is built from slide content in `docs/demo/slides/`. After editing any slide, regenerate the config:

```bash
python generate_pitch_agent.py [--slides-dir PATH] [--output PATH]
```

This writes/updates `agent_template/InvestorPitch.json` with the full deck in the system prompt.

## Run

```bash
python rime_agent.py dev --config InvestorPitch.json
```

The agent will greet as the founder, answer questions from the deck, and stay in character.

## Requirements

- `GOOGLE_API_KEY` or Google API access for Gemini (see main [README](../README.md) env section).
