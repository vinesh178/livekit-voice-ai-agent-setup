import asyncio
import logging
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.plugins import deepgram, openai, silero

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

load_dotenv()


class VoiceAssistant(agents.Agent):
    """A helpful voice AI assistant that can have conversations over the phone."""

    def __init__(self):
        super().__init__(
            instructions="""You are a helpful voice AI assistant.
            Be conversational, friendly, and concise in your responses.
            Keep answers brief and to the point since this is a voice conversation."""
        )


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent."""
    logger.info("Starting voice agent...")

    # Connect to the room
    await ctx.connect()
    logger.info(f"Connected to room: {ctx.room.name}")

    # Wait for participant to join
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    # Create the assistant
    assistant = VoiceAssistant()

    # Create the agent session with pipeline configuration
    session = agents.AgentSession(
        agent=assistant,
        stt=deepgram.STT(model="nova-2-general"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="alloy"),
        vad=silero.VAD.load(),
    )

    # Start the session
    session.start(ctx.room, participant)
    logger.info("Agent session started")

    # Log when user speaks
    @session.on("user_speech_committed")
    def on_user_speech(msg: agents.UserSpeechCommittedEvent):
        logger.info(f"User: {msg.user_transcript}")

    # Log agent responses
    @session.on("agent_speech_committed")
    def on_agent_speech(msg: agents.AgentSpeechCommittedEvent):
        logger.info(f"Agent: {msg.agent_transcript}")


async def prewarm(proc: agents.JobProcess):
    """Prewarm function to preload models."""
    logger.info("Prewarming models...")
    await proc.userdata.get_or_create("vad", lambda: silero.VAD.load())


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
