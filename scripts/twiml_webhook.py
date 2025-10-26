"""
TwiML webhook server to route incoming calls to LiveKit SIP
This server creates a simple HTTP endpoint that returns TwiML to route calls
"""
from flask import Flask, request, Response
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

LIVEKIT_SIP_URI = os.getenv("LIVEKIT_SIP_URI", "sip:fj64knskkmf.sip.livekit.cloud")

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Handle incoming voice calls and route to LiveKit SIP"""
    caller = request.values.get('From', 'unknown')

    print(f"Incoming call from: {caller}")

    # Generate TwiML to route call to LiveKit SIP URI
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial>
        <Sip>{LIVEKIT_SIP_URI}</Sip>
    </Dial>
</Response>"""

    return Response(twiml, mimetype='text/xml')

@app.route("/status", methods=['POST'])
def status():
    """Handle call status callbacks"""
    return Response("OK", mimetype='text/plain')

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"TwiML webhook server running on port {port}")
    print(f"Routing calls to: {LIVEKIT_SIP_URI}")
    app.run(host='0.0.0.0', port=port, debug=True)
