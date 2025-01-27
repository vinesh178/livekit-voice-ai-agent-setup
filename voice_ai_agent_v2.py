import os
import uuid
import asyncio
from datetime import datetime

from aiofile import async_open as open
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero, elevenlabs
from llama_index.llms.openai import OpenAI

from utils.memory import AgenticMemory
from logger import get_logger_lambda
from ...chat.service import find_or_create, update_chat, delete_chat
from ...message.service import create_message, get_messages_by_chat_id


log = get_logger_lambda("Health Coach", color='GREEN')


class VoiceAIAgent:
    def __init__(self):
        self.memory = AgenticMemory(
            llm_model="gpt-4o-mini",
            temperature=0.05,
            collection_name="health_coach_memories_vector",
            embedding_model_dims=3072
        )
        self.llm = OpenAI(model="gpt-4o", temperature=0.05, api_key=os.environ.get("OPENAI_API_KEY"))
        self.chatbot_id = "5ae77002-5a5e-45d4-a4c7-aba01026d600"
    
    async def entrypoint(ctx: JobContext):
        initial_ctx = llm.ChatContext().append(
            role="system",
            text=(
                "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
                "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
            ),
        )

        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        # wait for the first participant to connect
        participant = await ctx.wait_for_participant()
        user_id = participant.identity
        log.info(f"starting voice assistant for participant {participant.identity}")
        
        dg_model = "nova-2-general"
        
        # if participant is sip one, update the dg model and 
        # user id with given phone number
        # https://docs.livekit.io/sip/sip-participant/#basic-example
        # https://docs.livekit.io/sip/sip-participant/#sip-attributes
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            # use a model optimized for sip
            dg_model = "nova-2-phonecall"
            # get participant's phone number from sip attributes
            phone_number = participant.attributes['sip.phoneNumber']
            # TODO: fetch user id with given phone number using core-api endpoint
            # if user id is not found, return
            user_id = uuid.uuid4() # temporary user id
            chat_id = uuid.uuid4()
        
        chat = find_or_create(user_id, chat_id, self.chatbot)
        
        
        agent = VoicePipelineAgent(
            vad=silero.VAD.load(),
            stt=deepgram.STT(model=dg_model),
            llm=openai.LLM(),
            tts=elevenlabs.TTS(),
            chat_ctx=initial_ctx,
        )
        agent.start(ctx.room)

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

        await agent.say("Hey, how can I help you today?", allow_interruptions=True)

    def run(self):
        '''Runs the voice assistant'''
        cli.run_app(WorkerOptions(entrypoint_fnc=self.entrypoint))
        

if __name__ == "__main__":
    voice_ai_agent = VoiceAIAgent()
    voice_ai_agent.run()