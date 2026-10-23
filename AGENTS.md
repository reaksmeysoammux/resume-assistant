# AGENTS.md

## Project

Single-file FastAPI backend (`main.py`) + static vanilla-JS frontend (`index.html`). No packages, no tests, no lint/CI config. All backend logic lives in `main.py`; the frontend hardcodes `API_URL = 'http://localhost:8000'` (index.html:419).

## Run

Two processes are required (dev is Windows; `venv/` exists at repo root):

```bash
# Terminal 1 — backend on port 8000
venv\Scripts\activate
python main.py

# Terminal 2 — frontend on port 3000
python -m http.server 3000
```

Open http://localhost:3000. Backend alone: http://localhost:8000/ lists endpoints.

## Environment

- `.env` is loaded from the repo root at import time (`load_dotenv` in main.py:16-17).
- `GEMINI_API_KEY` is **mandatory**: `main.py` raises `ValueError` at module import if missing, so the server won't start at all without it — even for work unrelated to Gemini.
- Gotcha: the current local `.env` uses PowerShell syntax (`$env:GEMINI_API_KEY = ...`), which python-dotenv parses as a key literally named `$env:GEMINI_API_KEY`. Result: `GEMINI_API_KEY` stays unset and `import main` fails. Use plain `GEMINI_API_KEY=...` in `.env`, or set the variable in the shell.
- `USE_MOCK_MODE=true` is read and reported by `/` and `/api/health`, but `analyze_resume()` never checks it — it always calls the real Gemini API. Don't rely on mock mode; don't assume setting the flag avoids API calls.

## Conventions & gotchas

- Exports (`reportlab`, `python-docx`) are optional: imported in try/except with `PDF_AVAILABLE` / `DOCX_AVAILABLE` flags; endpoints return 400 if missing. Keep that pattern when touching imports.
- Gemini calls and PDF/DOCX generation run in a shared `ThreadPoolExecutor` via `run_in_executor` — preserve this so blocking work doesn't stall the event loop.
- The Gemini prompt lives inline in `analyze_resume()` and instructs the model to return strict JSON; response parsing falls back to extracting the first `{...}` block. If you change the prompt's JSON shape, update `generate_txt_export`, `generate_pdf_export`, `generate_docx_export`, and the frontend rendering together — the shape (`resume_summary`, `job_requirements`, `matching_skills`, `missing_areas`, `suggestions`, `improved_resume`) is duplicated across all of them.
- Known latent bugs in `main.py` (fix rather than copy): `respone_mine_type` typo in generation config (line 301) and `json.JSOBNDecodeError` typo (line 314, should be `JSONDecodeError`).
- README.md's setup is slightly stale: `reportlab` and `python-docx` are already in `requirements.txt` (no separate pip install needed), and its code fences are corrupted by stray backslashes — trust `requirements.txt` and this file over the README.

## Verification

No test suite or linters exist. Sanity-check backend changes with `python -c "import main"` (fails fast on missing key/imports) and by hitting `GET /api/health` on a running server. A `FutureWarning` about deprecated `google-generativeai` on import is expected noise.
