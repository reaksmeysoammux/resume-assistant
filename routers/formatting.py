import asyncio
from fastapi import APIRouter, File, HTTPException, Response, UploadFile, Form
from pydantic import BaseModel
from services.formatting import format_resume
from services.exporters import RESUME_FONTS, ACCENTS, TEMPLATES, build_resume_file, decode_photo
from utils.files import extract_text
from services.builder import build_resume
from pathlib import Path

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


class BuildRequest(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    address: str = ""
    target_job: str = ""
    profile: str = ""
    education: str = ""
    experience: str = ""
    skills: str = ""
    languages: str = ""
    certifications: str = ""


@router.post("/build")
async def build_endpoint(request: BuildRequest):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    notes = {
        "Target job": request.target_job,
        "About me": request.profile,
        "Education": request.education,
        "Work experience and projects": request.experience,
        "Skills": request.skills,
        "Languages": request.languages,
        "Certifications": request.certifications,
    }
    result = await asyncio.to_thread(build_resume, notes)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # Contact details come from the form, never from the model
    data = result["resume_data"]
    data["name"] = request.name.strip()
    data["contact"] = {
        "address": request.address.strip(),
        "phone": request.phone.strip(),
        "email": request.email.strip(),
    }
    return result


@router.post("/build/with-certificate")
async def build_with_certificate(
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    target_job: str = Form(""),
    profile: str = Form(""),
    education: str = Form(""),
    experience: str = Form(""),
    skills: str = Form(""),
    languages: str = Form(""),
    certifications: str = Form(""),
    certificate_pdf: UploadFile | None = File(None),
):
    if not name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    cert_text = certifications.strip()
    if certificate_pdf and certificate_pdf.filename:
        if Path(certificate_pdf.filename).suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="Certificate must be a PDF file")
        data = await certificate_pdf.read()
        try:
            pdf_text = await asyncio.to_thread(extract_text, certificate_pdf.filename, data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if not pdf_text.strip():
            raise HTTPException(status_code=400, detail="Could not read text from the PDF. Try typing the certificates instead.")
        cert_text = (cert_text + "\n" + pdf_text.strip()).strip()

    notes = {
        "Target job": target_job,
        "About me": profile,
        "Education": education,
        "Work experience and projects": experience,
        "Skills": skills,
        "Languages": languages,
        "Certifications": cert_text,
    }
    result = await asyncio.to_thread(build_resume, notes)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    data = result["resume_data"]
    data["name"] = name.strip()
    data["contact"] = {"address": address.strip(), "phone": phone.strip(), "email": email.strip()}
    return result