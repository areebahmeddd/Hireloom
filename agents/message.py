import os
from twilio.rest import Client
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
YOUR_WHATSAPP_NUMBER = f"whatsapp:{os.getenv('YOUR_PHONE_NUMBER')}"

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, YOUR_WHATSAPP_NUMBER]):
    raise ValueError("Missing required Twilio environment variables")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_message(message_text):
    try:
        message = client.messages.create(
            body=message_text, from_=TWILIO_WHATSAPP_NUMBER, to=YOUR_WHATSAPP_NUMBER
        )

        return {
            "status": "success",
            "message_sid": message.sid,
            "message": message_text,
            "to": YOUR_WHATSAPP_NUMBER,
            "from": TWILIO_WHATSAPP_NUMBER,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send WhatsApp message: {str(e)}"
        )


def send_media(message_text, media_url):
    try:
        message = client.messages.create(
            body=message_text,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=YOUR_WHATSAPP_NUMBER,
            media_url=[media_url],
        )

        return {
            "status": "success",
            "message_sid": message.sid,
            "message": message_text,
            "media_url": media_url,
            "to": YOUR_WHATSAPP_NUMBER,
            "from": TWILIO_WHATSAPP_NUMBER,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send WhatsApp media message: {str(e)}"
        )
