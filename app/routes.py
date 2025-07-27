# app/routes/routes.py

from fastapi import APIRouter, UploadFile, File, Body
from app.nlp.summarizer import summarize_note
from app.nlp.ner import extract_entities  
from app.diagnosis_api import suggest_diagnosis

router = APIRouter()
from pydantic import BaseModel

class DiagnosisRequest(BaseModel):
    symptoms: str
    conditions:str
    medications:str

@router.post("/summarize")
async def summarize_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")

    summary = summarize_note(text)
    structured = extract_entities(text)

    return {
        "summary": summary,
        "structured": structured
    }


# New endpoint for diagnosis suggestion
@router.post("/diagnose")
async def diagnose_endpoint(request: DiagnosisRequest):
    diagnosis = suggest_diagnosis(request.symptoms,request.conditions,request.medications)
    return {"diagnosis": diagnosis}
