# app/routes/routes.py
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi import APIRouter, UploadFile, File, Body
from httpcore import request
from app.nlp.summarizer import summarize_note
from app.nlp.ner import extract_entities  
from app.diagnosis_api import suggest_diagnosis
import re

router = APIRouter()
from pydantic import BaseModel

class DiagnosisRequest(BaseModel):
    symptoms: str
    conditions:str
    medications:str

Templates = Jinja2Templates(directory="app/Static")

def clean_form_data(raw_text: str) -> str:
    """
    Clean form data by removing boundaries, headers, and extracting actual clinical content
    """
    # Remove form boundaries and headers
    lines = raw_text.split('\n')
    cleaned_lines = []
    skip_line = False
    
    for line in lines:
        # Skip boundary lines
        if line.startswith('------gecko') or line.startswith('Content-Disposition') or line.startswith('Content-Type'):
            skip_line = True
            continue
        # Skip empty lines after headers
        elif skip_line and line.strip() == '':
            skip_line = False
            continue
        # Add actual content lines
        elif not skip_line and line.strip():
            cleaned_lines.append(line.strip())
    
    return '\n'.join(cleaned_lines)


@router.get("/")
@router.get("/index")
def index(request: Request):
    return Templates.TemplateResponse("index.html", {"request": request})


@router.post("/summarize")
async def summarize_endpoint(request: Request, text: str = Body(...)):
    print(f"Raw received text: {text[:200]}...")  # Debug print
    
    # Clean the form data to extract actual clinical content
    cleaned_text = clean_form_data(text)
    print(f"Cleaned text: {cleaned_text[:200]}...")  # Debug print
    
    summary = summarize_note(cleaned_text)
    structured = extract_entities(cleaned_text)
    print(f"Extracted entities: {structured}")  # Debug print
    
    history = ', '.join(structured['past_medical_history']) if structured['past_medical_history'] else "No past medical history found"
    
    # Format vitals properly - they are dictionaries with type, value, text
    if structured['vitals_with_values']:
        vitals_formatted = []
        for vital in structured['vitals_with_values']:
            if vital['type'] == 'blood_pressure':
                vitals_formatted.append(f"BP: {vital['systolic']}/{vital['diastolic']}")
            else:
                vitals_formatted.append(f"{vital['type'].replace('_', ' ').title()}: {vital['value']}")
        vitals = ', '.join(vitals_formatted)
    else:
        vitals = "No vitals found"
    
    # Format medications and symptoms for diagnosis API
    medications_str = ', '.join(structured['medications']) if structured['medications'] else "No medications"
    symptoms_str = ', '.join(structured['symptoms']) if structured['symptoms'] else "No symptoms"
    conditions_str = ', '.join(structured['past_medical_history']) if structured['past_medical_history'] else "No conditions"
    
    # Get AI diagnosis
    diagnosis_response = suggest_diagnosis(symptoms_str, conditions_str, medications_str)
    from app.diagnosis_api import parse_diagnosis_response
    parsed_diagnosis = parse_diagnosis_response(diagnosis_response)
    
    print(f"Formatted vitals: {vitals}")  # Debug print
    print(f"History: {history}")  # Debug print
    print(f"Diagnosis: {parsed_diagnosis}")  # Debug print
    
    return Templates.TemplateResponse("result.html", {
        "request": request,
        "text": cleaned_text,  # Use cleaned text for display
        "history": history,
        "summary": summary,
        'vitals': vitals,
        "structured": structured,
        "diagnosis": parsed_diagnosis
    })
    
    
@router.get("/upload")
async def upload_endpoint(request: Request):
    return Templates.TemplateResponse("upload.html", {"request": request})


from fastapi import Form

@router.post("/upload")
async def upload_endpoint(
    request: Request,
    clinical_file: UploadFile = File(None),
    clinical_text: str = Form(None)
):
    file_content = ""
    if clinical_file and clinical_file.filename:
        file_bytes = await clinical_file.read()
        file_content = file_bytes.decode("utf-8").strip()
    text_content = clinical_text.strip() if clinical_text else ""
    content = file_content or text_content
    if not content:
        return Templates.TemplateResponse(
            "upload.html",
            {"request": request, "error": "Please paste text or upload a file to analyze."}
        )
    # Directly POST to /summarize with the content
    from starlette.requests import Request as StarletteRequest
    from fastapi import status
    from fastapi.responses import HTMLResponse
    # Call summarize_endpoint directly
    # Create a fake request body for summarize_endpoint
    class FakeBody:
        def __init__(self, text):
            self.text = text
    # Use FastAPI's dependency injection to call summarize_endpoint
    return await summarize_endpoint(request, text=content)

# New endpoint for diagnosis suggestion
@router.post("/diagnose")
async def diagnose_endpoint(request: DiagnosisRequest):
    diagnosis = suggest_diagnosis(request.symptoms,request.conditions,request.medications)
    return {"diagnosis": diagnosis}
