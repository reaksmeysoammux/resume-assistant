from io import BytesIO
from datetime import datetime
from html import escape

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
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


def _s(value) -> str:
    return "" if value is None else str(value)


def generate_txt_export(analysis_results: dict) -> str:
    out = "=" * 80 + "\n"
    out += "RESUME ANALYSIS REPORT\n"
    out += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    out += "=" * 80 + "\n\n"

    if analysis_results.get("resume_summary"):
        out += "RESUME SUMMARY\n" + "-" * 40 + "\n"
        out += _s(analysis_results["resume_summary"]) + "\n\n"

    if analysis_results.get("job_requirements"):
        out += "JOB REQUIREMENTS\n" + "-" * 40 + "\n"
        for req in analysis_results["job_requirements"]:
            out += f"- {_s(req)}\n"
        out += "\n"

    if analysis_results.get("matching_skills"):
        out += "MATCHING SKILLS\n" + "-" * 40 + "\n"
        for skill in analysis_results["matching_skills"]:
            if isinstance(skill, dict):
                out += f"[+] {_s(skill.get('skill'))}\n"
                out += f"    Evidence: \"{_s(skill.get('evidence'))}\"\n\n"
            else:
                out += f"[+] {_s(skill)}\n\n"

    if analysis_results.get("missing_areas"):
        out += "MISSING OR WEAK AREAS\n" + "-" * 40 + "\n"
        for area in analysis_results["missing_areas"]:
            out += f"[!] {_s(area)}\n"
        out += "\n"

    if analysis_results.get("suggestions"):
        out += "IMPROVEMENT SUGGESTIONS\n" + "-" * 40 + "\n"
        for i, sugg in enumerate(analysis_results["suggestions"], 1):
            if isinstance(sugg, dict):
                out += f"\n{i}. Original:\n   \"{_s(sugg.get('original'))}\"\n"
                out += f"\n   Improved:\n   \"{_s(sugg.get('improved'))}\"\n"
                out += f"\n   Why: {_s(sugg.get('reason'))}\n"
            else:
                out += f"\n{i}. {_s(sugg)}\n"

    if analysis_results.get("improved_resume"):
        out += "\n" + "=" * 80 + "\n"
        out += "IMPROVED RESUME\n"
        out += "=" * 80 + "\n\n"
        out += _s(analysis_results["improved_resume"])

    return out


def generate_pdf_export(analysis_results: dict) -> bytes:
    if not PDF_AVAILABLE:
        raise ValueError("PDF export not available. Install reportlab: pip install reportlab")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Heading1"], fontSize=24,
        textColor=HexColor("#667eea"), spaceAfter=12, alignment=1,
    )
    story.append(Paragraph("Resume Analysis Report", title_style))
    story.append(Spacer(1, 0.2 * inch))

    if analysis_results.get("resume_summary"):
        story.append(Paragraph("Resume Summary", styles["Heading2"]))
        story.append(Paragraph(escape(_s(analysis_results["resume_summary"])), styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

    if analysis_results.get("job_requirements"):
        story.append(Paragraph("Job Requirements", styles["Heading2"]))
        for req in analysis_results["job_requirements"]:
            story.append(Paragraph(f"&bull; {escape(_s(req))}", styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

    if analysis_results.get("matching_skills"):
        story.append(Paragraph("Matching Skills [Match]", styles["Heading2"]))
        for skill in analysis_results["matching_skills"]:
            if isinstance(skill, dict):
                story.append(Paragraph(f"<b>{escape(_s(skill.get('skill')))}</b>", styles["Normal"]))
                evidence = _s(skill.get("evidence"))
                if evidence:
                    story.append(Paragraph(f"<i>Evidence: \"{escape(evidence)}\"</i>", styles["Normal"]))
            else:
                story.append(Paragraph(f"<b>{escape(_s(skill))}</b>", styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))
        story.append(Spacer(1, 0.1 * inch))

    if analysis_results.get("missing_areas"):
        story.append(Paragraph("Missing or Weak Areas", styles["Heading2"]))
        for area in analysis_results["missing_areas"]:
            story.append(Paragraph(f"[!] {escape(_s(area))}", styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

    if analysis_results.get("suggestions"):
        story.append(PageBreak())
        story.append(Paragraph("Improvement Suggestions", styles["Heading2"]))
        for i, sugg in enumerate(analysis_results["suggestions"], 1):
            story.append(Paragraph(f"<b>Suggestion {i}</b>", styles["Heading3"]))
            if isinstance(sugg, dict):
                story.append(Paragraph(f"<b>Original:</b> {escape(_s(sugg.get('original')))}", styles["Normal"]))
                story.append(Paragraph(f"<b>Improved:</b> {escape(_s(sugg.get('improved')))}", styles["Normal"]))
                story.append(Paragraph(f"<b>Why:</b> {escape(_s(sugg.get('reason')))}", styles["Normal"]))
            else:
                story.append(Paragraph(escape(_s(sugg)), styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

    if analysis_results.get("improved_resume"):
        story.append(PageBreak())
        story.append(Paragraph("Improved Resume", styles["Heading1"]))
        story.append(Spacer(1, 0.2 * inch))
        improved_text = escape(_s(analysis_results["improved_resume"])).replace("\n", "<br/>")
        story.append(Paragraph(improved_text, styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_docx_export(analysis_results: dict) -> bytes:
    if not DOCX_AVAILABLE:
        raise ValueError("DOCX export not available. Install python-docx: pip install python-docx")

    doc = Document()
    title = doc.add_heading("Resume Analysis Report", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if analysis_results.get("resume_summary"):
        doc.add_heading("Resume Summary", level=1)
        doc.add_paragraph(_s(analysis_results["resume_summary"]))

    if analysis_results.get("job_requirements"):
        doc.add_heading("Job Requirements", level=1)
        for req in analysis_results["job_requirements"]:
            doc.add_paragraph(_s(req), style="List Bullet")

    if analysis_results.get("matching_skills"):
        doc.add_heading("Matching Skills [Match]", level=1)
        for skill in analysis_results["matching_skills"]:
            p = doc.add_paragraph()
            if isinstance(skill, dict):
                p.add_run(_s(skill.get("skill"))).bold = True
                evidence = _s(skill.get("evidence"))
                if evidence:
                    doc.add_paragraph(f"Evidence: \"{evidence}\"", style="List Bullet 2")
            else:
                p.add_run(_s(skill)).bold = True

    if analysis_results.get("missing_areas"):
        doc.add_heading("Missing or Weak Areas", level=1)
        for area in analysis_results["missing_areas"]:
            doc.add_paragraph(f"[!] {_s(area)}", style="List Bullet")

    if analysis_results.get("suggestions"):
        doc.add_page_break()
        doc.add_heading("Improvement Suggestions", level=1)
        for i, sugg in enumerate(analysis_results["suggestions"], 1):
            doc.add_heading(f"Suggestion {i}", level=2)
            if isinstance(sugg, dict):
                for label, key in (("Original: ", "original"), ("Improved: ", "improved"), ("Why: ", "reason")):
                    p = doc.add_paragraph()
                    p.add_run(label).bold = True
                    p.add_run(_s(sugg.get(key)))
            else:
                doc.add_paragraph(_s(sugg))

    if analysis_results.get("improved_resume"):
        doc.add_page_break()
        doc.add_heading("Improved Resume", level=1)
        doc.add_paragraph(_s(analysis_results["improved_resume"]))

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()