#!/usr/bin/env python3
"""Quick test script to verify ElevenLabs API key works"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is loaded
api_key = os.getenv("ELEVEN_API_KEY")
if not api_key:
    print("❌ ELEVEN_API_KEY not found in environment")
    exit(1)

print(f"✅ ELEVEN_API_KEY found: {api_key[:10]}...{api_key[-4:]}")
print(f"   Length: {len(api_key)} characters")

# Try to import and use ElevenLabs
try:
    from livekit.plugins import elevenlabs
    print("✅ ElevenLabs plugin imported successfully")

    # Try to instantiate TTS (this will validate the API key)
    tts = elevenlabs.TTS()
    print("✅ ElevenLabs TTS initialized successfully")
    print("✅ API key is valid and working!")

except ImportError as e:
    print(f"❌ Failed to import ElevenLabs plugin: {e}")
    print("   Make sure livekit-plugins-elevenlabs is installed")
except Exception as e:
    print(f"❌ Error initializing ElevenLabs TTS: {e}")
    print("   The API key might be invalid")
