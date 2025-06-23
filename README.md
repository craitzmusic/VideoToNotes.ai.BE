# VideoToNotes.ai - Complete Setup and Usage Guide

This document details step by step how to configure, run, and use the VideoToNotes.ai project, 
which performs audio/video transcription and summarization using the OpenAI Whisper and GPT APIs, 
exposed via a FastAPI backend.

---

## 1. Prerequisites

- Python 3.12 or higher
- Docker and Docker Compose (recommended for isolation and reproducibility)
- git (to clone the repository)
- FFmpeg (if not using Docker)
- (Optional) Homebrew for installing dependencies on Mac/Linux, if not using Docker
- An OpenAI account and a valid `OPENAI_API_KEY` (required for transcription and summarization)

---

## 2. Cloning the project

1. Clone the repository (replace the URL with your project):

    git clone https://github.com/youruser/VideoToNotes.ai.git
    cd VideoToNotes.ai

---

## 3. Virtual environment setup (without Docker)

1. Create a Python virtual environment:

        python3 -m venv venv

2. Activate the virtual environment:

    On Linux/macOS:

        source venv/bin/activate

    On Windows:

        venv\Scripts\activate

3. Install dependencies:

    pip install -r requirements.txt

4. Create a `.env` file based on `.env.example` and set your environment variables (e.g., `OPENAI_API_KEY`).

---

## 4. Running locally (without Docker)

1. Make sure the virtual environment is active.
2. Run the app with uvicorn:

    uvicorn app.main:app --reload

3. The server will be running at:

    http://127.0.0.1:8000

4. To transcribe an audio or video file, use the POST `/transcribe` endpoint (see curl example below).

---

## 5. Using Docker (recommended for production)

1. In the root directory, you should already have a Dockerfile and docker-compose.yml configured.
2. To build and start the container:

    docker-compose up --build

3. The app will be available at:

    http://localhost:8000

4. To stop the container:

    docker-compose down

---

## 6. Important notes and tips

- The project uses the OpenAI Whisper API for transcription and OpenAI GPT models for summarization by default.
- You must set the `OPENAI_API_KEY` environment variable for the backend to work.
- FFmpeg is required for audio extraction from video files (already included in the Docker image).
- The `.env` file is used to store environment variables (e.g., API keys).
- Use Docker to avoid local installation of FFmpeg and other dependencies.
- For large uploads, configure both server and client to accept larger files (OpenAI has a 25MB limit per file).
- For development, `uvicorn --reload` restarts the server on code changes.
- Temporary files are automatically cleaned up after processing.
- Whisper is configured for the "base" model by default, but you can change this in the code.
- For video files, audio is automatically extracted using ffmpeg.
- If you want to use a local model (e.g., T5) for summarization, set the provider via query string (`?provider=t5`).

---

## 7. Project structure

    /app
      /main.py           # Main FastAPI application
      /questions.py      # Question generation logic
      /flashcards.py     # Flashcard generation logic
      /studyplan.py      # Study plan generation logic
      /utils.py          # Utility functions (token verification, etc)
    Dockerfile           # Docker container configuration
    docker-compose.yml   # Orchestrates container with volumes and ports
    requirements.txt     # Python dependencies
    .env.example         # Example environment variables

---

## 8. Usage examples (curl)

Transcribe audio or video via curl (replace file.mp3 with your file):

    curl -X POST "http://localhost:8000/transcribe" -F "file=@file.mp3" -H "Authorization: Bearer <your_jwt_token>"

You can specify the summarization provider (optional, defaults to OpenAI):

    curl -X POST "http://localhost:8000/transcribe?provider=t5" -F "file=@file.mp3" -H "Authorization: Bearer <your_jwt_token>"

---

## 9. Common issues and solutions

- 'python-multipart' not installed:

    pip install python-multipart

- 'ffmpeg not found':
  Install ffmpeg or run via Docker.

- 'OPENAI_API_KEY not set' or authentication errors:
  Make sure you have a valid OpenAI API key in your environment or `.env` file.

- 'File too large' errors:
  OpenAI Whisper API has a 25MB file size limit. Compress your audio/video or split into smaller parts.

- 'AttributeError whisper.load_model':
  Make sure to install the correct library:

    pip install openai-whisper

- 500 error on summary:
  Check your OpenAI API key and usage limits.

---

## 10. Next steps for improvement

- Add more robust authentication to the API
- Improve error handling and logging
- Add support for more languages and models
- Progressive upload and feedback via WebSocket

---

## Contact

Project developed by Camilo Raitz - Adapted for VideoToNotes.ai
Email: craitz@gmail.com
GitHub: https://github.com/craitz

---

End of document.