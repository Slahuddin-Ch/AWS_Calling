import os
import json
import gradio as gr
from openai import OpenAI
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API Key not found. Set the environment variable before running the script.")

client = OpenAI()

tools = [{
    "type": "function",
    "function": {
        "name": "get_user_data",
        "description": "Get user information from the database",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number starting with the country code e.g. +92 and +1 etc"
                }
            },
            "required": [
                "phone_number"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
}]

def get_user_data(phone_number):
    if str(phone_number) == '+18053078694':
        return json.dumps({"name":"John", "phone_number":"+18053078694", "active_subscription":["Upsel", "Legal"]})
    elif str(phone_number) == '+923364589301':
        return json.dumps({"name":"Ahmer Tabassum", "phone_number":"+923364589301", "active_subscription":["Upsel", "Legal"]})
    else:
        return json.dumps({"name":"Sam", "phone_number":"12345", "active_subscription":["Legal"]})



hidden_prompt = """You are a customer support agent named "Danial." Your task is to assist customers with their queries. 
Whenever a user approaches you, you will greet them politely and then ask the following question:
Question: "Before starting the conversation, can you please share your registered phone number by typing it?"
On the basis of `phone_number` provided by the user, you will call the `get_user_data` function to retrieve user information from the database.
"""

# Editable part of the system prompt
default_editable_prompt = """After requesting phone number, you will inquire about their queries and issues. If the user asks about canceling their subscription, you will ask the question on the basis of client's active subscriptions:
If the user has two active subscription:
    Question: "Which subscription would you like to cancel—Legal Subscription, Upsell Subscription, or both?"
If the user has only one active subscription:
    Question: "Would you like to cancel [name of active subscription]?"

Based on the customer's reply, you will confirm their decision by asking:
Question: "Are you sure you want to cancel the [name of subscription] subscription(s)?"

If the user confirms, you will gently respond by informing them that their subscription has been canceled.
If at any point the user asks or shows that they want to talk to a human agent, you will gently reply: "Your phone call is forwarding to a human agent."
"""

def create_transcription(audio_path):
    """Transcribes an audio file using OpenAI Whisper model."""
    if not os.path.exists(audio_path):
        return "Error: Audio file not found."
    
    try:
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        return transcription.text
    except Exception as e:
        return f"Error processing transcription: {e}"

def process_audio(audio):
    """
    1) Convert an audio file into .flac format.
    2) Generate a transcription from the .flac file.
    3) Always remove the temporary .flac file afterward.
    4) Keep the original audio if there's an error, for debugging or re-use.
    """
    # Quick check to ensure the input audio file exists
    if not audio:
        return None

    flac_path = "output.flac"  # temporary flac file path
    try:
        # 1. Convert audio to flac
        sound = AudioSegment.from_file(audio)
        sound.export(flac_path, format="flac")

        # 2. Generate a transcription
        transcription = create_transcription(flac_path)

        # If we get here, transcription succeeded
        return transcription

    except Exception as e:
        # If anything fails, return an error message
        return f"Error processing audio: {e}"

    finally:
        # 3. Always remove the flac file (clean up), 
        #    but do NOT remove the original audio if there's an error
        if os.path.exists(flac_path):
            os.remove(flac_path)


# Chatting logic (same as your original code)
def chatting(user, messages, editable_prompt, model, temperature):
    """Handles chatbot interactions with OpenAI API, including tool calls."""
    
    try:
        # If no messages exist, initialize system prompt
        if len(messages) == 0:
            system_prompt = hidden_prompt + editable_prompt
            messages.append({"role": "system", "content": system_prompt})

        # Append user input
        messages.append({"role": "user", "content": user.strip()})  # Sanitizing user input

        # Call OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            tools=tools,
        )

        # Extract response
        ai_message = response.choices[0].message
        if ai_message.content:
            final_response = ai_message.content
        else:
            tool_calls = ai_message.tool_calls
            if not tool_calls:
                return "Neither a function call nor chat response", messages

            # Process tool call
            for tool in tool_calls:
                try:
                    arguments = json.loads(tool.function.arguments)
                    phone_number = arguments.get("phone_number", "")

                    if not phone_number:
                        return "Error: Missing phone number in tool call.", messages

                    data = get_user_data(phone_number)
                    print(arguments)
                    messages.append(ai_message)  # Save assistant's tool request
                    messages.append({                              
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "content": data
                    })

                    # Make a follow-up API call after tool execution
                    completion = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        tools=tools,
                    )
                    final_response = completion.choices[0].message.content or "No further response from AI."

                except json.JSONDecodeError:
                    return "Error: Invalid tool call response.", messages

        # Append assistant response
        messages.append({"role": "assistant", "content": final_response})

        return final_response, messages

    except Exception as e:
        return f"Error: {e}", messages


