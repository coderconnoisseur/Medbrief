from fastapi import APIRouter, UploadFile, File
from app.nlp.ner import extract_entities
from app.nlp.summarizer import summarize_note

router = APIRouter()

@router.post("/summarize")
async def summarize(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")

    entities = extract_entities(text)
    summary = summarize_note(text)

    return {
        "summary": summary,
        "structured": entities
    }
