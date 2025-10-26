import asyncio
import logging
import random
import re
import urllib
from datetime import datetime

import aiohttp
from aiofile import async_open as open
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import deepgram, openai, silero

logger = logging.getLogger("weather-demo")
logger.setLevel(logging.INFO)

load_dotenv()


class WeatherAssistant(Agent):
    """Weather assistant that can check weather for any location"""

    def __init__(self):
        super().__init__(
            instructions=(
                "You are a weather assistant created by LiveKit. Your interface with users will be voice. "
                "You will provide weather information for a given location. "
                "Do not return any text while calling the function."
            )
        )

    @function_tool
    async def get_weather(
        self,
        run_ctx: RunContext,
        location: str,
    ):
        """Called when the user asks about the weather. This function will return the weather for the given location.

        Args:
            location: The location to get the weather for
        """
        # Clean the location string of special characters
        location = re.sub(r"[^a-zA-Z0-9]+", " ", location).strip()

        # Get the agent from the run context
        agent = run_ctx.agent

        # Provide a filler message while processing
        filler_messages = [
            "Let me check the weather in {location} for you.",
            "Let me see what the weather is like in {location} right now.",
            "The current weather in {location} is ",
        ]
        message = random.choice(filler_messages).format(location=location)
        logger.info(f"saying filler message: {message}")

        # Say the filler message and add to chat context
        await agent.say(message)

        logger.info(f"getting weather for {location}")
        url = f"https://wttr.in/{urllib.parse.quote(location)}?format=%C+%t"
        weather_data = ""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    weather_data = (
                        f"The weather in {location} is {await response.text()}."
                    )
                    logger.info(f"weather data: {weather_data}")
                else:
                    raise Exception(
                        f"Failed to get weather data, status code: {response.status}"
                    )

        return weather_data


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Create AgentSession with pipeline components
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
    )

    # Create the assistant agent
    assistant = WeatherAssistant()

    # Set up transcription logging
    log_queue = asyncio.Queue()

    @session.on("agent_state_changed")
    def on_agent_state_changed(state: str):
        logger.info(f"Agent state changed to: {state}")

    @session.on("user_transcript")
    def on_user_transcript(transcript: str):
        log_queue.put_nowait(f"[{datetime.now()}] USER:\n{transcript}\n\n")

    @session.on("agent_transcript")
    def on_agent_transcript(transcript: str):
        log_queue.put_nowait(f"[{datetime.now()}] AGENT:\n{transcript}\n\n")

    async def write_transcription():
        async with open("transcriptions.log", "w") as f:
            while True:
                msg = await log_queue.get()
                if msg is None:
                    break
                await f.write(msg)

    write_task = asyncio.create_task(write_transcription())

    async def finish_queue():
        log_queue.put_nowait(None)
        await write_task

    ctx.add_shutdown_callback(finish_queue)

    # Start the assistant session
    await session.start(room=ctx.room, agent=assistant)

    # Listen to incoming chat messages
    chat = rtc.ChatManager(ctx.room)

    async def answer_from_text(txt: str):
        await assistant.say(txt)

    @chat.on("message_received")
    def on_chat_received(msg: rtc.ChatMessage):
        if msg.message:
            asyncio.create_task(answer_from_text(msg.message))

    # Initial greeting
    await assistant.say("Hey", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
