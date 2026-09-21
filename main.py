
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai
import json
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import tempfile
from datetime import datetime

# Try to import export libraries
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

executor = ThreadPoolExecutor(max_workers=4)
app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=api_key)

# MOCK MODE - Set to False to use real Gemini API
USE_MOCK_MODE = True

class AnalysisRequest(BaseModel):
    resume: str
    job_description: str

class ExportRequest(BaseModel):
    analysis_results: dict

# Export Helper Functions

def generate_txt_export(analysis_results: dict) -> str:
    """Generate TXT format of analysis results"""
    txt_content = "=" * 80 + "\n"
    txt_content += "RESUME ANALYSIS REPORT\n"
    txt_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    txt_content += "=" * 80 + "\n\n"
    
    if analysis_results.get('resume_summary'):
        txt_content += "RESUME SUMMARY\n"
        txt_content += "-" * 40 + "\n"
        txt_content += analysis_results['resume_summary'] + "\n\n"
    
    if analysis_results.get('job_requirements'):
        txt_content += "JOB REQUIREMENTS\n"
        txt_content += "-" * 40 + "\n"
        for req in analysis_results['job_requirements']:
            txt_content += f"• {req}\n"
        txt_content += "\n"
    
    if analysis_results.get('matching_skills'):
        txt_content += "MATCHING SKILLS\n"
        txt_content += "-" * 40 + "\n"
        for skill in analysis_results['matching_skills']:
            txt_content += f"✓ {skill['skill']}\n"
            txt_content += f"  Evidence: \"{skill['evidence']}\"\n\n"
    
    if analysis_results.get('missing_areas'):
        txt_content += "MISSING OR WEAK AREAS\n"
        txt_content += "-" * 40 + "\n"
        for area in analysis_results['missing_areas']:
            txt_content += f"⚠ {area}\n"
        txt_content += "\n"
    
    if analysis_results.get('suggestions'):
        txt_content += "IMPROVEMENT SUGGESTIONS\n"
        txt_content += "-" * 40 + "\n"
        for i, sugg in enumerate(analysis_results['suggestions'], 1):
            txt_content += f"\n{i}. Original:\n   \"{sugg['original']}\"\n"
            txt_content += f"\n   Improved:\n   \"{sugg['improved']}\"\n"
            txt_content += f"\n   Why: {sugg['reason']}\n"
    
    if analysis_results.get('improved_resume'):
        txt_content += "\n" + "=" * 80 + "\n"
        txt_content += "IMPROVED RESUME\n"
        txt_content += "=" * 80 + "\n\n"
        txt_content += analysis_results['improved_resume']
    
    return txt_content

