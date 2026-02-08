"""
Snowflake Agentic RAG tool: query Snowflake Cortex (RAG/COMPLETE) from the voice agent.
Use when the agent needs answers from enterprise data or a knowledge base in Snowflake.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger("snowflake-rag-tool")

# Lazy import so agent runs without Snowflake if tool not used
_connector = None

def _get_connector():
    global _connector
    if _connector is None:
        try:
            import snowflake.connector
            _connector = snowflake.connector
        except ImportError:
            raise ImportError(
                "snowflake-connector-python is required for the Snowflake RAG tool. "
                "Install with: pip install snowflake-connector-python"
            )
    return _connector


def _run_snowflake_sync(question: str, model: str, system_instruction: Optional[str], custom_sql: Optional[str]) -> str:
    """Run Snowflake Cortex COMPLETE (or custom RAG SQL) in a sync way. Call from async via to_thread."""
    conn = None
    try:
        snowflake = _get_connector()
        account = os.getenv("SNOWFLAKE_ACCOUNT")
        user = os.getenv("SNOWFLAKE_USER")
        password = os.getenv("SNOWFLAKE_PASSWORD")
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "")
        database = os.getenv("SNOWFLAKE_DATABASE", "")
        schema = os.getenv("SNOWFLAKE_SCHEMA", "")
        role = os.getenv("SNOWFLAKE_ROLE")

        if not account or not user:
            return "Snowflake is not configured (set SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER)."

        connect_params: dict[str, Any] = {
            "account": account.strip(),
            "user": user.strip(),
            "warehouse": warehouse.strip() or None,
            "database": database.strip() or None,
            "schema": schema.strip() or None,
        }
        if password:
            connect_params["password"] = password.strip().strip('"').strip("'")
        elif os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH"):
            with open(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"], "rb") as f:
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.backends import default_backend
                pkey = serialization.load_pem_private_key(
                    f.read(),
                    password=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASS") or None,
                    backend=default_backend(),
                )
            connect_params["private_key"] = pkey
        else:
            return "Snowflake credentials missing (set SNOWFLAKE_PASSWORD or SNOWFLAKE_PRIVATE_KEY_PATH)."

        if role:
            connect_params["role"] = role.strip()

        conn = snowflake.connect(**connect_params)
        cursor = conn.cursor()

        if custom_sql:
            # User-provided SQL (e.g. CALL my_rag_proc(?) or SELECT ... CORTEX.COMPLETE(...))
            # Assume single ? placeholder for the question
            cursor.execute(custom_sql, (question,))
        else:
            # Default: SNOWFLAKE.CORTEX.COMPLETE(model, conversation_array, options)
            # With array + options, response is JSON: {"choices":[{"messages":"..."}], ...}
            prompt_arr = [{"role": "user", "content": question}]
            if system_instruction:
                prompt_arr.insert(0, {"role": "system", "content": system_instruction})
            prompt_json = json.dumps(prompt_arr)
            sql = "SELECT SNOWFLAKE.CORTEX.COMPLETE(%s, PARSE_JSON(%s), {}) AS response"
            cursor.execute(sql, (model, prompt_json))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return "No response from Snowflake."
        out = row[0]
        if out is None:
            return "Empty response from Snowflake."
        out_str = str(out).strip()
        # When using array+options, COMPLETE returns JSON; extract the message text
        if out_str.startswith("{"):
            try:
                data = json.loads(out_str)
                choices = data.get("choices") or []
                if choices and isinstance(choices[0], dict) and "messages" in choices[0]:
                    return (choices[0]["messages"] or "").strip()
            except (json.JSONDecodeError, KeyError, IndexError):
                pass
        return out_str
    except Exception as e:
        logger.exception("Snowflake RAG error: %s", e)
        return f"I couldn't get an answer from the knowledge base: {e!s}."
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


async def get_snowflake_rag_response(
    question: str,
    *,
    model: Optional[str] = None,
    system_instruction: Optional[str] = None,
    custom_sql: Optional[str] = None,
) -> str:
    """
    Run agentic RAG on Snowflake: ask a natural-language question and get an answer
    using Snowflake Cortex (COMPLETE) or a custom RAG stored procedure/SQL.

    Set in .env:
      SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD (or private key),
      optionally SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA, SNOWFLAKE_ROLE.
    Optional: SNOWFLAKE_RAG_SQL for custom SQL (one ? for the question).
    Optional: SNOWFLAKE_RAG_SYSTEM_INSTRUCTION for default system prompt.
    """
    model = model or os.getenv("SNOWFLAKE_RAG_MODEL", "mistral-large")
    system_instruction = system_instruction or os.getenv("SNOWFLAKE_RAG_SYSTEM_INSTRUCTION")
    custom_sql = custom_sql or os.getenv("SNOWFLAKE_RAG_SQL")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: _run_snowflake_sync(question, model, system_instruction, custom_sql),
    )
