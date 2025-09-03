import os
import json
import asyncio
import requests
from datetime import datetime
from twilio.rest import Client
from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


async def call_handler(background_tasks: BackgroundTasks):
    print("Initiating survey call")
    try:
        print("Creating TwiML script")
        twiml = create_twiml()

        print(f"Placing call to {YOUR_PHONE_NUMBER}")
        call = client.calls.create(
            twiml=twiml, to=YOUR_PHONE_NUMBER, from_=TWILIO_PHONE_NUMBER
        )

        print("Scheduling recording download")
        background_tasks.add_task(download_recordings, call.sid, 60)

        print("Call initiated successfully")
        return {
            "status": "success",
            "call_sid": call.sid,
            "message": "Call initiated successfully",
            "phone_number": YOUR_PHONE_NUMBER,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


def list_handler():
    recordings_dir = "recordings"

    if not os.path.exists(recordings_dir):
        print("No recordings directory found")
        return {"recordings": [], "total": 0}

    files = os.listdir(recordings_dir)
    mp3_files = [f for f in files if f.endswith(".mp3")]
    json_files = [f for f in files if f.endswith(".json")]

    print(f"Found {len(mp3_files)} recordings and {len(json_files)} summaries")
    return {
        "recordings": mp3_files,
        "summaries": json_files,
        "total_recordings": len(mp3_files),
        "total_calls": len(json_files),
    }


def create_twiml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-IN">Hello, this is an automated survey call. What is your name?</Say>
    <Record maxLength="15" finishOnKey="#" />
    <Pause length="1"/>

    <Say voice="alice" language="en-IN">What is your age?</Say>
    <Record maxLength="10" finishOnKey="#" />
    <Pause length="1"/>

    <Say voice="alice" language="en-IN">What do you do for work?</Say>
    <Record maxLength="20" finishOnKey="#" />
    <Pause length="1"/>

    <Say voice="alice" language="en-IN">Thank you for your time. Have a great day.</Say>
    <Hangup/>
</Response>"""


async def download_recordings(call_sid: str, delay: int = 60):
    await asyncio.sleep(delay)

    try:
        print("Fetching recordings from Twilio")
        recordings = client.recordings.list(call_sid=call_sid)

        if not recordings:
            print("No recordings found for this call")
            return

        recordings_dir = "recordings"
        if not os.path.exists(recordings_dir):
            os.makedirs(recordings_dir)

        questions = ["name", "age", "occupation"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        call_data = {
            "call_sid": call_sid,
            "phone_number": YOUR_PHONE_NUMBER,
            "recordings": [],
        }

        print(f"Processing {len(recordings)} recordings")
        for i, recording in enumerate(recordings):
            question_type = questions[i] if i < len(questions) else f"question_{i + 1}"

            print(f"Downloading recording {i + 1}: {question_type}")
            recording_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Recordings/{recording.sid}.mp3"
            response = requests.get(
                recording_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            )

            if response.status_code == 200:
                filename = (
                    f"{recordings_dir}/{question_type}_{call_sid[:8]}_{timestamp}.mp3"
                )

                with open(filename, "wb") as f:
                    f.write(response.content)

                print(f"Saved: {filename}")
                recording_info = {
                    "question": question_type,
                    "recording_sid": recording.sid,
                    "duration": recording.duration,
                    "filename": filename,
                }

                call_data["recordings"].append(recording_info)

        summary_file = f"{recordings_dir}/call_{call_sid[:8]}_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(call_data, f, indent=2)

        print("Recording download completed")
    except Exception as e:
        print(f"Error downloading recordings: {e}")
