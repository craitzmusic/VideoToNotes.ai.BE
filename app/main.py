from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl
import shutil
import subprocess
import tempfile
import whisper
import os
from openai import OpenAI
from transformers import pipeline
from jose import jwt, JWTError
from questions import router as questions_router
from flashcards import router as flashcards_router
from utils import verify_token, client
from studyplan import router as studyplan_router

# =============================
# FastAPI application instance
# =============================
# Disable /docs, /redoc and /openapi.json for security reasons in production
app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# =============================
# Middleware configuration
# =============================
# CORS: Allow all origins (for production, restrict to your frontend domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or replace with ["http://localhost:3000"] for more security
    allow_credentials=True,
    allow_methods=["*"],  # or specify ["POST", "GET", "OPTIONS"]
    allow_headers=["*"],
)

# Enable GZip compression for responses larger than 1000 bytes
app.add_middleware(GZipMiddleware, minimum_size=1000)

# =============================
# External API clients and models
# =============================
# OpenAI client for Whisper API and GPT-based summarization
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load the local Whisper model for audio transcription
model = whisper.load_model("base")

# Load HuggingFace summarization pipeline (T5-small model)
summarizer = pipeline("summarization", model="t5-small")

# =============================
# Environment variables and security
# =============================
DEFAULT_SUMMARY_PROVIDER = os.getenv("DEFAULT_SUMMARY_PROVIDER", "t5")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET", "insecure_dev_secret")

# HTTP Bearer authentication for protected endpoints
security = HTTPBearer()

# If using OpenAI as default, set the API key for openai-python
if DEFAULT_SUMMARY_PROVIDER == "openai" and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# =============================
# Authentication helper
# =============================
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifies the JWT token sent in the Authorization header.
    Raises HTTP 401 if invalid or expired.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, NEXTAUTH_SECRET, algorithms=["HS256"])
        return payload
    except JWTError as e:
        print("JWT validation error:", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
# =============================
# Summarization helper
# =============================
def summarize_text(text: str, provider: str = None) -> str:
    """
    Summarizes the given text using either OpenAI GPT or local T5 model.
    Truncates text to 5000 characters for performance/safety.
    """
    provider = provider or DEFAULT_SUMMARY_PROVIDER
    try:
        if len(text) > 5000:
            text = text[:5000]

        if provider == "openai" and os.getenv("OPENAI_API_KEY"):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes content."},
                    {"role": "user", "content": f"Summarize the following:\n\n{text}"},
                ],
                max_tokens=300,
                temperature=0.5,
            )
            return response.choices[0].message.content.strip()

        # fallback to T5
        summary = summarizer(text, max_length=150, min_length=40, do_sample=False)
        return summary[0]["summary_text"]

    except Exception as e:
        print(f"Error during summarization: {e}")
        return "Summary generation failed."

# =============================
# Audio extraction helper
# =============================
def extract_audio_from_video(video_path, audio_path):
    """
    Extracts audio from a video file using ffmpeg.
    The output is a compressed AAC file (mono, 16kHz, 48kbps) to minimize size for API limits.
    """
    command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "aac",
        "-b:a", "48k",
        "-ac", "1",
        "-ar", "16000",
        audio_path,
    ]
    subprocess.run(command, check=True)

# =============================
# Main transcription endpoint
# =============================
@app.post("/transcribe")
async def transcribe_audio_or_video(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(verify_token)
):
    """
    Receives an audio or video file via upload, extracts audio if needed,
    transcribes using OpenAI Whisper API or local Whisper model,
    summarizes the transcription, and returns both.
    The provider can be set via query string (?provider=openai or ?provider=t5).
    """
    provider = request.query_params.get("provider")  # e.g., ?provider=openai
    suffix = os.path.splitext(file.filename)[1].lower()
    
    # Save uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Determine audio path: extract if video, use as-is if audio
        if suffix in [".mp4", ".mov", ".mkv", ".avi", ".flv", ".wmv"]:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as audio_tmp:
                extract_audio_from_video(tmp_path, audio_tmp.name)
                audio_path = audio_tmp.name
        elif suffix in [".mp3", ".wav", ".m4a", ".aac", ".flac"]:
            audio_path = tmp_path
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        print("Transcribing:", audio_path)

        # Choose the transcription model: OpenAI Whisper API or local Whisper
        if provider == "openai" and OPENAI_API_KEY:
            print("Using OpenAI Whisper API")
            text = transcribe_with_openai_whisper(audio_path)
        else:
            print("Using local Whisper model")
            result = model.transcribe(audio_path, language="en")
            text = result["text"]

        summary = summarize_text(text, provider)

        return {
            "text": text,
            "summary": summary
        }

    finally:
        # Clean up temporary files
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        if suffix in [".mp4", ".mov", ".mkv", ".avi", ".flv", ".wmv"]:
            try:
                os.remove(audio_path)
            except Exception:
                pass

# =============================
# OpenAI Whisper API helper
# =============================
def transcribe_with_openai_whisper(file_path: str) -> str:
    """
    Sends the audio file to OpenAI Whisper API for transcription.
    Returns the transcribed text.
    """
    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return response.text

# =============================
# Routers for additional features (questions, flashcards, study plan)
# =============================
app.include_router(questions_router)
app.include_router(flashcards_router)
app.include_router(studyplan_router)