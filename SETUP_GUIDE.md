# LiveKit Cloud SIP Setup Guide

## Prerequisites
- LiveKit account and project
- Phone number from a SIP trunking provider (DIDlogic, Telnyx, etc.)
- OpenAI API key
- Deepgram API key (optional, for better STT)

## Important Note
LiveKit Cloud SIP doesn't sell phone numbers directly. You need to purchase a phone number from a SIP trunking provider and configure it with LiveKit.

## Step 1: Environment Setup

1. **Create a `.env` file** in your project root:
```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key_here
LIVEKIT_API_SECRET=your_api_secret_here

# Phone Number (use your existing number or get a new one)
PHONE_NUMBER=+1234567890

# AI Provider Keys
OPENAI_API_KEY=your_openai_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
ELEVEN_API_KEY=your_elevenlabs_api_key_here
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install LiveKit CLI**:
```bash
# macOS
brew install livekit-cli

# Windows
winget install LiveKit.LiveKitCLI

# Linux
curl -sSL https://get.livekit.io/cli | bash
```

4. **Authenticate with LiveKit**:
```bash
lk cloud auth
```

## Step 2: Get a Phone Number from SIP Provider

### Option A: DIDlogic (Recommended for LiveKit)
1. **Sign up at DIDlogic**: https://didlogic.com
2. **Purchase a phone number**:
   - Go to "BUY" section
   - Select your country/region
   - Choose a number
   - Complete purchase
3. **Create SIP account**:
   - Go to "SIP" tab
   - Click "Create SIP account"
   - Note your SIP username and password

### Option B: Telnyx
1. **Sign up at Telnyx**: https://telnyx.com
2. **Purchase a phone number**
3. **Configure SIP trunk**
4. **Get SIP credentials**

### Option C: Keep Your Twilio Number
If you want to keep your existing Twilio number, you can:
1. **Keep your Twilio account active**
2. **Use Twilio as the SIP provider**
3. **Configure LiveKit to work with Twilio SIP**

## Step 3: Configure LiveKit Cloud SIP

1. **Run the setup script**:
```bash
python scripts/create_inbound_trunk.py
```

This will:
- Create an inbound trunk in LiveKit Cloud SIP
- Set up dispatch rules for call routing
- Generate configuration files

2. **Configure your SIP trunk in LiveKit**:
   - Go to your LiveKit project dashboard
   - Navigate to "Telephony" → "Configuration"
   - Create a new trunk with your SIP provider details
   - Add your phone number
   - Configure authentication

## Step 3: Run Your Voice Agent

Choose one of these agents:

### Option A: Simple Voice Agent
```bash
python scripts/voice_agent.py
```

### Option B: OpenAI Realtime Agent
```bash
python scripts/openai_realtime_voice_ai_agent.py
```

### Option C: Advanced Agent with Function Calling
```bash
python scripts/save_chatctx.py
```

## Step 4: Test Your Setup

1. **Start your chosen agent**
2. **Call your phone number**
3. **The agent should answer and start a conversation**

## Troubleshooting

### Check LiveKit SIP Status
```bash
lk sip inbound list
lk sip dispatch-rule list
```

### View Logs
The agents will show logs in the terminal. Look for:
- Connection status
- Participant joins
- Speech recognition
- Agent responses

### Common Issues
1. **No answer**: Check if your phone number is properly configured in LiveKit Cloud SIP
2. **Audio issues**: Verify your LiveKit project settings
3. **API errors**: Check your environment variables

## Useful Commands

```bash
# List SIP trunks
lk sip inbound list

# Create a new trunk
lk sip inbound create inbound_trunk.json

# Delete a trunk
lk sip inbound delete TRUNK_ID

# List dispatch rules
lk sip dispatch-rule list

# Create dispatch rule
lk sip dispatch-rule create dispatch_rule.json
```
