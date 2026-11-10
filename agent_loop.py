"""Stage 2: what makes it an agent. Tools plus a loop, printed step by step.

Run: python agent_loop.py

The loop: Claude asks for a tool -> the SDK runs it -> the result goes back to
Claude -> Claude decides what to do next -> repeat until it stops asking.
Your code never writes that loop. You watch it through the message stream.
"""

import asyncio
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

PLAYGROUND = Path.cwd() / "playground"


async def main() -> None:
    PLAYGROUND.mkdir(exist_ok=True)
    (PLAYGROUND / "note.txt").write_text(
        "Spring Boot developer. Learning Python. Building a job search assistant.\n"
    )

    options = ClaudeAgentOptions(
        model="claude-sonnet-5-5",
        cwd=PLAYGROUND,
        # `tools` decides which tools exist at all.
        tools=["Read", "Write"],
        # `allowed_tools` only pre-approves. It does NOT restrict by itself.
        # Edit(...) rules also govern Write. A leading / means "inside cwd".
        allowed_tools=["Read", "Edit(/summary.txt)"],
        # dontAsk turns every unapproved call into a refusal. With it, this
        # agent can write summary.txt and nothing else.
        permission_mode="dontAsk",
        setting_sources=[],
        max_turns=6,  # A safety net against a runaway loop.
    )

    prompt = "Read note.txt, then write a five-word summary of it to summary.txt."
    step = 0

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            # Skip messages holding only hidden thinking, with nothing to show.
            visible = [
                b for b in message.content if isinstance(b, (TextBlock, ToolUseBlock))
            ]
            if not visible:
                continue
            step += 1
            print(f"\n--- Loop step {step}: Claude decides ---")
            for block in visible:
                if isinstance(block, TextBlock):
                    print(f"SAYS: {block.text}")
                elif isinstance(block, ToolUseBlock):
                    print(f"REQUESTS TOOL: {block.name} {block.input}")

        elif isinstance(message, UserMessage) and isinstance(message.content, list):
            # Tool results come back labelled as a "user" message, because
            # from Claude's side they are input it did not produce.
            for block in message.content:
                if isinstance(block, ToolResultBlock):
                    label = "TOOL ERROR" if block.is_error else "TOOL RESULT"
                    print(f"{label}: {str(block.content)[:200]}")

        elif isinstance(message, ResultMessage):
            print(f"\n=== Finished: {message.subtype}, {message.num_turns} turns ===")


if __name__ == "__main__":
    asyncio.run(main())
