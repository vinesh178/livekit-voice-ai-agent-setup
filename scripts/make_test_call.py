"""
Make a test outbound call that connects to the LiveKit voice agent
"""
from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

# Twilio credentials
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
livekit_sip_uri = os.getenv("LIVEKIT_SIP_URI")

# Your phone number to call (using the verified format)
your_phone_number = "+610413237634"

client = Client(account_sid, auth_token)

# Create TwiML that dials the LiveKit SIP
twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting you to the AI agent.</Say>
    <Dial>
        <Sip>{livekit_sip_uri}</Sip>
    </Dial>
</Response>"""

print(f"Making outbound call to {your_phone_number}...")
print(f"Will connect to LiveKit SIP: {livekit_sip_uri}")

# Make the call
call = client.calls.create(
    to=your_phone_number,
    from_=twilio_number,
    twiml=twiml
)

print(f"\n✅ Call initiated!")
print(f"Call SID: {call.sid}")
print(f"Status: {call.status}")
print(f"\nAnswer your phone and you'll be connected to the AI agent!")
