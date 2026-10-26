from services.llm import ask_gemini_json
from fastapi import File, UploadFile
from utils.files import extract_text

FORMAT_PROMPT = """You are an expert resume parser. Parse the RESUME into a clean, structured JSON object.

RESUME:
{RESUME}

First, check the input. If the RESUME is not a real resume or CV, return exactly this JSON and nothing else:
{"error": "Input is not a resume. Please paste the full resume text."}

Otherwise, return JSON with EXACTLY this structure:
{"resume_data": {
  "name": "Candidate's full name",
  "contact": {"address": "", "phone": "", "email": ""},
  "summary": "Professional summary or objective from the resume",
  "skills": ["Skill from the resume"],
  "languages": ["Language, with level if stated"],
  "experience": [
    {"title": "", "company": "", "location": "", "dates": "", "bullets": ["Achievement or responsibility from the resume"]}
  ],
  "education": [
    {"degree": "", "school": "", "location": "", "dates": ""}
  ],
  "certifications": ["Certification from the resume"]
}}

RULES:
1. Only use information explicitly stated in the RESUME. Never invent names, employers, dates, or contact details.
2. Leave a field as an empty string or empty list if the resume does not contain it.
3. Remove markdown symbols such as ** and # from the text.
4. Keep employers, dates, job titles, and degrees exactly as written.
5. Return ONLY the JSON, with no other text.
"""


def format_resume(resume: str) -> dict:
    """Return {"resume_data": {...}} or {"error": ...}."""
    result = ask_gemini_json(FORMAT_PROMPT.replace("{RESUME}", resume))
    if "error" in result:
        return result
    if "resume_data" in result:
        return result
    if "name" in result or "experience" in result:
        return {"resume_data": result}
    return {"error": "Failed to parse structured resume data from model response"}
