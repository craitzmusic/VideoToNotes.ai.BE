from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from utils import verify_token, client
import datetime
import json
import re

router = APIRouter()

class StudyPlanRequest(BaseModel):
    text: str
    num_reviews: int = 3  # Quantas revisões sugerir por tópico

class StudyPlanTopic(BaseModel):
    topic: str
    review_dates: List[str]
    notes: str

class StudyPlanResponse(BaseModel):
    plan: List[StudyPlanTopic]

@router.post("/generate_studyplan", response_model=StudyPlanResponse)
async def generate_studyplan(req: StudyPlanRequest, user=Depends(verify_token)):
    if not req.text or len(req.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text content is required")

    # Prompt para o modelo gerar o plano de estudos
    prompt = (
        "Aja como um assistente educacional. A partir do texto abaixo, identifique os principais tópicos e gere um plano de estudos personalizado. "
        "Para cada tópico, sugira {num_reviews} datas de revisão usando a técnica de spaced repetition (ex: 1, 3, 7 dias após o estudo inicial). "
        "Inclua uma breve nota ou dica para cada tópico. Responda SOMENTE com um JSON no formato:\n"
        "{\n  'plan': [\n    { 'topic': '...', 'review_dates': ['2024-06-22', ...], 'notes': '...' }, ...\n  ]\n}\n"
        f"Texto:\n{req.text}\n"
    ).replace("{num_reviews}", str(req.num_reviews))

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente que cria planos de estudo personalizados a partir de textos."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.7,
        )
        content = response.choices[0].message.content
        if not content or len(content.strip()) == 0:
            raise HTTPException(status_code=500, detail="Model returned empty response")
        # Extrair JSON da resposta usando regex para pegar apenas o bloco JSON
        match = re.search(r'\{[\s\S]*\}', content)
        if not match:
            raise HTTPException(status_code=500, detail="Model did not return valid JSON structure")
        try:
            plan_data = json.loads(match.group(0))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"JSON parsing error: {e}")
        if not plan_data.get("plan"):
            raise HTTPException(status_code=500, detail="Invalid study plan structure returned")
        return plan_data
    except HTTPException:
        raise
    except Exception as e:
        print("Error processing study plan:", e)
        raise HTTPException(status_code=500, detail="Failed to generate study plan") 