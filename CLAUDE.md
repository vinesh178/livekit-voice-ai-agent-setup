# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LiveKit-based voice AI agent setup that integrates Twilio for phone calls with OpenAI/Deepgram for speech processing. The project creates real-time voice assistants that can answer phone calls and have intelligent conversations using various AI providers.

## Environment Setup

### Required Dependencies

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Install LiveKit CLI:
```bash
# macOS
brew install livekit-cli

# Windows
winget install LiveKit.LiveKitCLI

# Linux
curl -sSL https://get.livekit.io/cli | bash
```

Authenticate with LiveKit:
```bash
lk cloud auth
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

**LiveKit Configuration:**
- `LIVEKIT_URL` - Your LiveKit WebSocket URL (wss://...)
- `LIVEKIT_SIP_URL` - LiveKit SIP URI from project settings
- `LIVEKIT_API_KEY` - API key from LiveKit project
- `LIVEKIT_API_SECRET` - API secret from LiveKit project

**Twilio Configuration:**
- `TWILIO_ACCOUNT_SID` - From Twilio Console Account Info
- `TWILIO_AUTH_TOKEN` - From Twilio Console Account Info
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number

**AI Provider Keys:**
- `OPENAI_API_KEY` - For OpenAI Realtime API and LLM
- `DEEPGRAM_API_KEY` - For speech-to-text (STT)
- `ELEVEN_API_KEY` - For ElevenLabs text-to-speech (optional)

## Common Commands

### Initial Setup: Create Twilio SIP Trunk

Run this script ONCE to configure Twilio and LiveKit integration:
```bash
python scripts/create_inbound_trunk.py
```

This script:
- Creates a SIP trunk in Twilio automatically
- Sets up inbound trunk configuration in LiveKit
- Creates dispatch rules for routing calls to rooms with "call-" prefix
- Generates `inbound_trunk.json` and `dispatch_rule.json` files

After running, manually update Voice Configuration in Twilio Console for the SIP trunk.

### Running Voice Agents

**OpenAI Realtime Voice Agent** (Simple multimodal agent):
```bash
python scripts/openai_realtime_voice_ai_agent.py
```
- Uses OpenAI's Realtime API with multimodal capabilities
- Audio-only subscription mode
- Default personality: "helpful assistant who loves kittens"
- Voice: "shimmer", temperature: 0.8

**Voice Pipeline Agent with Function Calling** (Advanced):
```bash
python scripts/save_chatctx.py
```
- Full pipeline with STT (Deepgram), LLM (OpenAI), TTS (OpenAI/ElevenLabs)
- Function calling support (example: weather lookup via wttr.in)
- Saves conversation transcriptions to `transcriptions.log`
- Supports both voice and text chat messages
- VAD (Voice Activity Detection) via Silero

### LiveKit CLI Commands

List inbound SIP trunks:
```bash
lk sip inbound list
```

Create inbound trunk from JSON:
```bash
lk sip inbound create inbound_trunk.json
```

Delete inbound trunk:
```bash
lk sip inbound delete <SIP_ID>
```

## Code Architecture

### Agent Types (LiveKit Agents v1.0)

**Important**: This project uses LiveKit Agents v1.0 API. The legacy `MultimodalAgent` and `VoicePipelineAgent` classes have been replaced with the unified `AgentSession` orchestrator.

**1. OpenAI Realtime Agent** (`scripts/openai_realtime_voice_ai_agent.py`)
- **Architecture**: Uses `AgentSession` with OpenAI Realtime API
- **Entry Point**: `main_entry(ctx: JobContext)`
- **Pattern**:
  - Define `Agent` subclass with instructions
  - Create `AgentSession` with RealtimeModel
  - Start session with `await session.start(room=ctx.room, agent=YourAgent())`
- **Components**:
  - Agent class: `VoiceAssistant(Agent)` with instructions
  - Model: `openai.realtime.RealtimeModel(voice, temperature, modalities)`
  - No separate VAD/STT/TTS needed (handled by Realtime API)
- **Use Case**: Simplest setup for OpenAI realtime conversations with natural-sounding speech

**2. Voice Pipeline Agent** (`scripts/save_chatctx.py`)
- **Architecture**: Uses `AgentSession` with modular STT/LLM/TTS pipeline
- **Entry Point**: `entrypoint(ctx: JobContext)`
- **Pattern**:
  - Define `Agent` subclass with `@function_tool` decorated methods
  - Create `AgentSession` with VAD/STT/LLM/TTS components
  - Start session with agent instance
- **Components**:
  - VAD: `silero.VAD.load()` for voice activity detection
  - STT: `deepgram.STT()` for speech-to-text
  - LLM: `openai.LLM()` for chat responses
  - TTS: `openai.TTS()` for text-to-speech
- **Function Tools**: `@function_tool` decorator on Agent methods (replaces `@llm.ai_callable()`)
- **Events**: `agent_state_changed`, `user_transcript`, `agent_transcript` (replaces committed events)
- **Logging**: Event hooks for transcription logging
- **Use Case**: Production-ready with function calling, pipeline control, transcription

### Function Calling Pattern (v1.0)

Define AI-callable functions as methods in your `Agent` subclass using the `@function_tool` decorator:

```python
from livekit.agents import Agent, RunContext, function_tool