def generate_pdf_export(analysis_results: dict) -> bytes:
    """Generate PDF format of analysis results"""
    if not PDF_AVAILABLE:
        raise ValueError("PDF export not available. Install reportlab: pip install reportlab")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#667eea'),
        spaceAfter=12,
        alignment=1  # center
    )
    story.append(Paragraph("Resume Analysis Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Summary
    if analysis_results.get('resume_summary'):
        story.append(Paragraph("Resume Summary", styles['Heading2']))
        story.append(Paragraph(analysis_results['resume_summary'], styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Job Requirements
    if analysis_results.get('job_requirements'):
        story.append(Paragraph("Job Requirements", styles['Heading2']))
        for req in analysis_results['job_requirements']:
            story.append(Paragraph(f"• {req}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Matching Skills
    if analysis_results.get('matching_skills'):
        story.append(Paragraph("Matching Skills ✓", styles['Heading2']))
        for skill in analysis_results['matching_skills']:
            story.append(Paragraph(f"<b>{skill['skill']}</b>", styles['Normal']))
            story.append(Paragraph(f"<i>Evidence: \"{skill['evidence']}\"</i>", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        story.append(Spacer(1, 0.1*inch))
    
    # Missing Areas
    if analysis_results.get('missing_areas'):
        story.append(Paragraph("Missing or Weak Areas", styles['Heading2']))
        for area in analysis_results['missing_areas']:
            story.append(Paragraph(f"⚠ {area}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Suggestions
    if analysis_results.get('suggestions'):
        story.append(PageBreak())
        story.append(Paragraph("Improvement Suggestions", styles['Heading2']))
        for i, sugg in enumerate(analysis_results['suggestions'], 1):
            story.append(Paragraph(f"<b>Suggestion {i}</b>", styles['Heading3']))
            story.append(Paragraph(f"<b>Original:</b> {sugg['original']}", styles['Normal']))
            story.append(Paragraph(f"<b>Improved:</b> {sugg['improved']}", styles['Normal']))
            story.append(Paragraph(f"<b>Why:</b> {sugg['reason']}", styles['Normal']))
            story.append(Spacer(1, 0.15*inch))
    
    # Improved Resume
    if analysis_results.get('improved_resume'):
        story.append(PageBreak())
        story.append(Paragraph("Improved Resume", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        improved_text = analysis_results['improved_resume'].replace('\n', '<br/>')
        story.append(Paragraph(improved_text, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_docx_export(analysis_results: dict) -> bytes:
    """Generate DOCX format of analysis results"""
    if not DOCX_AVAILABLE:
        raise ValueError("DOCX export not available. Install python-docx: pip install python-docx")
    
    doc = Document()
    
    # Title
    title = doc.add_heading('Resume Analysis Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Summary
    if analysis_results.get('resume_summary'):
        doc.add_heading('Resume Summary', level=1)
        doc.add_paragraph(analysis_results['resume_summary'])
    
    # Job Requirements
    if analysis_results.get('job_requirements'):
        doc.add_heading('Job Requirements', level=1)
        for req in analysis_results['job_requirements']:
            doc.add_paragraph(req, style='List Bullet')
    
    # Matching Skills
    if analysis_results.get('matching_skills'):
        doc.add_heading('Matching Skills ✓', level=1)
        for skill in analysis_results['matching_skills']:
            p = doc.add_paragraph()
            p.add_run(f"{skill['skill']}").bold = True
            doc.add_paragraph(f"Evidence: \"{skill['evidence']}\"", style='List Bullet 2')
    
    # Missing Areas
    if analysis_results.get('missing_areas'):
        doc.add_heading('Missing or Weak Areas', level=1)
        for area in analysis_results['missing_areas']:
            doc.add_paragraph(f"⚠ {area}", style='List Bullet')
    
    # Suggestions
    if analysis_results.get('suggestions'):
        doc.add_page_break()
        doc.add_heading('Improvement Suggestions', level=1)
        for i, sugg in enumerate(analysis_results['suggestions'], 1):
            doc.add_heading(f'Suggestion {i}', level=2)
            p = doc.add_paragraph()
            p.add_run('Original: ').bold = True
            p.add_run(sugg['original'])
            
            p = doc.add_paragraph()
            p.add_run('Improved: ').bold = True
            p.add_run(sugg['improved'])
            
            p = doc.add_paragraph()
            p.add_run('Why: ').bold = True
            p.add_run(sugg['reason'])
    
    # Improved Resume
    if analysis_results.get('improved_resume'):
        doc.add_page_break()
        doc.add_heading('Improved Resume', level=1)
        doc.add_paragraph(analysis_results['improved_resume'])
    
    # Save to bytes
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# Resume Analysis Function

def analyze_resume(resume: str, job_description: str) -> dict:
    """Use Google Gemini to analyze resume against job description"""
    
    if USE_MOCK_MODE:
        return {
            "resume_summary": "John Doe is a Senior Software Engineer with 4 years at TechCorp, experienced with FastAPI, REST APIs, and team leadership.",
            "job_requirements": ["Python", "FastAPI", "REST APIs", "PostgreSQL", "Docker", "Leadership"],
            "matching_skills": [
                {"skill": "Python", "evidence": "Built REST APIs using Python and FastAPI"},
                {"skill": "FastAPI", "evidence": "Built REST APIs using Python and FastAPI"},
                {"skill": "Leadership", "evidence": "Led team of 3 developers"}
            ],
            "missing_areas": ["No evidence of PostgreSQL experience mentioned"],
            "suggestions": [{"original": "Improved API response time by 40%", "improved": "Optimized API performance, achieving 40% response time improvement", "reason": "More impactful phrasing"}],
            "improved_resume": "John Doe\nSenior Software Engineer at TechCorp (2020-2024)\n- Developed REST APIs using Python and FastAPI\n- Led and mentored a team of 3 developers\n- Optimized API performance, achieving 40% response time improvement\n\nSkills: Python, FastAPI, PostgreSQL, Docker, JavaScript"
        }
    
    prompt = f"""Analyze this resume against the job description and provide structured feedback.

RESUME:
{resume}

JOB DESCRIPTION:
{job_description}

Provide a JSON response with EXACTLY this structure (no markdown, pure JSON):
{{
  "resume_summary": "A 2-3 sentence summary of the candidate based ONLY on what's in the resume",
  "job_requirements": ["list", "of", "key", "skills", "and", "requirements"],
  "matching_skills": [
    {{
      "skill": "skill name",
      "evidence": "exact sentence or phrase from resume"
    }}
  ],
  "missing_areas": [
    "requirement without clear evidence in resume"
  ],
  "suggestions": [
    {{
      "original": "original sentence from resume",
      "improved": "improved sentence using only info from resume",
      "reason": "explanation of improvement"
    }}
  ],
  "improved_resume": "Complete revised resume using only information from the original"
}}

CRITICAL RULES:
1. Never invent information, companies, dates, or skills
2. For matching_skills, only include items clearly present in the resume
3. For missing_areas, use phrasing like "No clear evidence found in resume" - never say the candidate is unqualified
4. For suggestions, only modify phrasing/structure - use only info already in resume
5. For improved_resume, keep all original facts but improve writing and emphasize job-relevant skills
6. Don't add fake statistics or percentages
7. Never change employer names, dates, job titles, or degrees

Make the JSON parseable and valid. Return ONLY the JSON, no other text."""

    try:
        # Create the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Extract text
        text = response.text
        
        # Parse JSON
        try:
            # Remove markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            # Look for JSON object
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = text[json_start:json_end].strip()
                result = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            return {
                "error": f"Failed to parse JSON: {str(e)}",
                "raw_response": text[:500]
            }
        
        return result
    
    except Exception as e:
        return {
            "error": f"Gemini API error: {str(e)}",
            "details": str(e)
        }

# API Endpoints

@app.get("/")
def read_root():
    return {
        "message": "Resume Assistant API is running",
        "endpoints": {
            "analyze": "POST /api/analyze",
            "health": "GET /api/health",
            "export": {
                "txt": "POST /api/export/txt",
                "pdf": "POST /api/export/pdf",
                "docx": "POST /api/export/docx"
            }
        },
        "mode": "MOCK" if USE_MOCK_MODE else "REAL"
    }

@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    """Analyze resume against job description"""
    
    if not request.resume.strip():
        raise HTTPException(status_code=400, detail="Resume cannot be empty")
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")
    
    try:
        # Run analysis in thread pool
        result = await asyncio.get_event_loop().run_in_executor(
            executor, 
            analyze_resume, 
            request.resume, 
            request.job_description
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/txt")
async def export_txt(request: ExportRequest):
    """Export analysis results as TXT file"""
    try:
        txt_content = generate_txt_export(request.analysis_results)
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(txt_content)
            temp_path = f.name
        
        return FileResponse(
            temp_path,
            media_type="text/plain",
            filename="resume_analysis.txt"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TXT export error: {str(e)}")

@app.post("/api/export/pdf")
async def export_pdf(request: ExportRequest):
    """Export analysis results as PDF file"""
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=400, detail="PDF export not available. Install reportlab: pip install reportlab")
    
    try:
        pdf_bytes = await asyncio.get_event_loop().run_in_executor(
            executor,
            generate_pdf_export,
            request.analysis_results
        )
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(pdf_bytes)
            temp_path = f.name
        
        return FileResponse(
            temp_path,
            media_type="application/pdf",
            filename="resume_analysis.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export error: {str(e)}")

@app.post("/api/export/docx")
async def export_docx(request: ExportRequest):
    """Export analysis results as DOCX file"""
    if not DOCX_AVAILABLE:
        raise HTTPException(status_code=400, detail="DOCX export not available. Install python-docx: pip install python-docx")
    
    try:
        docx_bytes = await asyncio.get_event_loop().run_in_executor(
            executor,
            generate_docx_export,
            request.analysis_results
        )
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            f.write(docx_bytes)
            temp_path = f.name
        
        return FileResponse(
            temp_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="resume_analysis.docx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX export error: {str(e)}")

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "provider": "Google Gemini",
        "mode": "MOCK" if USE_MOCK_MODE else "REAL",
        "exports": {
            "txt": True,
            "pdf": PDF_AVAILABLE,
            "docx": DOCX_AVAILABLE
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Resume Assistant Backend with Google Gemini...")
    print(f"Mode: {'MOCK (testing mode)' if USE_MOCK_MODE else 'REAL (using Gemini API)'}")
    print("Make sure GEMINI_API_KEY environment variable is set")
    print("Server running at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)