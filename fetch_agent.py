"""Stage 4: an agent that uses your own tools, driven by a plain-English request.

Run: python fetch_agent.py "Get up to 3 backend jobs from the gitlab Greenhouse board"
"""

import asyncio
import sys

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

from job_tools import jobs_server


async def main(request: str) -> None:
    options = ClaudeAgentOptions(
        model="claude-sonnet-5-5",
        tools=[],  # No built-in tools. Only the custom ones below.
        mcp_servers={"jobs": jobs_server},
        # The naming pattern is mcp__<key in mcp_servers>__<tool name>.
        allowed_tools=["mcp__jobs__fetch_greenhouse_jobs", "mcp__jobs__fetch_lever_jobs"],
        permission_mode="dontAsk",
        setting_sources=[],
        max_turns=6,
    )

    async for message in query(prompt=request, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"TOOL: {block.name} {block.input}")
                elif isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage) and message.is_error:
            sys.exit(f"Agent failed: {message.subtype} {message.errors}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python fetch_agent.py "your request"')
    asyncio.run(main(sys.argv[1]))
