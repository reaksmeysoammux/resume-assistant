import asyncio
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from services.exporters import (
    PDF_AVAILABLE, DOCX_AVAILABLE,
    generate_txt_export, generate_pdf_export, generate_docx_export,
)

router = APIRouter(prefix="/api/export", tags=["export"])


class ExportRequest(BaseModel):
    analysis_results: dict


@router.post("/txt")
async def export_txt(request: ExportRequest):
    try:
        content = generate_txt_export(request.analysis_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TXT export error: {e}")
    return Response(
        content=content.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="resume_analysis.txt"'},
    )


@router.post("/pdf")
async def export_pdf(request: ExportRequest):
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=400, detail="PDF export not available. Install reportlab.")
    try:
        data = await asyncio.to_thread(generate_pdf_export, request.analysis_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export error: {e}")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="resume_analysis.pdf"'},
    )


@router.post("/docx")
async def export_docx(request: ExportRequest):
    if not DOCX_AVAILABLE:
        raise HTTPException(status_code=400, detail="DOCX export not available. Install python-docx.")
    try:
        data = await asyncio.to_thread(generate_docx_export, request.analysis_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX export error: {e}")
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="resume_analysis.docx"'},
    )