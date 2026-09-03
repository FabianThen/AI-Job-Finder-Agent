# AI Software Engineering Job Finder Agent

An autonomous AI agent I built to support my own job search. It searches multiple job sites for Software Engineer and Full-Stack Developer postings, filters out aggregator/category pages, scores each real posting against my resume for skill fit and salary, and emails me a daily report each morning, so I don't have to manually check multiple job boards.

## What it does

Every run, the agent:

1. Searches LinkedIn, Indeed, ZipRecruiter, Built In, and Dice for target roles (Full-Stack Software Engineer remote, Software Engineer Connecticut hybrid/on-site)
2. Filters out job board search, category, and listing pages, keeping only individual postings for a specific role at a specific company
3. Uses an LLM (via Groq) to extract structured details (company, location, experience, salary) and evaluate fit against my resume: skill match score, location match (Remote or Connecticut), and whether the role meets a $70k+ salary floor
4. Filters out jobs that don't meet the location, salary, or skill-fit criteria
5. Filters out any jobs already sent in a previous run, using a local JSON memory file
6. Formats a clean report of the qualifying postings and emails it via SMTP
7. Can run once on demand or continuously on a daily schedule (6:00 AM) using APScheduler

## Architecture

- `main.py` — orchestrates the workflow: search → filter → evaluate fit → dedupe → report → send → save
- `resume_profile.txt` — candidate profile (skills, experience, target role/location/salary) used to score job fit; not committed to version control
- `tools/tavily_tool.py` — searches each configured job site individually via the Tavily search API, filtering out aggregator/category pages
- `tools/memory.py` — tracks which job URLs have already been sent, so the daily report only includes new postings
- `tools/email_tool.py` — builds and sends the report via SMTP
- `tools/scheduler.py` — runs the workflow automatically every day using APScheduler

## Tech stack

Python, OpenAI SDK (via Groq's OpenAI-compatible API), Tavily Search API, APScheduler, smtplib, python-dotenv

## Setup

1. Install dependencies with `uv sync`
2. Copy `.env.example` to `.env` and fill in your own API keys and email credentials:
   - `GROQ_API_KEY` — from console.groq.com
   - `TAVILY_API_KEY` — from tavily.com
   - `EMAIL_USER`, `EMAIL_PASSWORD` (Gmail requires an App Password, not your regular password), `RECIPIENT_EMAIL`
   - `SMTP_SERVER`, `SMTP_PORT`
3. Create a `resume_profile.txt` with your own background, skills, and target role/location/salary
4. Run once on demand:

   uv run python -c "from main import run_workflow; run_workflow()"

5. Or run continuously on the daily schedule:

   uv run python main.py

## Notes

I built this while actively job searching, to save time and stay on top of new postings without manually checking multiple job boards every day. The first version searched generic queries and often returned job board category pages instead of real postings. I upgraded it to search specific job sites individually, filter out non-posting pages, and use an LLM to score each real posting against my actual resume for skill fit, location, and salary, so the daily report only contains roles genuinely worth applying to. It runs automatically every morning and emails me a fresh, filtered report.
