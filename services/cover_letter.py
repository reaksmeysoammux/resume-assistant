from datetime import datetime
from services.llm import ask_gemini_json

COVER_LETTER_PROMPT = """You are an expert career writer. Write a cover letter for the candidate below, following the structure and rules exactly.

RESUME:
{RESUME}

JOB DESCRIPTION:
{JOB_DESCRIPTION}

First, check the inputs. If the RESUME is not a real resume, return exactly this JSON and nothing else:
{"error": "Input is not a resume. Please paste the full resume text."}

Otherwise, return JSON with EXACTLY this structure:
{
  "header": {"name": "candidate full name", "email": "", "phone": "", "address": ""},
  "salutation": "Dear [Title or name from the job description],",
  "paragraphs": ["paragraph 1", "paragraph 2", "paragraph 3", "paragraph 4 (optional)"],
  "closing": "Best,",
  "signature": "candidate full name"
}

STRUCTURE (3 or 4 paragraphs, under 350 words in total):
1. Introduction: say why you are writing and why you are interested in this position and/or organization, using the organization's name from the job description. If the sources name a referral, mention that person in the first sentence.
2. Qualifications (paragraphs 2 and 3): connect 2 or 3 specific experiences from the resume (academic, work, volunteer, or activities) to the job requirements. Include numbers and results only when the resume states them. Reuse key words from the job description. Focus on key ideas instead of repeating resume lines word for word.
3. Final paragraph: restate your interest and main qualification, and thank the reader for their time and consideration. Mention the company's mission or values only if the job description states them.

RULES:
1. Use only facts explicitly stated in the RESUME and JOB DESCRIPTION. Never invent employers, dates, degrees, numbers, skills, or achievements. Never claim a skill the resume does not show.
2. If no person's name is given, use a title in the salutation, such as "Dear Hiring Manager," or "Dear Internship Coordinator,". Never use "To Whom It May Concern".
3. Avoid starting most sentences with "I". Vary your sentence openings.
4. Avoid clichés such as "outstanding candidate", "team player", or "think outside the box".
5. Use positive, confident, active language. Be concise.
6. Plain text only: no markdown, bullets, or bold.
7. Leave a contact field as an empty string if the resume does not contain it.
8. Return ONLY the JSON, with no other text.
"""


def generate_cover_letter(resume: str, job_description: str) -> dict:
    """Return the letter as structured fields, or {"error": ...}."""
    prompt = (
        COVER_LETTER_PROMPT
        .replace("{RESUME}", resume)
        .replace("{JOB_DESCRIPTION}", job_description)
    )

    result = ask_gemini_json(prompt)
    if "error" in result:
        return result

    paragraphs = [p.strip() for p in result.get("paragraphs", []) if isinstance(p, str) and p.strip()]
    if not 3 <= len(paragraphs) <= 4:
        return {"error": "Model returned an invalid number of cover letter paragraphs"}

    header = result.get("header") or {}
    fields = ("name", "email", "phone", "address")
    clean_header = {k: str(header.get(k) or "").strip() for k in fields}

    return {
        "header": clean_header,
        "date": datetime.now().strftime("%B %d, %Y"),
        "salutation": result.get("salutation") or "Dear Hiring Manager,",
        "paragraphs": paragraphs,
        "closing": result.get("closing") or "Best,",
        "signature": result.get("signature") or clean_header["name"],
    }