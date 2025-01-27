# Install prequisties

1. To ensure your environment is ready for Twilio, LiveKit, and OpenAI integration, install the necessary Python packages. Run the following command in your terminal:

   ```bash
   pip install openai twilio websocket-client livekit livekit-agents livekit-plugins-openai
   ```

2. Install the LiveKit SDK. [Link](https://docs.livekit.io/home/cli/cli-setup/)

   - macos

   ```bash
   brew install livekit-cli
   ```

   - Windows

   ```bash
   winget install LiveKit.LiveKitCLI
   ```

3. Authenticate with LiveKit

   ```bash
   lk cloud auth
   ```

# Useful livekit-cli commands

```
lk sip inbound list
lk sip inbound create inbound_trunk.json
lk sip inbound delete SIP_ID
```

# Preferences

https://livekit.io/
https://docs.livekit.io/agents/overview/
https://docs.livekit.io/agents/quickstarts/voice-agent/
https://github.com/livekit/agents/tree/main/examples/voice-pipeline-agent/llamaindex-rag
https://github.com/lexiconlabsai/rag-saas

https://www.datavise.ai/blog/usage-of-realtime-openai-api-with-twillio-and-livekit
https://gist.github.com/ShayneP/51eabe243f9e7126929ea7e9db1dc683
