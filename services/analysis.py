from services.llm import ask_gemini_json
from utils.text import keep_verified_skills

def analyze_resume(resume: str, job_description: str) -> dict:
    prompt = f"""You are a resume reviewer. Analyze the RESUME against the JOB DESCRIPTION.

RESUME:
{resume}

JOB DESCRIPTION:
{job_description}

First, check the inputs. If the RESUME is not a real resume or CV, or the JOB DESCRIPTION is not a real job posting, return exactly this JSON and nothing else:
{{"error": "Input is not a resume or job description. Please paste the full text."}}

Otherwise, return a JSON object with EXACTLY this structure:
{{
  "resume_summary": "A 2-3 sentence summary of the candidate based ONLY on the resume",
  "job_requirements": ["key skills and requirements taken from the job description"],
  "matching_skills": [
    {{"skill": "skill name", "evidence": "word-for-word quote copied from the resume"}}
  ],
  "missing_areas": ["requirement from the job description with no clear evidence in the resume"],
  "suggestions": [
    {{"original": "original sentence from the resume", "improved": "improved sentence using only info from the resume", "reason": "why the change helps"}}
  ],
  "improved_resume": "Complete revised resume using only information from the original"
}}

CRITICAL RULES:
1. Never invent information, companies, dates, or skills.
2. matching_skills must only include skills that appear in BOTH the job description and the resume. The "evidence" must be copied word-for-word from the resume.
3. For missing_areas, use phrasing like "No clear evidence found in resume". Never say the candidate is unqualified.
4. Suggestions may only modify phrasing or structure, using facts already in the resume.
5. Keep all employers, dates, job titles, and degrees exactly as written.
6. Don't add fake statistics or percentages.
7. Return ONLY the JSON, with no other text.
"""
    result = ask_gemini_json(prompt)
    if "error" in result:
        return result
    return keep_verified_skills(result, resume)