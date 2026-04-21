# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "livekit-agents",
#     "livekit-plugins-elevenlabs",
#     "livekit-plugins-openai",
#     "livekit-plugins-anthropic",
#     "livekit-plugins-google",
#     "livekit-plugins-silero",
#     "livekit-plugins-noise-cancellation",
#     "python-dotenv",
#     "requests",
#     "aiohttp",
# ]
# ///

import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    ChatContext,
    ChatMessage,
    FunctionTool,
    JobContext,
    ModelSettings,
    cli,
    function_tool,
    inference,
)
from livekit.plugins import silero, anthropic

# Ensure the project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from galatea_livekit.providers import ElevenLabsTTS, ElevenLabsSTT
from galatea_livekit.bus.events import InboundMessage, OutboundMessage
from galatea_livekit.bus.queue import MessageBus
from galatea_livekit.utils.paths import PathManager

# Configure logging
logger = logging.getLogger("galatea-voice-agent")
logger.setLevel(logging.INFO)

load_dotenv()

class GalateaVoiceAgent(Agent):
    def __init__(self, instructions: str, tools: list[FunctionTool]) -> None:
        super().__init__(instructions=instructions, tools=tools)

    async def llm_node(
        self, chat_ctx: ChatContext, tools: list[FunctionTool], model_settings: ModelSettings
    ):
        return Agent.default.llm_node(self, chat_ctx, tools, model_settings)

def load_workspace() -> dict:
    """Load config.json, SOUL.md, and SKILLS.md from the .galatea directory."""
    config_path = PathManager.get_config_path()
    soul_path = PathManager.get_soul_path()
    skills_path = PathManager.get_skills_path()
    
    config = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to load config.json: {e}")

    soul = soul_path.read_text(encoding="utf-8") if soul_path.exists() else "You are a helpful assistant."
    skills = skills_path.read_text(encoding="utf-8") if skills_path.exists() else ""

    return {
        "config": config,
        "soul": soul,
        "skills": skills,
    }

server = AgentServer()

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    logger.info(f"Starting Galatea Voice Session: {ctx.room.name}")
    
    # 1. Load Workspace
    workspace = load_workspace()
    cfg = workspace["config"]
    
    system_prompt = f"{workspace['soul']}\n\nCORE SKILLS AND CAPABILITIES:\n{workspace['skills']}"
    
    agent_name = cfg.get("name", "Natasha")

    # 2. Data Structures: Queues for Bus Integration
    bus = MessageBus()
    chat_id = f"voice_{ctx.room.name}"

    # 3. Tools for Agent to interact with the Galatea Ecosystem
    @function_tool(description=f"Send a physical or system command to {agent_name}'s processing loop.")
    async def command_body(
        text: Annotated[str, "The command or intent to send to the internal system"]
    ) -> str:
        logger.info(f"Tool Call: command_body text='{text}'")
        msg = InboundMessage(
            source="voice",
            user_id="user",
            chat_id=chat_id,
            text=text
        )
        await bus.publish_inbound(msg)
        return "Command sent to system bus."

    # 4. Initialize Agent & Session
    agent = GalateaVoiceAgent(
        instructions=system_prompt,
        tools=[command_body],
    )

    # Use ElevenLabs for BOTH TTS and STT
    voice_id = cfg.get("voice_id") or os.getenv("ELEVEN_VOICE_ID", "95XPUDALaQL1LY3I023E")
    llm_model = cfg.get("llm_model", "claude-haiku-4-5")
    llm_provider = cfg.get("provider", "anthropic").lower()

    if llm_provider == "anthropic":
        llm = anthropic.LLM(model=llm_model)
    elif llm_provider == "openai":
        from livekit.plugins import openai
        llm = openai.LLM(model=llm_model)
    elif llm_provider == "google":
        from livekit.plugins import google
        llm = google.LLM(model=llm_model)
    else:
        llm = inference.LLM(llm_model)

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=ElevenLabsSTT(), 
        llm=llm,
        tts=ElevenLabsTTS(voice_id=voice_id),
        tools=[command_body]
    )

    # 5. Listen for Outbound Queue (Responses from System)
    async def _listen_outbound():
        async for msg in bus.subscribe_outbound("voice"):
            if msg.chat_id == chat_id:
                logger.info(f"Speaking outbound message from bus: {msg.text}")
                await session.say(msg.text)

    asyncio.create_task(_listen_outbound())

    # 6. Bridge Speech Commitment directly to Inbound Queue
    @session.on("user_speech_committed")
    def _on_speech(msg):
        text = msg.text.strip()
        if text:
            asyncio.create_task(bus.publish_inbound(InboundMessage(
                source="voice",
                user_id="user",
                chat_id=chat_id,
                text=text
            )))

    await session.start(agent, room=ctx.room)
    
    # Ready and listening without robotic greeting
    logger.info(f"{agent_name} is now connected and listening.")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("console")
    cli.run_app(server)
