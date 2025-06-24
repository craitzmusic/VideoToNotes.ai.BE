# FastAPI imports for API routing and dependency injection
from fastapi import APIRouter, HTTPException, Depends
# Pydantic for request/response data validation
from pydantic import BaseModel
# Typing for type hints
from typing import List
# OpenAI client for GPT-based flashcard generation
from openai import OpenAI
from utils import verify_token, client
import re

# Create a FastAPI router for flashcard-related endpoints
router = APIRouter()

# Request model for flashcard generation
class FlashcardRequest(BaseModel):
    text: str  # The input text to generate flashcards from
    num_flashcards: int = 10  # Number of flashcards to generate (default: 10)

# Response model for a single flashcard
class Flashcard(BaseModel):
    front: str  # The front of the flashcard (question, keyword, or concept)
    back: str   # The back of the flashcard (answer or explanation)

# Endpoint to generate flashcards from input text
@router.post("/generate_flashcards", response_model=List[Flashcard])
async def generate_flashcards(req: FlashcardRequest, user=Depends(verify_token)):
    # Prompt instructs the model to generate flashcards in a strict JSON format
    prompt = (
        f"Generate {req.num_flashcards} flashcards from the text below. "
        "Each flashcard should have a 'front' (question, keyword, or concept) and a 'back' (answer or explanation). "
        "Return ONLY a JSON array, starting your response directly with '[' and nothing before it. Do not add explanations or comments. "
        "Format:\n"
        "[\n"
        "  { \"front\": \"...\", \"back\": \"...\" },\n"
        "  ...\n"
        "]\n"
        f"Text:\n{req.text}\n"
    )

    # Call OpenAI GPT model to generate flashcards
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that creates flashcards for students."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1800,
        temperature=0.7,
    )
    import json
    try:
        # Extract the model's response content
        content = response.choices[0].message.content
        # Use regex to extract the JSON array from the response
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if not match:
            print("Raw model output:", content)
            raise HTTPException(status_code=500, detail="Model did not return valid JSON")
        flashcards = json.loads(match.group(0))
        return flashcards
    except Exception as e:
        print("Error processing flashcards:", e)
        raise HTTPException(status_code=500, detail="Failed to generate flashcards") 