import os
import json
import base64
import asyncio
import websockets
import requests
from tools import tools
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
NGROK_URL = os.getenv('NGROK_URL')  
PORT = int(os.getenv('PORT', 5050))

LOG_EVENT_TYPES = [
    'response.content.done', 
    # 'rate_limits.updated', 
    'response.done',
    'conversation.item.created',
    'input_audio_buffer.committed', 
    'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 
    'session.created',
    # 'response.audio.delta',
    'conversation.item.input_audio_transcription.completed',
    # 'response.function_call_arguments.delta',
    
]



def get_user_data(phone_number):
    if str(phone_number) == '+18053078694':
        return json.dumps({"name":"John", "phone_number":"+18053078694", "active_subscription":["Upsel", "Legal"]})
    else:
        return json.dumps({"name":"Dani", "phone_number":"12345", "active_subscription":["Legal"]})

prompt = "instructions.txt"
with open(prompt, 'r') as file:
    prompt = file.read()

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')
if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
    raise ValueError('Missing Twilio configuration. Please set it in the .env file.')

app = FastAPI()

@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}


@app.post("/incoming-call")
async def handle_incoming_call(request: Request):
    """Handle incoming calls to the AI assistant"""
    print(f"[{datetime.now()}] Incoming call Received....")
    response = VoiceResponse()
    response.say("Welcome to the AI Voice Assistant.")
    print("Name", request.url.hostname)
    response.pause(length=1)
    response.say("You can start talking now!")
    connect = Connect()
    connect.stream(url=f'wss://{request.url.hostname}/media-stream')  
    response.append(connect)
    print(f"[{datetime.now()}]: Incoming call returned...")
    return HTMLResponse(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    print(f"[{datetime.now()}] Client connected")
    await websocket.accept()  
    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17',
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        print(f"[{datetime.now()}] OpenAI connected")
        await send_session_update(openai_ws)
        stream_sid = None
        session_id = None
        async def receive_from_twilio():
            print(f"[{datetime.now()}] Received from Twilio")
            nonlocal stream_sid
            try:
                async for message in websocket.iter_text(): 
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.open:
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()
        async def send_to_twilio():
            print(f"[{datetime.now()}] Send to Twilio")
            nonlocal stream_sid, session_id
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    # if response['type'] in LOG_EVENT_TYPES:
                        # print(f"Received event: {response['type']}", response)
                    if response.get("type") == "error":
                        # print(f"\n\n>>> Received error from OpenAI: {response}\n\n")
                        assert False, "Received error from OpenAI"

                    if response['type'] == 'conversation.item.input_audio_transcription.completed':
                        user_transcript = response['transcript']
                        # print("User_transcript", user_transcript)
                    if response['type'] == 'response.function_call_arguments.done':
                        # print("Function Call Triggered by LLM", response)
                        call_id = response['call_id']
                        name = response['name']
                        args = json.loads(response['arguments'])
                        phone_number = args['phone_number']
                        # print(call_id, name, args, phone_number)

                        data = get_user_data(phone_number)
                        function_call_output = {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": call_id,
                                "output": data
                            }
                        }
                        await openai_ws.send(json.dumps(function_call_output))
                        await openai_ws.send(json.dumps({"type": "response.create"}))
                    try:
                        if response['type'] == 'response.done' and len(response['response']['output']) != 0:
                            if response['response']['output'][0]['type'] == 'message':
                                assistant_transcript = response['response']['output'][0]['content'][0]['transcript']
                                # print("Assistant_Transcript", assistant_transcript)
                        else:
                            pass
                    except Exception as e:
                        print(f"Issue in output list: {e}")

                    if response['type'] == 'response.audio.delta' and response.get('delta'):
                        try:
                            audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": audio_payload
                                }
                            }
                            await websocket.send_json(audio_delta)  
                        except Exception as e:
                            print(f"Error processing audio data: {e}")
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")
        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def send_session_update(openai_ws):
    session_update = {
        "type": "session.update",
        "session": {
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": "alloy",
            "instructions": prompt,
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            "turn_detection": {
            "type": "server_vad",
            "threshold": 0.4,
            "prefix_padding_ms": 500,
            "silence_duration_ms": 600,
        },
            "tools" : tools,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
        }
    }
    print(f"[{datetime.now()}] Session is updating")
    await openai_ws.send(json.dumps(session_update))

