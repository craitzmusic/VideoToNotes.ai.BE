from fastapi import APIRouter, HTTPException, Depends, Body, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from utils import verify_token, client
import io
from weasyprint import HTML
import os
import re
from typing import List, Dict
import asyncio
import httpx
from questions import QuestionRequest, generate_questions

router = APIRouter()

class StudyGuidePDFRequest(BaseModel):
    transcript: str  # Raw transcript text
    title: str = "Study Guide"  # Optional custom title

class SegmentTopicsRequest(BaseModel):
    transcript: str  # Raw transcript text
    num_topics: int = 5  # Optional: number of topics to suggest

class Topic(BaseModel):
    title: str
    content: str

class GenerateStructuredGuideRequest(BaseModel):
    transcript: str
    num_topics: int = 5
    num_questions: int = 5

class TopicWithQuiz(BaseModel):
    title: str
    content: str
    quiz: list

@router.post("/segment_topics", response_model=List[Topic])
async def segment_topics(data: SegmentTopicsRequest, user=Depends(verify_token)):
    """
    Receives a transcript and returns a list of didactic topics (title and content) in JSON format.
    Uses ChatGPT to segment the text. All comments and prompts in Portuguese for now.
    """
    # Ultra explicit prompt to force full coverage and avoid summarization
    prompt = (
        f"Divida o texto abaixo em {data.num_topics} tópicos didáticos, cobrindo TODO o conteúdo, sem omitir partes importantes. "
        "É OBRIGATÓRIO que todo o texto seja utilizado, sem resumir, condensar ou omitir trechos. "
        "Cada tópico deve conter um trecho substancial do texto original, mantendo o máximo de conteúdo possível. "
        "NÃO RESUMA. NÃO REESCREVA. Apenas separe o texto em blocos didáticos, mantendo o texto original em cada tópico. "
        "Se necessário, divida o texto em blocos de tamanho semelhante, mas sempre mantendo o texto original. "
        "Para cada tópico, retorne apenas o título e o texto do tópico, sem perguntas, sem sumário, sem introdução ou conclusão geral. "
        "Responda SOMENTE com um array JSON, no formato: [ { 'title': '...', 'content': '...' }, ... ]. "
        "Não adicione explicações, comentários ou qualquer texto fora do JSON.\n"
        f"Texto:\n{data.transcript}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente que segmenta textos em tópicos didáticos."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.5,
        )
        import json
        content = response.choices[0].message.content
        # Extract JSON array from the response
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if not match:
            raise HTTPException(status_code=500, detail="Model did not return valid JSON array.")
        topics = json.loads(match.group(0))
        # Validate structure
        if not isinstance(topics, list) or not all('title' in t and 'content' in t for t in topics):
            raise HTTPException(status_code=500, detail="Invalid topic structure returned.")
        return topics
    except Exception as e:
        print("Error segmenting topics:", e)
        raise HTTPException(status_code=500, detail="Failed to segment topics with ChatGPT.")

def segment_transcript_semantic_spacy(text: str, min_words: int = 100) -> list:
    """
    Segments the transcript into semantic blocks using spaCy (pt_core_news_sm).
    Groups sentences into blocks of at least min_words words, preserving semantic boundaries.
    Returns a list of dicts: { 'content': ... }
    """
    try:
        import spacy
    except ImportError:
        raise ImportError("spaCy is not installed. Please install it with 'pip install spacy' and download the Portuguese model with 'python -m spacy download pt_core_news_sm'.")
    try:
        nlp = spacy.load("pt_core_news_sm")
    except OSError:
        raise OSError("spaCy Portuguese model not found. Run: python -m spacy download pt_core_news_sm")
    doc = nlp(text)
    blocks = []
    current_block = []
    current_word_count = 0
    for sent in doc.sents:
        sent_text = sent.text.strip()
        if not sent_text:
            continue
        sent_words = sent_text.split()
        current_block.append(sent_text)
        current_word_count += len(sent_words)
        if current_word_count >= min_words:
            blocks.append({'content': ' '.join(current_block)})
            current_block = []
            current_word_count = 0
    # Add any remaining sentences as the last block
    if current_block:
        blocks.append({'content': ' '.join(current_block)})
    return blocks