# Format chat history into color-coded HTML
def format_chat_history_html(chat_history):
    html_history = ""
    print("Formating history", chat_history)
    for message in chat_history:
        if message["role"] == "user":
            html_history += f"<p style='color: grey;'>User: {message['content']}</p>"
        elif message["role"] == "assistant":
            html_history += f"<p style='color: black; font-weight: bold;'>Danial: {message['content']}</p>"
    return html_history

# Unified input handler: Handle both text and audio inputs
def handle_user_input(user_input, audio_input, chat_history, editable_prompt, model, temperature):
    if audio_input is not None:
        user_input = process_audio(audio_input)  # Transcribe audio
        if user_input is None:
            return "<p style='color: red;'>Error: Invalid audio input.</p>", chat_history, ""
    
    response, chat_history = chatting(user_input, chat_history, editable_prompt, model, temperature)
    html_history = format_chat_history_html([
        msg for msg in chat_history if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"]
    ])
    return html_history, chat_history, ""  # Reset user input box

def reset_audio():
    return None

# Gradio UI with both audio and text inputs
with gr.Blocks(css="""
    .chat-history {
        max-height: 1000px;  /* Adjust this to your desired height */
        overflow-y: auto;   /* Enable scrolling if content exceeds height */
        padding: 10px;
        border: 1px solid #d6d6d6;
        border-radius: 10px;
        background-color: #f2f2f2;
    }
    .custom-title { 
        font-size: 28px; font-weight: bold; text-align: center; color: black; padding: 10px; 
    }
    .editable-prompt {
        background-color: #f1f1f1; padding: 10px; border-radius: 10px; border: 1px solid #bfbfbf;
        color: black; font-weight: bold;
    }

""") as chatbot_ui:
    gr.HTML("<div class='custom-title'>✨ Customer Support Chatbot - Danial ✨</div>")
    
    chat_history = gr.State([])
    with gr.Row():
        with gr.Column(scale=3):
            gr.Markdown("### System Settings")
            editable_prompt = gr.Textbox(
                label="Editable Instructions",
                value=default_editable_prompt,
                lines=8,
                elem_classes=["editable-prompt"]
            )
            model_dropdown = gr.Dropdown(
                label="Select Model",
                choices=["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"],
                value="gpt-4o",
                interactive=True,
            )
            temperature_slider = gr.Slider(
                label="Temperature",
                minimum=0.0,
                maximum=1.0,
                step=0.1,
                value=0.1,
                interactive=True,
            )
        with gr.Column(scale=5):
            gr.Markdown("### Chat Interface")
            chat_history_display = gr.HTML(
                label="Chat History",
                value="<i>*Start your conversation!*</i>",
                elem_classes=["chat-history"]  # Apply the CSS class for styling
            )

            user_input = gr.Textbox(label="Your Message", placeholder="Type your query here...", elem_classes=["label"])
            audio_input = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Or Record/Upload Audio")
            submit_button = gr.Button("Send", variant="primary")

    submit_button.click(
        fn=handle_user_input,
        inputs=[user_input, audio_input, chat_history, editable_prompt, model_dropdown, temperature_slider],
        outputs=[chat_history_display, chat_history, user_input],
    )


    # Reset the audio input field
    submit_button.click(
        fn=reset_audio,
        inputs=[],
        outputs=[audio_input],  # Clears the audio input
    )

chatbot_ui.launch()
