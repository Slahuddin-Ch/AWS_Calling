# slahuddin-ch-aws_calling

An AI-based voice assistant that uses **Twilio** for telephony, **OpenAI** (GPT & Whisper) for speech recognition and language understanding, and **Gradio** for a simple web-based chatbot interface.

## Directory Structure
```
slahuddin-ch-aws_calling/
├── chatbot.py
├── instructions.txt
├── main.py
├── requirements.txt
└── tools.py
```

- **chatbot.py**: Contains logic for transcribing audio, integrating with the OpenAI API for chatbot responses, and setting up the Gradio interface.
- **instructions.txt**: Holds the system prompt detailing how the assistant should behave.
- **main.py**: Handles incoming phone calls via Twilio, streams audio to OpenAI for real-time transcription and response, and returns synthesized speech back to the caller.
- **requirements.txt**: Lists all Python dependencies needed.
- **tools.py**: Defines the function(s) that OpenAI can call to fetch user data or other external information.

## Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone <your_repo_url>
   cd slahuddin-ch-aws_calling
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create or update your `.env` file with:
   ```ini
   OPENAI_API_KEY=YOUR_OPENAI_API_KEY
   TWILIO_ACCOUNT_SID=YOUR_TWILIO_ACCOUNT_SID
   TWILIO_AUTH_TOKEN=YOUR_TWILIO_AUTH_TOKEN
   TWILIO_PHONE_NUMBER=YOUR_TWILIO_PHONE_NUMBER
   NGROK_URL=YOUR_NGROK_HTTPS_URL
   PORT=5050
   ```
   - `OPENAI_API_KEY` is required for accessing OpenAI endpoints.
   - `TWILIO_*` variables are required for Twilio integration to handle phone calls.
   - `NGROK_URL` is the public URL that Twilio should use for media streaming.
   - `PORT` defines the port on which the FastAPI server runs (default 5050).

4. **Run the Application:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 5050
   ```
   - The server starts and is ready to handle incoming calls via Twilio webhook (`/incoming-call`) and a WebSocket media stream (`/media-stream`).

5. **Using the Gradio Chatbot (Optional):**
   - The `chatbot.py` script provides a local Gradio web interface for testing or demonstration. Launch it:
     ```bash
     python chatbot.py
     ```
   - You can open the local URL (e.g., `http://127.0.0.1:7860/`) to access the chatbot interface.

## How It Works

1. **Incoming Phone Call**:
   - Twilio triggers the `/incoming-call` endpoint, which responds with TwiML instructing Twilio to establish a media stream.
2. **Media Stream & OpenAI**:
   - The `/media-stream` WebSocket endpoint receives the audio in G711 format from Twilio.
   - Audio is relayed in real-time to OpenAI’s Whisper model for transcription. The GPT model processes the text and generates a response.
   - OpenAI returns synthesized audio in small chunks, which are forwarded back to Twilio and played to the caller.
3. **Chatbot**:
   - A Gradio UI is also provided for text or audio input. It uses OpenAI to generate responses and demonstrates the same logic and tool-calling mechanism.

## License
This project is provided for demonstration and educational purposes.

---