class YourAssistant(Agent):
    def __init__(self):
        super().__init__(instructions="Your agent instructions here")

    @function_tool
    async def your_function(
        self,
        run_ctx: RunContext,
        param: str,
    ):
        """Docstring describes when this function is called.

        Args:
            param: Parameter description
        """
        # Get agent from run context
        agent = run_ctx.agent

        # Optional: say filler message while processing
        await agent.say("Let me check that for you...")

        # Your function logic here
        return result
```

**Key Changes from v0.x**:
- `@llm.ai_callable()` → `@function_tool`
- `AgentCallContext.get_current().agent` → `run_ctx.agent`
- No `llm.FunctionContext` wrapper class needed
- Functions auto-discovered as Agent methods
- Type hints in function signature (no `Annotated[str, llm.TypeInfo(...)]` needed)

### Room Connection Pattern (v1.0)

**New simplified pattern** - no need to wait for participant:
1. `await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)`
2. Create `AgentSession` with model components
3. `await session.start(room=ctx.room, agent=YourAgent())`

**Key Changes from v0.x**:
- No need to call `ctx.wait_for_participant()` explicitly
- Session handles participant connection automatically
- `session.start()` takes `room` and `agent` parameters (not `room` and `participant`)

### Event Handling (v1.0)

**AgentSession events**:
- `@session.on("agent_state_changed")` - Agent state transitions: "initializing", "idle", "listening", "thinking", "speaking"
- `@session.on("user_transcript")` - User speech transcript available
- `@session.on("agent_transcript")` - Agent response transcript available
- `@chat.on("message_received")` - Handle text chat messages in room

**Key Changes from v0.x**:
- `user_speech_committed` → `user_transcript`
- `agent_speech_committed` → `agent_transcript`
- `user_started_speaking` / `user_stopped_speaking` → `user_state_changed`
- `agent_started_speaking` → `agent_state_changed` with state values

### Transcription Logging (v1.0)

`save_chatctx.py` demonstrates logging pattern:
- Queue-based async file writing
- Event hooks: `@session.on("user_transcript")` and `@session.on("agent_transcript")`
- Timestamped entries for user/agent transcripts
- Shutdown callback ensures clean file closure

```python
log_queue = asyncio.Queue()

@session.on("user_transcript")
def on_user_transcript(transcript: str):
    log_queue.put_nowait(f"[{datetime.now()}] USER:\n{transcript}\n\n")

@session.on("agent_transcript")
def on_agent_transcript(transcript: str):
    log_queue.put_nowait(f"[{datetime.now()}] AGENT:\n{transcript}\n\n")
```

## Infrastructure Setup Script

`scripts/create_inbound_trunk.py` handles Twilio/LiveKit integration:

**Key Functions:**
- `create_livekit_trunk()` - Creates Twilio trunk with LiveKit SIP URI
- `create_inbound_trunk()` - Uses `lk` CLI to create LiveKit inbound trunk
- `create_dispatch_rule()` - Routes calls to rooms with "call-" prefix

**Important**: Script uses `subprocess.run()` to execute `lk` CLI commands and parses output for trunk SIDs using regex `ST_\w+`.

## Plugin System

The project uses LiveKit plugin architecture:

- `livekit-plugins-openai` - OpenAI STT/LLM/TTS/Realtime
- `livekit-plugins-deepgram` - Deepgram STT
- `livekit-plugins-elevenlabs` - ElevenLabs TTS
- `livekit-plugins-silero` - Voice Activity Detection
- `livekit-plugins-google` - Google AI services (installed but not used in examples)
- `livekit-plugins-rag` - RAG capabilities (installed but not used in examples)

Import pattern: `from livekit.plugins import openai, deepgram, silero, elevenlabs`

## Testing/Development Workflow

1. Ensure all environment variables are configured in `.env`
2. Run setup script once: `python scripts/create_inbound_trunk.py`
3. Choose agent type and run appropriate script
4. Call your Twilio number to test the voice agent
5. Monitor logs for debugging (agents use Python logging)
6. Check `transcriptions.log` for conversation history (pipeline agent only)

## Resources

**Official Documentation:**
- LiveKit Agents: https://docs.livekit.io/agents/overview/
- Voice Agent Quickstart: https://docs.livekit.io/agents/quickstarts/voice-agent/

**Examples & Playgrounds:**
- LiveKit Agents Playground: https://agents-playground.livekit.io/
- KITT Demo: https://kitt.livekit.io/
- Cartesia Assistant: https://cartesia-assistant.vercel.app/

**Code References:**
- RAG Example: https://github.com/livekit/agents/tree/main/examples/voice-pipeline-agent/llamaindex-rag
