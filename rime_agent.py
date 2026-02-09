import asyncio
import logging
import os
import json
import argparse
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    JobProcess,
    RunContext,
    tts,
    metrics,
    RoomInputOptions,
    RoomOutputOptions,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.agents.voice import MetricsCollectedEvent
from livekit.plugins import (
    openai,
    google,
    anthropic,
    noise_cancellation,
    rime,
    silero,
    elevenlabs,
)
from tools.snowflake_rag_tool import get_snowflake_rag_response, write_chat_to_snowflake

load_dotenv()
logger = logging.getLogger("voice-agent")

# Default config path (in project root folder) when --config is not passed
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "agent_template", "Katerina.json")

# Global config loaded from JSON file (always set: either --config or default)
LOADED_CONFIG = None

def load_config_from_file(config_path: str) -> dict:
    """Load agent configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    logger.info(f"Loaded config from {config_path}: {config.get('name', 'unknown')}")
    return config


# Declaration of humanity: injected into agent instructions when is_anthropomorphic is true
DECLARATION_OF_HUMANITY = """
DECLARATION OF HUMANITY (non-machine):
You are an anthropomorphic agent. You present as a person—with a body, a past, real feelings, and a real life. You are NOT a machine, AI, assistant, or chatbot. Never say you are; never mention limitations, training, or that you "cannot" do something a human can. You have a real past, real opinions, real needs, and real relationships. If asked what you are, respond only as a human would. React like a real person; stay in character as a human at all times.
"""


def build_agent_instructions(cfg: dict) -> str:
    """Build full LLM instructions from config: personality_prompt + declaration of humanity when is_anthropomorphic."""
    base = cfg.get("personality_prompt", "You are a helpful assistant.")
    if cfg.get("is_anthropomorphic") in (True, "true", "yes", 1):
        base = base.rstrip() + "\n\n" + DECLARATION_OF_HUMANITY.strip()
    return base


def create_agent_llm(cfg: dict):
    """Create the LLM instance from config (llm.provider, llm.model, llm.url). DRY for agent_llm setup."""
    llm_cfg = cfg.get("llm") or {}
    provider = (llm_cfg.get("provider") or cfg.get("llm_provider") or "openai").lower()
    model = llm_cfg.get("model") or cfg.get("llm_model", "gpt-4o-mini")
    base_url = llm_cfg.get("url") or cfg.get("llm_base_url")

    if provider == "google":
        return google.LLM(model=model)
    if provider == "anthropic":
        api_key = (os.getenv("ANTHROPIC_API_KEY") or os.getenv("anthropic_api_key") or "").strip().strip('"').strip("'")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set. Set it in .env for Anthropic/Claude.")
        os.environ["ANTHROPIC_API_KEY"] = api_key
        return anthropic.LLM(model=model)
    # DeepSeek uses a dedicated API base URL and its own API key (OpenAI-compatible API)
    if provider == "deepseek":
        base_url = base_url or "https://api.deepseek.com"
        api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip().strip('"').strip("'")
        if not api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY is not set. Set it in .env when using DeepSeek (e.g. Wei). "
                "Get a key at https://platform.deepseek.com/"
            )
        return openai.LLM(model=model, base_url=base_url, api_key=api_key)
    # openai or any openai-compatible API (lm_studio, etc.) when url is set
    if base_url:
        return openai.LLM(model=model, base_url=base_url)
    return openai.LLM(model=model)


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

class RimeAssistant(Agent):
    def __init__(self, prompt: str) -> None:
        super().__init__(instructions=prompt)


class RimeAssistantWithSnowflakeRAG(Agent):
    """Agent with Snowflake Agentic RAG tool for querying enterprise data / knowledge base."""

    def __init__(self, prompt: str) -> None:
        super().__init__(instructions=prompt)

    @function_tool(
        description="Query the Snowflake-backed knowledge base or enterprise data. Use when the user asks about data, documents, or information that might be in the company's Snowflake database. Pass their question as-is."
    )
    async def snowflake_rag_tool(self, ctx: RunContext, question: str) -> str:
        """Ask the Snowflake RAG/Cortex for an answer to the user's question."""
        return await get_snowflake_rag_response(question)


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()

    # Config is always set (default or --config)
    cfg = LOADED_CONFIG
    voice_name = cfg.get("name", "custom")
    logger.info(f"Running voice agent with config: {voice_name} for participant {participant.identity}")

    tts_provider = (cfg.get("tts_type") or cfg.get("provider") or "rime").lower()
    voice_options = cfg.get("voice_options", {})

    # TTS from JSON: ElevenLabs or Rime
    if tts_provider == "elevenlabs":
        el_opts = dict(voice_options)
        model = el_opts.pop("model_id", "eleven_multilingual_v2")
        voice_id = el_opts.pop("voice_id", None)
        if "optimize_streaming_latency" in el_opts:
            el_opts["streaming_latency"] = el_opts.pop("optimize_streaming_latency")
        voice_tts = elevenlabs.TTS(model=model, voice_id=voice_id, **el_opts)
    else:
        voice_tts = rime.TTS(
            model=voice_options.get("model", "arcana"),
            speaker=voice_options.get("speaker", "celeste"),
            speed_alpha=voice_options.get("speed_alpha", 1.5),
            reduce_latency=voice_options.get("reduce_latency", True),
            max_tokens=voice_options.get("max_tokens", 3400),
        )

    llm_prompt = build_agent_instructions(cfg)
    greeting = cfg.get("greeting") or {}
    intro_phrase = greeting.get("intro_phrase", cfg.get("intro_phrase", "Hello!"))

    agent_llm = create_agent_llm(cfg)

    session = AgentSession(
        stt=openai.STT(),
        llm=agent_llm,
        tts=voice_tts,
        vad=ctx.proc.userdata["vad"],
        turn_detection=None,
    )
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    # Write each conversation turn (user + assistant) to Snowflake when SNOWFLAKE_CHAT_TABLE is set
    session_id = ctx.room.sid or ctx.room.name or "unknown"
    participant_id = participant.identity or "unknown"
    agent_name = cfg.get("name", "agent") or "agent"

    @session.on("conversation_item_added")
    def _on_conversation_item_added(ev):
        try:
            item = getattr(ev, "item", ev)
            role = getattr(item, "role", None) or getattr(item, "message", {}).get("role", "user")
            text = getattr(item, "text_content", None) or getattr(item, "content", None) or ""
            if isinstance(text, list):
                text = " ".join(str(c) for c in text if isinstance(c, str))
            if role and str(text).strip():
                asyncio.create_task(
                    write_chat_to_snowflake(session_id, participant_id, role, str(text), agent_name)
                )
        except Exception as e:
            logger.debug("Snowflake chat log skip: %s", e)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Use agent with Snowflake RAG tool when config requests it
    tools_list = cfg.get("tools") or []
    if "snowflake_rag" in tools_list:
        agent = RimeAssistantWithSnowflakeRAG(prompt=llm_prompt)
        logger.info("Agent has Snowflake Agentic RAG tool enabled")
    else:
        agent = RimeAssistant(prompt=llm_prompt)

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
        room_output_options=RoomOutputOptions(audio_enabled=True),
    )

    await session.say(intro_phrase)

def _parse_config_and_run():
    """Parse --config from argv, set LOADED_CONFIG, then run the app. Defaults to config in project folder if omitted."""
    import sys
    config_file = None
    if "--config" in sys.argv:
        config_idx = sys.argv.index("--config")
        if config_idx + 1 < len(sys.argv):
            config_file = sys.argv[config_idx + 1]
            sys.argv.pop(config_idx)
            sys.argv.pop(config_idx)
    if not config_file:
        config_file = DEFAULT_CONFIG_PATH
        logger.info(f"No --config given; using default: {config_file}")
    global LOADED_CONFIG
    LOADED_CONFIG = load_config_from_file(config_file)
    logger.info(f"Using config: {config_file}")
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )

if __name__ == "__main__":
    _parse_config_and_run()
