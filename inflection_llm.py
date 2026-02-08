import json
import logging
import os
from typing import AsyncIterable, List, Optional

import aiohttp
from livekit.agents.llm import (
    LLM,
    ChatContext,
    ChatMessage,
    LLMStream,
    Tool,
    ToolChoice,
)
from livekit.agents.types import (
    APIConnectOptions,
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    NotGivenOr,
)

logger = logging.getLogger("inflection-llm")

class InflectionLLM(LLM):
    def __init__(self, model: str = "Pi-3.1", api_key: Optional[str] = None):
        super().__init__()
        self._model = model
        self._api_key = api_key or os.getenv("INFLECTION_AI_KEY")
        if not self._api_key:
            raise ValueError("INFLECTION_AI_KEY must be set")
        self._api_url = "https://api.inflection.ai/external/api/inference"

    def chat(
        self,
        *,
        chat_ctx: ChatContext,
        tools: Optional[List[Tool]] = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
        tool_choice: NotGivenOr[ToolChoice] = NOT_GIVEN,
        extra_kwargs: NotGivenOr[dict] = NOT_GIVEN,
    ) -> "InflectionLLMStream":
        return InflectionLLMStream(
            self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
            model=self._model,
            api_key=self._api_key,
            api_url=self._api_url,
        )

class InflectionLLMStream(LLMStream):
    def __init__(
        self,
        llm: InflectionLLM,
        *,
        chat_ctx: ChatContext,
        tools: List[Tool],
        conn_options: APIConnectOptions,
        model: str,
        api_key: str,
        api_url: str,
    ):
        super().__init__(llm=llm, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options)
        self._model = model
        self._api_key = api_key
        self._api_url = api_url

    async def _run(self) -> None:
        # Convert ChatContext to Inflection format
        # Inflection expects: {"context": [{"text": "...", "type": "Human" | "AI"}], "config": "Pi-3.1"}
        
        context_data = []
        for msg in self._chat_ctx.messages():
            if msg.role == "user":
                context_data.append({"text": msg.content, "type": "Human"})
            elif msg.role == "assistant":
                context_data.append({"text": msg.content, "type": "AI"})
            elif msg.role == "system":
                 # Inflection doesn't seem to have a dedicated system prompt in the curl example,
                 # commonly we prepend it to the first message or ignore. 
                 # Let's prepend to the first human message if possible, or just add as Human saying "Instructions: ..."
                 # For now, let's treat it as context if it's strictly instruction.
                 # Actually, let's try mapping System -> Human (instruction).
                 context_data.append({"text": f"System Instructions: {msg.content}", "type": "Human"})

        payload = {
            "context": context_data,
            "config": self._model
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self._api_url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    err_text = await resp.text()
                    logger.error(f"Inflection API error: {resp.status} - {err_text}")
                    return

                # Inflection API (based on provided curl) likely returns JSON.
                # If it supports streaming, the curl usually would show headers or we'd know.
                # The provided curl is basic. Let's assume non-streaming for now, 
                # OR check if it returns SSE.
                # Assuming simple JSON response for now based on standard inference APIs unless valid SSE headers.
                # NOTE: LiveKit LLMStream expects chunks.
                
                try:
                    data = await resp.json()
                    # We need to find the text in the response.
                    # Commonly {"text": "..."} or similar. 
                    # Without response docs, I'll assume a 'text' field or similar.
                    # If the user says it works like Pi, maybe just 'text'.
                    
                    # Wait, if it's SSE, we iterate lines.
                    # Let's check generally if we can iterate chunks.
                    
                    full_text = data.get("text") # Guessing field name
                    if not full_text:
                         # Try 'response' or inspect keys
                         logger.info(f"Inflection response keys: {data.keys()}")
                         full_text = data.get("text", "") 

                    # Stream it out as a single chunk if it's not actually streaming
                    if full_text:
                        self._output_chunk(llm.ChatChunk(
                            choices=[
                                llm.Choice(
                                    delta=llm.ChoiceDelta(content=full_text, role="assistant"),
                                    index=0
                                )
                            ]
                        ))
                except Exception as e:
                    logger.error(f"Error parsing Inflection response: {e}")
