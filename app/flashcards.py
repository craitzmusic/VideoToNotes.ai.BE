from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from utils import verify_token, client
import re

router = APIRouter()

class FlashcardRequest(BaseModel):
    text: str
    num_flashcards: int = 10

class Flashcard(BaseModel):
    front: str
    back: str

@router.post("/generate_flashcards", response_model=List[Flashcard])
async def generate_flashcards(req: FlashcardRequest, user=Depends(verify_token)):
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
        content = response.choices[0].message.content
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if not match:
            print("Raw model output:", content)
            raise HTTPException(status_code=500, detail="Model did not return valid JSON")
        flashcards = json.loads(match.group(0))
        return flashcards
    except Exception as e:
        print("Error processing flashcards:", e)
        raise HTTPException(status_code=500, detail="Failed to generate flashcards") 