@router.post("/generate_structured_study_guide", response_model=List[TopicWithQuiz])
async def generate_structured_study_guide(
    data: GenerateStructuredGuideRequest,
    user=Depends(verify_token)
):
    """
    Orchestrates the creation of a structured study guide:
    - Segments the transcript into semantic blocks
    - For each block, generates a title (ChatGPT) and a quiz (ChatGPT, in parallel)
    - Returns a list of topics, each with its text and quiz.
    """
    # 1. Segment transcript into semantic blocks
    blocks = segment_transcript_semantic_spacy(data.transcript, min_words=max(80, int(len(data.transcript.split()) / data.num_topics)))

    # Helper async function to formalize a single block
    async def formalize_block_async(block):
        prompt = (
            "Reescreva o texto abaixo de forma formal, clara e didática, removendo gírias, maneirismos, repetições e expressões informais, tornando-o adequado para uma apostila de estudos. Não omita nenhum conteúdo importante. Responda apenas com o texto reescrito.\n"
            f"Texto:\n{block['content']}"
        )
        try:
            response = await client.chat.completions.create(  # Await the LLM call
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente que reescreve textos para apostilas de estudo."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1200,
                temperature=0.4,
            )
            formal_text = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] Error formalizing block: {e}")
            formal_text = block['content'] # Fallback to original content on error
        return {'content': formal_text}

    # 1.5. Formalize each block using LLM (ChatGPT) in parallel
    formalized_blocks = await asyncio.gather(*[formalize_block_async(block) for block in blocks])

    # 2. For each block, generate a title (ChatGPT) and a quiz (in parallel)
    async def get_title_and_quiz_for_block(block):
        # Prompt for title generation (ultra simple and explicit)
        prompt = (
            "Dê um título didático e objetivo para o texto abaixo. "
            "Responda SOMENTE com o título, sem explicações, sem pontuação extra, sem aspas.\n"
            f"Texto:\n{block['content']}"
        )
        try:
            response = await client.chat.completions.create( # Await the LLM call
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente que sugere títulos didáticos para blocos de texto."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=30,
                temperature=0.3,
            )
            title = response.choices[0].message.content.strip().replace('"', '').replace("'", "")
        except Exception as e:
            print("Error generating title:", e)
            title = "Tópico"
        # Prepare request for /generate_questions endpoint
        quiz_req = {
            "text": block['content'],
            "num_questions": data.num_questions
        }
        # Call the generate_questions function directly instead of making an HTTP request
        question_request = QuestionRequest(**quiz_req)
        quiz = await generate_questions(question_request, user)
        return {
            "title": title,
            "content": block['content'],
            "quiz": quiz
        }

    results = await asyncio.gather(*[get_title_and_quiz_for_block(block) for block in formalized_blocks])
    # Log each topic for debugging: title, first 100 chars of content, content length, quiz count
    for idx, topic in enumerate(results):
        print(f"[DEBUG] Topic {idx+1} - Title: {topic['title']}")
        print(f"[DEBUG] Content (start): {topic['content'][:100]}...")
        print(f"[DEBUG] Content length: {len(topic['content'])} chars")
        print(f"[DEBUG] Quiz questions: {len(topic['quiz'])}")
    return results

@router.post("/generate_structured_study_guide_pdf")
async def generate_structured_study_guide_pdf(
    data: GenerateStructuredGuideRequest = Body(...),
    title: str = "Study Guide",
    user=Depends(verify_token)
):
    """
    Endpoint to generate a fully structured study guide PDF:
    - Segments transcript into topics
    - Generates quizzes for each topic
    - Builds the HTML
    - Returns the PDF as a downloadable file
    """
    # 1. Orchestrate the structure (topics + quizzes)
    topics_with_quiz = await generate_structured_study_guide(data, user)
    # 2. Build the HTML
    html_content = build_structured_study_guide_html(topics_with_quiz, title)
    # 3. Generate the PDF
    pdf_io = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_io)
    pdf_io.seek(0)
    # 4. Return the PDF as a downloadable file
    return StreamingResponse(pdf_io, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=study_guide.pdf"
    })

