from __future__ import annotations

import logging
import os
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai

# Initialize the logger for the agent
log = logging.getLogger("voice_agent")
log.setLevel(logging.INFO)

async def main_entry(ctx: JobContext):
    log.info("Initiating the entry point")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    log.info(f"OpenAI API Key: {openai_api_key}")
    
    # Connect to the LiveKit room, subscribing only to audio
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for a participant to join the session
    participant = await ctx.wait_for_participant()
    
    # Set up the OpenAI real-time model
    ai_model = openai.realtime.RealtimeModel(
        instructions="You are a helpful assistant and you love kittens",
        voice="shimmer",
        temperature=0.8,
        modalities=["audio", "text"],
        api_key=openai_api_key,
		)

    # Initialize and start the multimodal agent
    multimodal_assistant = MultimodalAgent(model=ai_model)
    multimodal_assistant.start(ctx.room)

    log.info("AI assistant agent has started")

    # Initialize a session and create a conversation interaction
    session_instance = ai_model.sessions[0]
    session_instance.conversation.item.create(
      llm.ChatMessage(
        role="user",
        content="Please begin the interaction with the user in a manner consistent with your instructions.",
      )
    )
    session_instance.response.create()

# Entry point for the application
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=main_entry))