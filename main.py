import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

# Configuration
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 5050))

client = Client(account_sid, auth_token)

prompt = "instructions.txt"
with open(prompt, 'r') as file:
    SYSTEM_MESSAGE = file.read()

VOICE = 'sage'

LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created', 'response.content.done', 
    'conversation.item.created',
    'session.created', 'session.updated',
    # 'response.audio.delta',
    'conversation.item.input_audio_transcription.completed',
    'response.function_call_arguments.delta',
    
]

def get_user_data(phone_number):
    if str(phone_number) == '+18053078694':
        return json.dumps({"name":"John", "phone_number":"+18053078694", "active_subscription":["Upsel", "Legal"]})
    elif str(phone_number) == '+923364589301':
        return json.dumps({"name":"Sam", "phone_number":"+923364589301", "active_subscription":["Legal"]})
    elif str(phone_number) == '+923114663661':
        return json.dumps({"name":"Michael", "phone_number":"+923114663661", "active_subscription":["Legal", "Upsel"]})
    else:
        return json.dumps({"name":"","data":"The data against the user's phone number is not found."})
        # return json.dumps({"name":"Dani", "phone_number":"12345", "active_subscription":["Legal", "Upsel"]})

tools = [
            {
                "type": "function",
                "name": "get_user_data",
                "description": "Get the user information from the Database...",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": { "type": "string", "description": "It is phone number of user that consists of country code plus 10 digits, e.g., country code like `+92` and `1` etc and 10 digits like `3332326709`" }
                    },
                    "required": ["phone_number"],

                }
            },
        ]



SHOW_TIMING_MATH = False

app = FastAPI()

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')

@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    form_data = await request.form()
    data = dict(form_data)
    callSid = data['CallSid']
    phone_number = data['Caller']
    print("phone_number",phone_number)
    print(data)
    host = request.url.hostname
    connect = Connect()
    stream = Stream(url=f'wss://{host}/media-stream/{phone_number}')
    connect.append(stream)
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream/{phone_number}")
async def handle_media_stream(websocket: WebSocket, phone_number:str):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    print("websocket", websocket)

    await websocket.accept()
    # Updated part at the beginning of handle_media_stream:
    print("phone_number", phone_number)

    # print("Caller from query params 2:", caller)

# Updated call to initialize_session:
    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17',
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        
        await initialize_session(openai_ws, phone_number)

        # Connection specific state
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None
        
        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.open:
                        latest_media_timestamp = int(data['media']['timestamp'])
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print("Full start event payload:", data['start'])
                        # caller = data['start']['customParameters']['caller']
                        # print("start_event with caller", caller)
                        print(f"Incoming stream has started {stream_sid}")
                        # await initialize_session(openai_ws, caller)

                        response_start_timestamp_twilio = None
                        latest_media_timestamp = 0
                        last_assistant_item = None
                    elif data['event'] == 'mark':
                        
                        if mark_queue:
                            mark_queue.pop(0)
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)

                    if response['type'] == 'conversation.item.input_audio_transcription.completed':
                        user_transcript = response['transcript']
                        print("User_transcript", user_transcript)
                    if response['type'] == 'response.function_call_arguments.done':
                        # print("Function Call Triggered by LLM", response)
                        call_id = response['call_id']
                        name = response['name']
                        if name == 'get_user_data':
                            args = json.loads(response['arguments'])
                            phone_number = args['phone_number']
                            print(call_id, name, args, phone_number)

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
                                print("Assistant_Transcript", assistant_transcript)
                        else:
                            pass
                    except Exception as e:
                        print(f"Issue in output list: {e}")

                    if response.get('type') == 'response.audio.delta' and 'delta' in response:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        audio_delta = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {
                                "payload": audio_payload
                            }
                        }
                        await websocket.send_json(audio_delta)

                        if response_start_timestamp_twilio is None:
                            response_start_timestamp_twilio = latest_media_timestamp
                            if SHOW_TIMING_MATH:
                                print(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                        # Update last_assistant_item safely
                        if response.get('item_id'):
                            # If the item_id has changed, assume a new response is starting.
                            if last_assistant_item is not None and response['item_id'] != last_assistant_item:
                                response_start_timestamp_twilio = latest_media_timestamp
                            last_assistant_item = response['item_id']
                        print("last_assistant_item", last_assistant_item)

                        await send_mark(websocket, stream_sid)

                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("Speech started detected.")
                        if last_assistant_item:
                            print(f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            """Handle interruption when the caller's speech starts."""
            nonlocal response_start_timestamp_twilio, last_assistant_item
            print("Handling speech started event.")
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio +500
                print("Elapsed_time", elapsed_time)
                if SHOW_TIMING_MATH:
                    print(f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                if last_assistant_item:
                    if SHOW_TIMING_MATH:
                        print(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")
                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))

                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })

                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"}
                }
                await connection.send_json(mark_event)
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def send_initial_conversation_item(openai_ws, phone_number):
    """Send initial conversation item if AI talks first."""
    data = get_user_data(phone_number)
    name = json.loads(data)['name']
    print(name)
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"Greet the user with 'Thank you {name} for calling Legal Services. This is LISA, How can I help you?'"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))


async def initialize_session(openai_ws, phone_number: str):
    """Control initial session with OpenAI."""
    print("phone_number", phone_number)
    user_info = get_user_data(phone_number)
    print("user_info", user_info)
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad",
            },
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE + f"\n user information {user_info}",
            "modalities": ["text", "audio"],
            "temperature": 0.8,
            "tools" : tools,

        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))
    await send_initial_conversation_item(openai_ws, phone_number)