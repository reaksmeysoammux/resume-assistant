from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from config import  STATIC_DIR, GEMINI_MODEL
from routers import analysis, formatting, export
from services.exporters import PDF_AVAILABLE, DOCX_AVAILABLE

app = FastAPI(title="Resume Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router)
app.include_router(formatting.router)
app.include_router(export.router)


@app.get("/")
def index_page():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/formatresume.html")
def format_page():
    return FileResponse(STATIC_DIR / "formatresume.html")


@app.get("/api")
def api_info():
    return {
        "message": "Resume Assistant API is running",
        "endpoints": {
            "analyze": "POST /api/analyze",
            "format": "POST /api/format",
            "health": "GET /api/health",
            "export": {
                "txt": "POST /api/export/txt",
                "pdf": "POST /api/export/pdf",
                "docx": "POST /api/export/docx",
            },
        },
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "provider": "Google Gemini",
        "model": GEMINI_MODEL,
        "exports": {"txt": True, "pdf": PDF_AVAILABLE, "docx": DOCX_AVAILABLE},
    }


@app.get("/coverletter.html")
def cover_letter_page():
    return FileResponse(STATIC_DIR / "coverletter.html")


@app.get("/buildresume.html")
def build_page():
    return FileResponse(STATIC_DIR / "buildresume.html")


if __name__ == "__main__":
    import uvicorn
    print(f"Starting Resume Assistant on http://localhost:8000 (model: {GEMINI_MODEL})")
    uvicorn.run(app, host="127.0.0.1", port=8000)