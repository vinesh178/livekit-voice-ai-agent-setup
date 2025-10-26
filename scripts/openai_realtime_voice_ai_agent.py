from __future__ import annotations

import logging
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import openai

# Load environment variables
load_dotenv()

# Initialize the logger for the agent
log = logging.getLogger("voice_agent")
log.setLevel(logging.INFO)


class VoiceAssistant(Agent):
    """OpenAI Realtime voice assistant that loves kittens"""

    def __init__(self):
        super().__init__(
            instructions="You are a helpful assistant and you love kittens",
        )


async def main_entry(ctx: JobContext):
    log.info("Initiating the entry point")

    # Connect to the LiveKit room, subscribing only to audio
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Create AgentSession with OpenAI Realtime model
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="shimmer",
            temperature=0.8,
            modalities=["audio", "text"],
        )
    )

    log.info("Starting AI assistant agent")

    # Start the session with the assistant agent
    await session.start(room=ctx.room, agent=VoiceAssistant())


# Entry point for the application
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=main_entry))
