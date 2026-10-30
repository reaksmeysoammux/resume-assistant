from services.llm import ask_gemini_json

BUILD_PROMPT = """You are an expert resume writer. Build a professional resume from the NOTES below.

NOTES:
{NOTES}

RULES:
1. Use only facts written in the NOTES. Never invent employers, schools, dates, numbers, skills, or achievements.
2. Turn each experience note into 2 to 4 short, action-led bullet points. Do not add figures that are not in the notes.
3. Write the summary as 2 or 3 sentences using only facts from the notes.
4. Put a skill in "skills" only if the notes mention it.
5. Leave any field the notes do not give as an empty string or an empty list.
6. Do not use bullet symbols, markdown, or bold text.
7. Return ONLY JSON in this exact structure, with no other text:
{"resume_data": {
  "name": "",
  "contact": {"address": "", "phone": "", "email": ""},
  "summary": "",
  "skills": [""],
  "languages": [""],
  "experience": [{"title": "", "company": "", "location": "", "dates": "", "bullets": [""]}],
  "education": [{"degree": "", "school": "", "location": "", "dates": ""}],
  "certifications": [""]
}}
"""


def build_resume(notes: dict) -> dict:
    """Return {"resume_data": {...}} or {"error": ...}."""
    lines = "\n".join(f"{label}: {text}" for label, text in notes.items() if text.strip())
    result = ask_gemini_json(BUILD_PROMPT.replace("{NOTES}", lines))
    if "error" in result:
        return result
    if "resume_data" in result:
        return result
    if "name" in result or "experience" in result:
        return {"resume_data": result}
    return {"error": "Model did not return resume data"}