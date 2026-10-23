import asyncio
from fastapi import APIRouter , HTTPException
from pydantic import BaseModel
from services.analysis import analyze_resume
from services.cover_letter import generate_cover_letter

router = APIRouter(prefix="/api", tags=["analysis"])


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