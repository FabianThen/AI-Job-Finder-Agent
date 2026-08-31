import os
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI

from tools.tavily_tool import search_jobs
from tools.email_tool import send_email
from tools.memory import is_duplicate, mark_as_sent
from tools.scheduler import start_scheduler

# Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
load_dotenv()

# Groq AI Client
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# ---------- 4 Fixed Categories ----------
CATEGORIES = [
    "Remote Software Engineer Jobs",
    "Remote Full Stack Developer Jobs",
    "Software Engineer Jobs Connecticut Hybrid",
    "Software Engineer Jobs Connecticut On-Site",
]


def ai_extract_details(title: str, content: str) -> dict:
    """Use Groq AI to extract structured job details from raw content."""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract job details from the given text. "
                        "Return ONLY a valid JSON object with these keys: "
                        "company, location, experience, salary. "
                        "If a field is not found, use 'Not specified'. "
                        "Return ONLY the JSON, no other text."
                    )
                },
                {
                    "role": "user",
                    "content": f"Title: {title}\nContent: {content}"
                }
            ]
        )
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else {}
        return parsed
    except Exception as e:
        logger.warning(f"AI extraction failed: {e}")
        return {
            "company": "Not specified",
            "location": "Not specified",
            "experience": "Not specified",
            "salary": "Not specified"
        }


def build_report(jobs: list) -> str:
    """Build a clean, fixed-format report string using Python (not AI)."""
    lines = []
    for idx, job in enumerate(jobs, 1):
        lines.append(f"{idx}.")
        lines.append(f"Job Title: {job['title']}")
        lines.append(f"Company: {job['company']}")
        lines.append(f"Location: {job['location']}")
        lines.append(f"Experience: {job['experience']}")
        lines.append(f"Salary: {job['salary']}")
        lines.append(f"Apply Link: {job['url']}")
        lines.append("")
        lines.append("---------------------------------")
        lines.append("")

    lines.append(f"Total Jobs Found: {len(jobs)}")
    return "\n".join(lines)


def run_workflow():
    """Search 4 categories, AI extracts details, Python formats report, email it."""
    logger.info("Starting daily AI job search...")

    all_jobs = []

    # Step 1 — Search each category (1 result each)
    for category in CATEGORIES:
        logger.info(f"Searching: {category}")
        results = search_jobs(category)
        for job in results:
            if not is_duplicate(job["url"]):
                # Step 2 — AI extracts structured details
                logger.info(f"AI extracting details for: {job['title']}")
                details = ai_extract_details(job["title"], job["content"])

                all_jobs.append({
                    "title": job["title"],
                    "url": job["url"],
                    "company": details.get("company", "Not specified"),
                    "location": details.get("location", "Not specified"),
                    "experience": details.get("experience", "Not specified"),
                    "salary": details.get("salary", "Not specified"),
                })

    if not all_jobs:
        logger.info("No new jobs found today. Skipping email.")
        return

    # Step 3 — Python formats the report (guaranteed clean)
    report = build_report(all_jobs)
    logger.info("Report ready!")

    # Step 4 — Send email
    logger.info("Sending email...")
    success = send_email(report)

    # Step 5 — Save to memory
    if success:
        sent_urls = [job["url"] for job in all_jobs]
        mark_as_sent(sent_urls)
        logger.info(f"Done! {len(all_jobs)} jobs emailed and saved to memory.")
    else:
        logger.error("Email failed. Jobs NOT marked as sent.")


if __name__ == "__main__":
    logger.info("=== AI Job Finder Agent ===")

    # --- PRODUCTION MODE: run daily at 8 AM ---
    start_scheduler(run_workflow)
