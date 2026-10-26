import asyncio
from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from pydantic import BaseModel
from services.formatting import format_resume
from services.exporters import RESUME_FONTS, ACCENTS, TEMPLATES, build_resume_file, decode_photo
from utils.files import extract_text

router = APIRouter(prefix="/api", tags=["formatting"])


class FormatRequest(BaseModel):
    resume: str


class ExportFormattedRequest(BaseModel):
    resume_data: dict
    font: str = "Arial"
    accent: str = "black"
    photo: str = ""


@router.post("/format")
async def format_endpoint(request: FormatRequest):
    if not request.resume.strip():
        raise HTTPException(status_code=400, detail="Resume cannot be empty")

    result = await asyncio.to_thread(format_resume, request.resume)

    if "error" in result:
        status = 400 if "not a resume" in result["error"] else 500
        raise HTTPException(status_code=status, detail=result["error"])
    return result


@router.post("/format/upload")
async def format_upload(file: UploadFile = File(...)):
    data = await file.read()

    try:
        text = await asyncio.to_thread(extract_text, file.filename or "", data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Could not read enough text from this file. Try another format or a text-based PDF.",
        )

    result = await asyncio.to_thread(format_resume, text)

    if "error" in result:
        status = 400 if "not a resume" in result["error"] else 500
        raise HTTPException(status_code=status, detail=result["error"])
    return result


@router.post("/format/export/{fmt}")
async def export_formatted(fmt: str, request: ExportFormattedRequest):
    font = request.font if request.font in RESUME_FONTS else "Arial"
    accent = ACCENTS.get(request.accent, ACCENTS["black"])
    tpl = request.template if request.template in TEMPLATES else "classic"
    photo = decode_photo(request.photo)
    try:
        data, media, filename = await asyncio.to_thread(
            build_resume_file, fmt, request.resume_data, font, accent, photo, tpl
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )