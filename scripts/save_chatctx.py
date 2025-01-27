import asyncio
from datetime import datetime

from aiofile import async_open as open
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero, elevenlabs

import logging
import random
import re
import urllib
from typing import Annotated

import aiohttp
from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import AgentCallContext, VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero

logger = logging.getLogger("weather-demo")
logger.setLevel(logging.INFO)

load_dotenv()


class AssistantFnc(llm.FunctionContext):
    """
    The class defines a set of LLM functions that the assistant can execute.
    """

    @llm.ai_callable()
    async def get_weather(
        self,
        location: Annotated[
            str, llm.TypeInfo(description="The location to get the weather for")
        ],
    ):
        """Called when the user asks about the weather. This function will return the weather for the given location."""
        # Clean the location string of special characters
        location = re.sub(r"[^a-zA-Z0-9]+", " ", location).strip()

        # When a function call is running, there are a couple of options to inform the user
        # that it might take awhile:
        # Option 1: you can use .say filler message immediately after the call is triggered
        # Option 2: you can prompt the agent to return a text response when it's making a function call
        agent = AgentCallContext.get_current().agent

        if (
            not agent.chat_ctx.messages
            or agent.chat_ctx.messages[-1].role != "assistant"
        ):
            # skip if assistant already said something
            filler_messages = [
                "Let me check the weather in {location} for you.",
                "Let me see what the weather is like in {location} right now.",
                # LLM will complete this sentence if it is added to the end of the chat context
                "The current weather in {location} is ",
            ]
            message = random.choice(filler_messages).format(location=location)
            logger.info(f"saying filler message: {message}")

            # NOTE: set add_to_chat_ctx=True will add the message to the end
            #   of the chat context of the function call for answer synthesis
            speech_handle = await agent.say(message, add_to_chat_ctx=True)  # noqa: F841

        logger.info(f"getting weather for {location}")
        url = f"https://wttr.in/{urllib.parse.quote(location)}?format=%C+%t"
        weather_data = ""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    # response from the function call is returned to the LLM
                    weather_data = (
                        f"The weather in {location} is {await response.text()}."
                    )
                    logger.info(f"weather data: {weather_data}")
                else:
                    raise Exception(
                        f"Failed to get weather data, status code: {response.status}"
                    )

        # (optional) To wait for the speech to finish before giving results of the function call
        # await speech_handle.join()
        return weather_data


async def entrypoint(ctx: JobContext):

    fnc_ctx = AssistantFnc()  # create our fnc ctx instance
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a weather assistant created by LiveKit. Your interface with users will be voice. "
            "You will provide weather information for a given location. "
            # when using option 1, you can suppress from the agent with prompt
            "do not return any text while calling the function."
            # uncomment this to use option 2
            # "when performing function calls, let user know that you are checking the weather."
        ),
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # await for a participant to join the room
    participant = await ctx.wait_for_participant()
    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
        fnc_ctx=fnc_ctx,
        chat_ctx=initial_ctx,
    )
    # Start the assistant. This will automatically publish a microphone track and listen to the participant.
    agent.start(ctx.room, participant)

    # listen to incoming chat messages, only required if you'd like the agent to
    # answer incoming messages from Chat
    chat = rtc.ChatManager(ctx.room)

    async def answer_from_text(txt: str):
        chat_ctx = agent.chat_ctx.copy()
        chat_ctx.append(role="user", text=txt)
        stream = agent.llm.chat(chat_ctx=chat_ctx, fnc_ctx=fnc_ctx)
        await agent.say(stream)

    @chat.on("message_received")
    def on_chat_received(msg: rtc.ChatMessage):
        if msg.message:
            asyncio.create_task(answer_from_text(msg.message))

    log_queue = asyncio.Queue()

    @agent.on("user_speech_committed")
    def on_user_speech_committed(msg: llm.ChatMessage):
        # convert string lists to strings, drop images
        if isinstance(msg.content, list):
            msg.content = "\n".join(
                "[image]" if isinstance(x, llm.ChatImage) else x for x in msg
            )
        log_queue.put_nowait(f"[{datetime.now()}] USER:\n{msg.content}\n\n")

    @agent.on("agent_speech_committed")
    def on_agent_speech_committed(msg: llm.ChatMessage):
        log_queue.put_nowait(f"[{datetime.now()}] AGENT:\n{msg.content}\n\n")

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

    await agent.say("Hey", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
