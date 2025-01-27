import asyncio
from datetime import datetime

from aiofile import async_open as open
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero, elevenlabs
import logging

logger = logging.getLogger("voice_ai_agent_v1")
load_dotenv()


class VoiceAIAgent:
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
        logger.info(f"starting voice assistant for participant {participant.identity}")
        
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
            logger.info(f"participant {participant.identity} has phone number {phone_number}")
        
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