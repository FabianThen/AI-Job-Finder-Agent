# AI Software Engineering Job Finder Agent

An autonomous AI agent I built to support my own job search. It searches for the latest software engineering job postings, extracts structured details using an LLM, filters out duplicates, and emails me a daily report each morning so I don't have to manually check multiple job boards.

## What it does

Every run, the agent:

1. Searches multiple job categories: remote Software Engineer and Full-Stack Developer roles, plus Connecticut-based hybrid and on-site Software Engineer roles using the Tavily search API
2. Uses an LLM (via Groq) to extract structured details, company, location, experience level, and salary, from each raw job posting
3. Filters out any jobs that were already sent in a previous run, using a local JSON memory file
4. Formats a clean, deduplicated report and emails it via SMTP
5. Can run once on demand or continuously on a daily schedule (6:00 AM) using APScheduler

## Architecture

- `main.py` — orchestrates the workflow: search → extract → dedupe → report → send → save
- `tools/tavily_tool.py` — wraps the Tavily search API to fetch job postings
- `tools/memory.py` — tracks which job URLs have already been sent, so the daily report only includes new postings
- `tools/email_tool.py` — builds and sends the report via SMTP
- `tools/scheduler.py` — runs the workflow automatically every day using APScheduler
- `prompts/system_prompt.txt` — the agent's operating instructions

## Tech stack

Python, OpenAI SDK (via Groq's OpenAI-compatible API), Tavily Search API, APScheduler, smtplib, python-dotenv

## Setup

1. Install dependencies with `uv sync`
2. Copy `.env.example` to `.env` and fill in your own API keys and email credentials:
   - `GROQ_API_KEY` — from console.groq.com
   - `TAVILY_API_KEY` — from tavily.com
   - `EMAIL_USER`, `EMAIL_PASSWORD` (Gmail requires an App Password, not your regular password), `RECIPIENT_EMAIL`
   - `SMTP_SERVER`, `SMTP_PORT`
3. Run once on demand:

uv run python -c "from main import run_workflow; run_workflow()"

4. Or run continuously on the daily schedule:

uv run python main.py


## Notes

I built this while actively job searching, to save time and stay on top of new postings without manually checking multiple job boards every day. It also served as a hands-on way to explore agentic AI design: using an LLM for structured extraction as one step inside a larger, deterministic pipeline, rather than having the LLM handle the entire task end to end. Formatting and scheduling are handled in plain Python for reliability, while the LLM is used specifically where it adds value: parsing unstructured job listing text into structured fields. It runs automatically every morning and emails me a fresh report.
