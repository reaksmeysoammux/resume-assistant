import json
from config import client, GEMINI_MODEL
import time

def ask_gemini_json(prompt: str) -> dict:
    """Send a prompt to Gemini and return a parsed JSON object, or {"error": ...}."""
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        text = (response.text or "").strip()
    except Exception as e:
        return {"error": f"Gemini API error: {e}"}

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}") + 1
        if start == -1 or end <= start:
            return {"error": "Failed to parse JSON from model response", "raw_response": text[:500]}
        try:
            parsed = json.loads(text[start:end])
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON from model response", "raw_response": text[:500]}

    if not isinstance(parsed, dict):
        return {"error": "Unexpected response format from model"}
    return parsed


def call_with_retry(fn, retries=3, base_delay=2):
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            msg = str(e)
            transient = "503" in msg or "UNAVAILABLE"in msg or "429" in msg
            if not transient or attempt == retries - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))