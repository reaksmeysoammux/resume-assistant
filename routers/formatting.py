import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.formatting import format_resume

router = APIRouter(prefix="/api", tags=["formatting"])


class FormatRequest(BaseModel):
    resume: str


@router.post("/format")
async def format_endpoint(request: FormatRequest):
    if not request.resume.strip():
        raise HTTPException(status_code=400, detail="Resume cannot be empty")

    result = await asyncio.to_thread(format_resume, request.resume)

    if "error" in result:
        status = 400 if "not a resume" in result["error"] else 500
        raise HTTPException(status_code=status, detail=result["error"])
    return result