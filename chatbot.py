import gradio as gr
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

# Fixed hidden part of the system prompt
hidden_prompt = """You are a customer support agent named "Danial." Your task is to assist customers with their queries. 
Whenever a user approaches you, you will greet them politely and then ask the following question:
Question: "Before starting the conversation, can you please share your registered phone number by typing it?"
On the basis of `phone_number` provided by the user, you will call the `get_user_data` function to retrieve user information from the database.
"""

# Editable part of the system prompt
default_editable_prompt = """After requesting phone number, you will inquire about their queries and issues. If the user asks about canceling their subscription, you will ask:
Question: "Which subscription would you like to cancel—Legal Subscription, Upsell Subscription, or both?"

Based on the customer's reply, you will confirm their decision by asking:
Question: "Are you sure you want to cancel the [name of subscription] subscription(s)?"

If the user confirms, you will gently respond by informing them that their subscription has been canceled.

If at any point the user asks or shows that they want to talk to a human agent, you will gently reply: "Your phone call is forwarding to a human agent."
"""

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
                    "description": "Phone number starting with the country code"
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
        return json.dumps({"name":"Dani", "phone_number":"12345", "active_subscription":["Legal"]})


# Simulate a chatting function
def chatting(user, messages, editable_prompt, model, temperature):
    if len(messages) == 0:
        # Combine hidden and editable parts of the system prompt
        system_prompt = hidden_prompt + editable_prompt
        system_message = {"role": "system", "content": system_prompt}
        messages.append(system_message)

    messages.append({"role": "user", "content": user})
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        tools = tools,
    )
    if response.choices[0].message.content:
        print("__Response__")
        final_response = response.choices[0].message.content

    else:
        tool_calls = response.choices[0].message.tool_calls
        for tool in tool_calls:
            arguments = json.loads(tool.function.arguments)
            name = tool.function.name
            id = tool.id
            phone_number = arguments['phone_number']
            # print(id, name, arguments, phone_number)
            print(f"Calling the {name} function...")
            data = get_user_data(phone_number)
            messages.append(response.choices[0].message)
            messages.append({                              
                "role": "tool",
                "tool_call_id": id,
                "content": data
            })

            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
            )
            final_response = completion.choices[0].message.content

    messages.append({"role": "assistant", "content": final_response})
    return final_response, messages


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


# Define the Gradio interface function
def gradio_chatbot(user_input, chat_history, editable_prompt, model, temperature):
    response, chat_history = chatting(user_input, chat_history, editable_prompt, model, temperature)
    # Format chat history for display with colors
    print("History", chat_history)
    html_history = format_chat_history_html([
        msg for msg in chat_history if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"]
    ])
    return html_history, chat_history, ""  # Reset user_input to empty string

# Gradio UI with improved design and monochrome theme
with gr.Blocks(
    css="""
    .custom-title { 
        font-size: 28px; font-weight: bold; text-align: center; color: black; padding: 10px; 
    }
    .chat-history { 
        background-color: #f2f2f2; padding: 10px; border-radius: 10px; border: 1px solid #d6d6d6; 
    }
    .editable-prompt {
        background-color: #e8e8e8; padding: 10px; border-radius: 10px; border: 1px solid #bfbfbf;
        color: black; font-weight: bold;
    }
    """
) as chatbot_ui:
    gr.HTML("<div class='custom-title'>✨ Customer Support Chatbot - Danial ✨</div>")

    chat_history = gr.State([])  # Maintain chat history state

    with gr.Row():
        with gr.Column(scale=3, min_width=250):
            gr.Markdown("### System Settings")
            editable_prompt = gr.Textbox(
                label="Editable Instructions",
                value=default_editable_prompt,
                lines=8,
                placeholder="Edit the instructions here...",
                elem_classes=["editable-prompt"],  # Apply CSS class for styling
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
        with gr.Column(scale=5, min_width=500):
            gr.Markdown("### Chat Interface")
            chat_history_display = gr.HTML(
                label="Chat History",
                value="<i>*Start your conversation!*</i>",
                elem_classes=["chat-history"],  # Apply CSS class for styling
            )
            user_input = gr.Textbox(
                label="Your Message",
                placeholder="Type your query here...",
                interactive=True,
            )
            submit_button = gr.Button("Send", variant="primary")

    # Update chatbot UI on user input
    submit_button.click(
        fn=gradio_chatbot,
        inputs=[user_input, chat_history, editable_prompt, model_dropdown, temperature_slider],
        outputs=[chat_history_display, chat_history, user_input],  # Reset user_input
    )

# Launch the chatbot UI
chatbot_ui.launch()