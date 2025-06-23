from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from openai import OpenAI
import os
from jose import jwt, JWTError
from utils import verify_token, client
import random
import re

# Create a FastAPI router for question-related endpoints
router = APIRouter()

# Request model for question generation
class QuestionRequest(BaseModel):
    text: str  # The input text to generate questions from
    num_questions: int = 5  # Number of questions to generate (default: 5)

# Response model for a single question
class Question(BaseModel):
    enunciado: str  # The question statement
    alternativas: List[str]  # List of the answer alternatives
    correta: int  # Index of the correct alternative
    explicacao: str | None = None  # Optional explanation for the answer

# Endpoint to generate multiple-choice questions from input text
@router.post("/generate_questions", response_model=List[Question])
async def generate_questions(req: QuestionRequest, user=Depends(verify_token)):
    # Prompt instructs the model to generate questions in a strict JSON format
    prompt = (
        f"Crie {req.num_questions} questões de múltipla escolha sobre o texto abaixo. "
        "Cada questão deve ter 4 alternativas, apenas uma correta. "
        "Embaralhe a ordem das alternativas em cada questão, de modo que a correta não seja sempre a primeira. "
        "Responda SOMENTE com um array JSON, começando sua resposta diretamente com '[' e nada antes disso. Não adicione explicações ou comentários. "
        "Formato:\n"
        "[\n"
        "  {\"enunciado\":\"...\", \"alternativas\":[\"...\",\"...\",\"...\",\"...\"], \"correta\":0, \"explicacao\":\"...\" },\n"
        "  ...\n"
        "]\n"
        f"Texto:\n{req.text}\n"
    )

    # Call OpenAI GPT model to generate questions
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um gerador de questões para concursos."},
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
        questions = json.loads(match.group(0))
        # Shuffle alternatives for each question and update the correct index
        for q in questions:
            alternatives = q["alternativas"]
            correct_idx = q["correta"]
            correct_answer = alternatives[correct_idx]
            zipped = list(zip(alternatives, range(len(alternatives))))
            random.shuffle(zipped)
            shuffled_alts, orig_indices = zip(*zipped)
            new_correct_idx = shuffled_alts.index(correct_answer)
            q["alternativas"] = list(shuffled_alts)
            q["correta"] = new_correct_idx
        return questions
    except Exception as e:
        print("Error processing questions:", e)
        raise HTTPException(status_code=500, detail="Failed to generate questions") 