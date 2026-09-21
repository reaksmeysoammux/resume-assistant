# Resume Assistant

AI-powered resume analysis tool that compares your resume against job descriptions.

## Features

- 📝 Resume analysis
- 🎯 Job matching
- 📊 Skill comparison
- 💡 Improvement suggestions
- 📥 Export (TXT, PDF, DOCX)

## Setup

### Requirements
- Python 3.8+
- FastAPI
- Google Generative AI API

### Installation

1. Clone the repository:
\\\ash
git clone https://github.com/reaksmeysoammux/resume-assistant.git
cd resume-assistant
\\\

2. Create virtual environment:
\\\ash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
\\\

3. Install dependencies:
\\\ash
pip install -r requirements.txt
pip install reportlab python-docx
\\\

4. Set API key:
\\\ash
set GEMINI_API_KEY=your_api_key_here  # Windows
export GEMINI_API_KEY=your_api_key_here  # Mac/Linux
\\\

5. Run backend:
\\\ash
python main.py
\\\

6. Run frontend (new terminal):
\\\ash
python -m http.server 3000
\\\

7. Open browser: http://localhost:3000

## Technologies

- FastAPI (Backend)
- Vanilla JavaScript (Frontend)
- Google Generative AI API
- ReportLab (PDF export)
- Python-DOCX (Word export)

## License

MIT