# --- Post-processing function for study guide HTML ---
def postprocess_study_guide_html(html: str) -> str:
    """
    Aggressive post-processing for study guide HTML to ensure strict format:
    - Forces all <ol> to <ol type='a'>.
    - Removes any numbering from <li> (e.g., '1.', '1)', 'a)', 'a.').
    - Removes numbering from question statements (e.g., '1. What...' → 'What...').
    - Extracts Answer Key even if not in a <h3> section, or adds a placeholder if missing.
    - Cleans up any extra code blocks or markdown.
    """
    # Remove markdown code blocks (triple backticks)
    html = re.sub(r"```[a-zA-Z]*", "", html)
    html = html.replace("```", "")

    # Convert all <ol> or <ol ...> to <ol type='a'>
    html = re.sub(r"<ol[^>]*>", "<ol type='a'>", html)

    # Convert <ul> to <ol type='a'> for alternatives (if model used <ul> by mistake)
    html = re.sub(r"<ul>", "<ol type='a'>", html)
    html = re.sub(r"</ul>", "</ol>", html)

    # Remove any stray <code> or <pre> tags
    html = re.sub(r"<code>.*?</code>", "", html, flags=re.DOTALL)
    html = re.sub(r"<pre>.*?</pre>", "", html, flags=re.DOTALL)

    # Remove any markdown-style lists (e.g., '- item', '* item')
    html = re.sub(r"^\s*[-*] ", "", html, flags=re.MULTILINE)

    # Clean up <li> items: remove manual numbering (e.g., '1.', '1)', 'a)', 'a.') at the start
    html = re.sub(r"<li>\s*([a-dA-D0-9][\)\.]\s*)", "<li>", html)
    html = re.sub(r"<li>\s*\d+\.\s*", "<li>", html)  # Remove '1. '
    html = re.sub(r"<li>\s*[a-dA-D][\)\.]\s*", "<li>", html)  # Remove 'a) ', 'a. '

    # Remove nested <ol> inside <ol type='a'> (flatten if needed)
    html = re.sub(r"(<ol type='a'>)\s*(<ol type='a'>)+", r"<ol type='a'>", html)
    html = re.sub(r"</ol>\s*</ol>", "</ol>", html)

    # Remove numbering from question statements (e.g., '1. What...' → 'What...')
    html = re.sub(r"(<p>)\s*\d+\.\s*", r"\1", html)
    html = re.sub(r"(<p>)\s*[a-dA-D][\)\.]\s*", r"\1", html)

    # Try to extract the Answer Key from anywhere in the HTML
    answer_key_lines = re.findall(r"\d+\.\s*[a-dA-D]\)", html)
    answer_key_section = ''
    if answer_key_lines:
        # Remove duplicates and join with newlines
        seen = set()
        clean_lines = []
        for line in answer_key_lines:
            if line not in seen:
                clean_lines.append(line)
                seen.add(line)
        answer_key_section = '<h3>Answer Key</h3>\n' + '\n'.join(clean_lines)
    else:
        answer_key_section = '<h3>Answer Key</h3>\nAnswer Key not found.'

    # Remove any existing Answer Key section (to avoid duplicates)
    html = re.sub(r"<h3>Answer Key</h3>[\s\S]*", "", html)
    # Append the cleaned Answer Key at the end
    html = html.strip() + '\n' + answer_key_section

    # Remove any remaining triple backticks (just in case)
    html = html.replace("```", "")

    return html

def build_structured_study_guide_html(topics_with_quiz: list, title: str = "Study Guide") -> str:
    """
    Builds the final HTML for the study guide PDF.
    - Each topic includes its title (from ChatGPT), content (from spaCy segmentation), and quiz (questions and alternatives).
    - At the end, an Answer Key section lists the correct alternative for each question.
    - IMPORTANT: The content of each topic must be the original block from the transcript, not a summary or explanation.
    """
    html = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; text-align: justify; }}
            h1 {{ text-align: center; font-size: 2.2em; margin-bottom: 0.5em; }}
            h2 {{ color: #2a4d7c; margin-top: 2em; }}
            .section {{ margin-bottom: 2em; text-align: justify; }}
            .quiz-title {{ font-weight: bold; margin-top: 1.5em; margin-bottom: 1em; display: block; }}
            .quiz {{ margin-top: 1em; margin-bottom: 2em; }}
            .quiz ol {{ list-style-type: none; margin-left: 0; padding-left: 0; }}
            .footer {{ text-align: center; font-size: 0.9em; color: #888; margin-top: 3em; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
    """
    answer_key = []
    question_counter = 1
    for topic in topics_with_quiz:
        html += f"<h2>{topic['title']}</h2>"
        # Use the original content from spaCy segmentation, not a summary
        html += f"<div class='section'>{topic['content']}</div>"
        html += f"<span class='quiz-title'>Quiz</span>"
        html += "<div class='quiz'>"
        for q in topic['quiz']:
            # Add question statement
            html += f"<p>{q['enunciado']}</p>"
            # Add alternatives as <ol>
            html += "<ol>"
            for i, alt in enumerate(q['alternativas']):
                letter = chr(ord('a') + i)  # Calculate the letter (a, b, c, ...)
                html += f"<li>{letter}) {alt}</li>"
            html += "</ol>"
            # Register answer key (question number and correct letter)
            correct_letter = chr(ord('a') + q['correta'])
            answer_key.append(f"{question_counter}. {correct_letter})")
            question_counter += 1
        html += "</div>"
    # Add Answer Key section
    html += "<h3>Answer Key</h3>"
    html += "<div>" + "<br>".join(answer_key) + "</div>"
    html += "<div class='footer'>Generated by VideoToNotes.ai</div>"
    html += "</body></html>"
    return html 