# slahuddin-ch-aws_calling

An AI-based voice assistant that uses **Twilio** for telephony, **OpenAI** (Real-time API & Whisper) for speech recognition and language understanding, and **Gradio** for a simple web-based chatbot interface.

## Directory Structure
```
slahuddin-ch-aws_calling/
├── Chatbot/
│   ├── chatbot.py
│   └── requirements.txt
└── Twilio-Calling/
    ├── Dockerfile
    ├── Twilio-README.md
    ├── docker-compose.yaml
    ├── instructions.txt
    ├── main.py
    ├── requirements.txt
    ├── tools.py
    ├── .dockerignore
    └── .gitignore
```

## Twilio-Calling:

- **Dockerfile**: Defines a lightweight containerized environment for deploying the application.
- **Docker-compose.yaml**: Automates the setup and deployment of the Twilio-Calling service using Docker.
- **instructions.txt**: Holds the system prompt detailing how the assistant should behave.
- **main.py**: Handles Twilio WebSocket audio streaming, interacts with OpenAI’s real-time API, and provides responses.
- **requirements.txt**: Lists Python dependencies for Twilio voice assistant.
- **tools.py**: Defines the function(s) that OpenAI can call to fetch user data or other external information.
- **.dockerignore**: Excludes unnecessary files when building the Docker image.
- **.gitignore**: Ensures sensitive and unnecessary files are not tracked by Git.

## Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone <your_repo_url>
   cd slahuddin-ch-aws_calling/Twilio-Calling
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

4. **Local Tunnel with Ngrok:**
   
   To run the application locally and allow Twilio to reach your server, create a tunnel with:
   ```bash
   ngrok http 5050
   ```
   - Copy the generated HTTPS URL from ngrok and set it in your Twilio console for the incoming call webhook. This way, Twilio can forward calls to your local FastAPI server.

5. **Run the Application:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 5050
   ```
   - The server starts and is ready to handle incoming calls via Twilio webhook (`/incoming-call`) and a WebSocket media stream (`/media-stream`).

### Dockerized Implementation
You can also containerize and run this application with Docker by running the following command:
```bash
docker-compose up --build
```
This command builds the image and starts the container, making the app available on the port defined in your Docker Compose file.  
Remember to configure your environment variables (e.g., OpenAI, Twilio credentials) in the Docker Compose file or pass them at runtime.

> **Note:** To run the application locally with Docker Compose, you need to follow Step 4 mentioned above.

## How It Works

1. **Incoming Phone Call**:
   - Twilio triggers the `/incoming-call` endpoint, which responds with TwiML instructing Twilio to establish a media stream.
2. **Media Stream & OpenAI**:
   - The `/media-stream` WebSocket endpoint receives the audio in G711 format from Twilio.
   - Audio is relayed in real-time to OpenAI’s Real Time API for processing. 
   - OpenAI returns synthesized audio in small chunks, which are forwarded back to Twilio and played to the caller.


## License
This project is provided for demonstration and educational purposes.

---