# Snowflake Agentic RAG Tool

This doc describes how to use the **Snowflake Agentic RAG** tool so your voice agent can answer questions from Snowflake-backed data or a RAG knowledge base.

## What it does

When the agent has the `snowflake_rag` tool enabled, it can call Snowflake Cortex (or your custom RAG SQL) with the user’s question and use the result in its reply. That gives you:

- **Simple Cortex COMPLETE:** Direct LLM completion in Snowflake (no retrieval).
- **Agentic RAG:** Your own stored procedure or view that does embed → search → complete (or Cortex Analyst / Cortex Search) and returns one answer; the tool runs it with the user’s question.

## Enable the tool for an agent

In the agent’s JSON (e.g. `agent_template/Wei.json`), add `"snowflake_rag"` to the `tools` array:

```json
"tools": ["snowflake_rag"]
```

If the agent already has other tools (e.g. Rime or MCP tools), add it to the list:

```json
"tools": ["deep_thinking", "empathy", "snowflake_rag"]
```

## Environment variables

In `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `SNOWFLAKE_ACCOUNT` | Yes | Account identifier (e.g. `xy12345.us-east-1`) |
| `SNOWFLAKE_USER` | Yes | Login name |
| `SNOWFLAKE_PASSWORD` | Yes* | Password (*or use key-based auth below) |
| `SNOWFLAKE_WAREHOUSE` | No | Warehouse name |
| `SNOWFLAKE_DATABASE` | No | Default database |
| `SNOWFLAKE_SCHEMA` | No | Default schema |
| `SNOWFLAKE_ROLE` | No | Role (e.g. `SNOWFLAKE.CORTEX_USER`) |
| `SNOWFLAKE_RAG_MODEL` | No | Cortex model (default: `mistral-large`) |
| `SNOWFLAKE_RAG_SYSTEM_INSTRUCTION` | No | System prompt for the Cortex call |
| `SNOWFLAKE_RAG_SQL` | No | Custom SQL with one `?` for the question |

For key-based auth, use `SNOWFLAKE_PRIVATE_KEY_PATH` (and optionally `SNOWFLAKE_PRIVATE_KEY_PASS`) instead of `SNOWFLAKE_PASSWORD`.

## Default behavior (no custom SQL)

If `SNOWFLAKE_RAG_SQL` is not set, the tool runs:

```sql
SELECT SNOWFLAKE.CORTEX.COMPLETE(<model>, [{'role':'system','content':...},{'role':'user','content':<question>}], {}) AS response
```

So the agent gets a single Cortex LLM answer. Use `SNOWFLAKE_RAG_SYSTEM_INSTRUCTION` to steer the style or scope of answers.

## Custom RAG (agentic RAG in Snowflake)

To plug in your own RAG pipeline (embed → search → complete):

1. In Snowflake, create a stored procedure (or view) that:
   - Takes the user question (e.g. one VARCHAR argument).
   - Optionally embeds it, searches your doc/store, then calls `SNOWFLAKE.CORTEX.COMPLETE` (or Cortex Search / Analyst) with the retrieved context.
   - Returns the final answer (e.g. a single string or one row).

2. Set in `.env`:

   ```env
   SNOWFLAKE_RAG_SQL=CALL my_schema.my_rag_procedure(?)
   ```

   The `?` is replaced with the user’s question. The tool expects one result value (e.g. one column) that it returns to the agent.

## Dependency

```bash
pip install snowflake-connector-python
```

It is already listed in `requirements.txt`.

## References

- [COMPLETE (SNOWFLAKE.CORTEX)](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
- [Arctic Agentic RAG (Snowflake)](https://snowflake.com/en/engineering-blog/arctic-agentic-rag-enterprise-ai)
- [RAG with Snowflake Cortex](https://www.snowflake.com/blog/easy-secure-llm-inference-retrieval-augmented-generation-rag-cortex/)
