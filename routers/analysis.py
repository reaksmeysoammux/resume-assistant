import asyncio
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from services.analysis import analyze_resume
from services.cover_letter import generate_cover_letter
from pathlib import Path
from utils.files import extract_text

router = APIRouter(prefix="/api", tags=["analysis"])

COVER_LETTER_UPLOAD_TYPES = {".doc", ".docx", ".txt"}


class AnalysisRequest(BaseModel):
    resume: str
    job_description: str


@router.post("/analyze")
async def analyze(request: AnalysisRequest):
    if not request.resume.strip():
        raise HTTPException(status_code=400, detail="Resume cannot be empty")
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    result = await asyncio.to_thread(analyze_resume, request.resume, request.job_description)

    if "error" in result:
        status = 400 if "not a resume" in result["error"] else 500
        raise HTTPException(status_code=status, detail=result["error"])
    return result

class CoverLetterRequest(BaseModel):
    resume: str
    job_description: str


@router.post("/cover-letter")
async def cover_letter(request: CoverLetterRequest):
    if not request.resume.strip():
        raise HTTPException(status_code=400, detail="Resume cannot be empty")
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    result = await asyncio.to_thread(generate_cover_letter, request.resume, request.job_description)

    if "error" in result:
        status = 400 if "not a resume" in result["error"] else 500
        raise HTTPException(status_code=status, detail=result["error"])
    return result


@router.post("/cover-letter/upload")
async def cover_letter_upload(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_details: str = Form(...),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in COVER_LETTER_UPLOAD_TYPES:
        raise HTTPException(status_code=400, detail="Accepted file formats: DOC, DOCX, and TXT")

    if not job_title.strip():
        raise HTTPException(status_code=400, detail="Job title cannot be empty")
    if not job_details.strip():
        raise HTTPException(status_code=400, detail="Job responsibilities and requirements cannot be empty")

    data = await file.read()
    try:
        resume = await asyncio.to_thread(extract_text, file.filename or "", data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(resume.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Could not read enough text from this file. Try a DOCX or TXT file.",
        )

    job_description = (
        f"JOB TITLE: {job_title.strip()}\n\n"
        f"RESPONSIBILITIES AND REQUIREMENTS:\n{job_details.strip()}"
    )

    result = await asyncio.to_thread(generate_cover_letter, resume, job_description)

    if "error" in result:
        status = 400 if "not a resume" in result["error"] else 500
        raise HTTPException(status_code=status, detail=result["error"])
    return result

ANALYZE_UPLOAD_TYPES = {".doc", ".docx", ".pdf", ".txt"}


@router.post("/analyze/upload")
async def analyze_upload(
    file: UploadFile = File(...),
    job_description: str = Form(...),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ANALYZE_UPLOAD_TYPES:
        raise HTTPException(status_code=400, detail="Accepted file formats: DOC, DOCX, PDF, and TXT")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    data = await file.read()
    try:
        resume = await asyncio.to_thread(extract_text, file.filename or "", data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(resume.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Could not read enough text from this file. Try a DOCX or TXT file.",
        )

    result = await asyncio.to_thread(analyze_resume, resume, job_description)

    if "error" in result:
        status = 400 if "not a resume" in result["error"] else 500
        raise HTTPException(status_code=status, detail=result["error"])
    return result