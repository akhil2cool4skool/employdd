# Employdd

Paste a job description, get a tailored 1-page PDF resume in seconds.

## Local development

```bash
pip install -r requirements.txt
playwright install chromium
export OPENAI_API_KEY=sk-...
python app.py
```

Open http://localhost:5000

## Deploy to Railway

1. Push this repo to GitHub
2. Go to railway.app → New Project → Deploy from GitHub repo
3. Select this repo
4. Go to Variables → add `OPENAI_API_KEY` = your OpenAI key
5. Railway auto-deploys on every push

## How it works

1. You paste a job description
2. GPT-4o mini reads your background + the job description and writes tailored resume content as JSON
3. Playwright renders it as HTML and generates a verified 1-page PDF
4. PDF downloads automatically — no formatting needed
