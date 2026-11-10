"""One Claude call that returns validated JSON and has no tools.

Used by score_jobs.py and draft.py. Think of it as a small shared service class:
callers pass prompts and a JSON Schema (like a DTO definition) and get a dict.

With tools=[] Claude cannot read files, run commands or reach the network. That
is the defence against a malicious job posting: even if the text fools the
model, there is nothing for it to abuse. The session's only tool is the SDK's
internal StructuredOutput, which is how Claude hands back the JSON.
"""

from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKError, ResultMessage, query


class StructuredQueryError(Exception):
    """Claude did not produce valid output for this one request."""


async def ask_for_json(
    system_prompt: str, user_prompt: str, schema: dict[str, Any], model: str
) -> dict[str, Any]:
    options = ClaudeAgentOptions(
        model=model,
        system_prompt=system_prompt,
        tools=[],
        output_format={"type": "json_schema", "schema": schema},
        permission_mode="dontAsk",
        setting_sources=[],
        # A little headroom, because each failed schema validation costs a turn.
        max_turns=5,
    )

    result = None
    try:
        async for message in query(prompt=user_prompt, options=options):
            if isinstance(message, ResultMessage):
                result = message
    except ClaudeSDKError as error:
        # query() raises after yielding an error result, so this is an expected
        # path. Like catching a checked exception and rethrowing our own type.
        raise StructuredQueryError(str(error)) from error

    if result is None:
        raise StructuredQueryError("the run ended without a result message")
    if result.subtype != "success" or result.structured_output is None:
        raise StructuredQueryError(f"{result.subtype}: {result.errors}")
    return result.structured_output
