import re

def norm(value) -> str:
    """Normalize text so quotes and dashes from the model still match the resume."""
    s = str(value).lower()
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = re.sub(r"[\u2013\u2014]", "-", s)
    return " ".join(s.split())


def keep_verified_skills(result: dict, resume: str) -> dict:
    """Drop matching skills whose evidence isn't actually in the resume."""
    resume_text = norm(resume)
    verified = []
    for item in result.get("matching_skills", []) or []:
        if isinstance(item, dict):
            evidence = norm(item.get("evidence", ""))
            if evidence and evidence in resume_text:
                verified.append(item)
    result["matching_skills"] = verified
    return result