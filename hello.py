"""Stage 1: one query, printing every message the SDK streams back.

Run: python hello.py

Java comparison: query() behaves like a reactive Flux<Message>. `async for` is a
loop that pauses between items while the agent works, and asyncio.run() is the
event loop that drives it, a bit like blocking on the Flux from main().
"""

import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query


async def main() -> None:
    options = ClaudeAgentOptions(
        model="claude-sonnet-5-5",  # Uses less of your Pro quota than Opus.
        tools=[],  # No tools at all, so this is a chatbot and not yet an agent.
        max_turns=1,
        permission_mode="dontAsk",  # Anything needing approval is refused.
        setting_sources=[],  # Ignore your personal Claude Code settings.
    )

    async for message in query(
        prompt="In one sentence, what is an AI agent?", options=options
    ):
        # Messages are plain dataclasses, the Python version of a Java record.
        print(f"\n=== {type(message).__name__} ===")
        print(str(message)[:400])  # The init message is huge, so trim it.


if __name__ == "__main__":  # Python's equivalent of public static void main.
    asyncio.run(main())
