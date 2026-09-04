import os
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI

from tools.tavily_tool import search_jobs_multi_site
from tools.email_tool import send_email
from tools.memory import is_duplicate, mark_as_sent
from tools.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

with open("resume_profile.txt") as f:
    RESUME_PROFILE = f.read()

# role, location pairs — searched across all configured job sites
SEARCH_TARGETS = [
    ("Full Stack Software Engineer", "Remote"),
    ("Software Engineer", "Connecticut Hybrid"),
    ("Software Engineer", "Connecticut On-Site"),
]

MIN_SALARY = 70000

import re
SENIORITY_PATTERN = re.compile(r"\b(senior|sr\.?|staff|principal|lead|director|vp|head of)\b", re.IGNORECASE)

def is_senior_title(title: str) -> bool:
    return bool(SENIORITY_PATTERN.search(title))


def ai_evaluate_job(title: str, content: str) -> dict:
    """Use Groq to extract details AND score fit against the candidate profile."""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You evaluate job postings against a candidate profile.\n"
                        f"CANDIDATE PROFILE:\n{RESUME_PROFILE}\n\n"
                        "IMPORTANT: Extract ALL fields ONLY from the job posting text below. NEVER use the "
                        "candidate profile above to fill in job fields (it exists only for fit-scoring). The "
                        "'experience' field must describe what THIS POSTING requires, as literally stated in "
                        "its own text -- if the posting does not state a requirement, use 'Not specified'. Never "
                        "output the candidate's own years of experience for this field.\n"
                        "Given a job posting's title and content, return ONLY a valid JSON object with these keys:\n"
                        "company, location, experience, salary (numeric estimate or 'Not specified'), "
                        "salary_meets_minimum (true/false/null if unknown), "
                        "location_matches (true if Remote OR Connecticut, else false), "
                        "required_years_experience (numeric estimate of MINIMUM years required, or null if not stated), "
                        "experience_mismatch (true if the posting requires meaningfully more years of professional experience than the candidate profile describes, else false), "
                        "skill_match_score (0-10, how well candidate's skills fit this role; if experience_mismatch is true, this score must be capped at 5 regardless of skill keyword overlap), "
                        "is_real_posting (true if this is a specific job posting for one role at one company, "
                        "false if it is a job board search/category/listing page).\n"
                        "Return ONLY the JSON, no other text."
                    )
                },
                {"role": "user", "content": f"Title: {title}\nContent: {content}"}
            ]
        )
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else {}
        return parsed
    except Exception as e:
        logger.warning(f"AI evaluation failed: {e}")
        return {}


def passes_filters(eval_result: dict) -> bool:
    if not eval_result.get("is_real_posting", True):
        return False
    if eval_result.get("location_matches") is False:
        return False
    if eval_result.get("salary_meets_minimum") is False:
        return False
    if eval_result.get("skill_match_score", 10) is not None and eval_result.get("skill_match_score", 10) < 4:
        return False
    return True


def build_report(jobs: list) -> str:
    lines = []
    for idx, job in enumerate(jobs, 1):
        lines.append(f"{idx}.")
        lines.append(f"Job Title: {job['title']}")
        lines.append(f"Company: {job['company']}")
        lines.append(f"Location: {job['location']}")
        lines.append(f"Experience: {job['experience']}")
        lines.append(f"Salary: {job['salary']}")
        lines.append(f"Fit Score: {job.get('skill_match_score', 'N/A')}/10")
        status_tag = "Verified live" if job.get("verified_live") else "Unverified — check before applying"
        lines.append(f"Status: {status_tag}")
        lines.append(f"Apply Link: {job['url']}")
        lines.append("")
        lines.append("---------------------------------")
        lines.append("")
    lines.append(f"Total Jobs Found: {len(jobs)}")
    return "\n".join(lines)


def run_workflow():
    logger.info("Starting daily AI job search...")
    all_jobs = []

    seen_this_run = set()
    for role, location in SEARCH_TARGETS:
        logger.info(f"Searching: {role} — {location}")
        results = search_jobs_multi_site(role, location)
        for job in results:
            from tools.memory import _normalize
            norm_url = _normalize(job["url"])
            if norm_url in seen_this_run or is_duplicate(job["url"]):
                continue
            seen_this_run.add(norm_url)
            if is_senior_title(job["title"]):
                logger.info(f"Skipping senior-level title: {job['title']}")
                continue
            logger.info(f"Evaluating: {job['title']}")
            import time; time.sleep(2)
            evaluation = ai_evaluate_job(job["title"], job["content"])
            if not passes_filters(evaluation):
                logger.info(f"Filtered out: {job['title']}")
                continue
            all_jobs.append({
                "title": job["title"],
                "url": job["url"],
                "company": evaluation.get("company", "Not specified"),
                "location": evaluation.get("location", "Not specified"),
                "experience": evaluation.get("experience", "Not specified"),
                "salary": evaluation.get("salary", "Not specified"),
                "skill_match_score": evaluation.get("skill_match_score", "N/A"),
                "verified_live": job.get("verified_live", False),
            })

    if not all_jobs:
        logger.info("No new matching jobs found today. Skipping email.")
        return

    report = build_report(all_jobs)
    logger.info("Report ready!")
    logger.info("Sending email...")
    success = send_email(report)

    if success:
        sent_urls = [job["url"] for job in all_jobs]
        mark_as_sent(sent_urls)
        logger.info(f"Done! {len(all_jobs)} jobs emailed and saved to memory.")
    else:
        logger.error("Email failed. Jobs NOT marked as sent.")


if __name__ == "__main__":
    logger.info("=== AI Job Finder Agent ===")
    start_scheduler(run_workflow)
