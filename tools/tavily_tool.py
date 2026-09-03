import os
import re
import requests
from tavily import TavilyClient

# Job sites to search individually, using Tavily's site: targeting
JOB_SITES = [
    "linkedin.com/jobs",
    "indeed.com",
    "ziprecruiter.com",
    "builtin.com",
    "dice.com",
]

# Patterns that indicate an aggregator/category/search page rather than a single job posting
AGGREGATOR_PATTERNS = [
    r"^\d+\s", r"^best\s", r"jobs? in \w+.*20\d\d", r"^top\s\d",
    r"q-.*-jobs\.html", r"/jobs/category", r"/search\?", r"/q-",
]

# Phrases that indicate the posting page itself says the job is dead/removed
DEAD_PHRASES = [
    "no longer available",
    "job posting has been removed",
    "job id provided may not be valid",
    "position has been filled",
    "this job is no longer accepting applications",
    "job not found",
    "posting has expired",
    "no longer accepting applications",
    "unable to load the page",
]

MAX_POSTING_AGE_DAYS = 45


def _is_individual_posting(title: str, url: str) -> bool:
    t = title.lower()
    u = url.lower()
    for pat in AGGREGATOR_PATTERNS:
        if re.search(pat, t) or re.search(pat, u):
            return False
    return True


def _extract_posting_age_days(text: str):
    """Look for 'Posted X days ago' style phrases. Returns int days, or None if not found."""
    t = text.lower()
    m = re.search(r'posted\s+(\d+)\+?\s*days?\s+ago', t)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)\+?\s*days?\s+ago', t)
    if m:
        return int(m.group(1))
    if re.search(r'posted\s+today|posted\s+just\s+now', t):
        return 0
    if 'posted yesterday' in t:
        return 1
    return None


def _verify_posting_live(url: str, timeout: int = 8):
    """
    Fetch the actual posting URL and check for clear dead/expired signals.
    Returns (status, reason):
      "live"       -> confirmed active, safe to include
      "dead"       -> confirmed dead/expired, exclude
      "unverified" -> could not confirm either way (blocked, JS-rendered, timeout) —
                       kept in results but flagged as not independently verified
    """
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            allow_redirects=True,
        )
    except requests.RequestException as e:
        return "unverified", f"request failed: {e}"

    if resp.status_code in (404, 410):
        return "dead", f"HTTP {resp.status_code}"
    if resp.status_code in (403, 999):
        # Bot-blocked (common on LinkedIn) — inconclusive, not a confirmed dead posting
        return "unverified", f"blocked (HTTP {resp.status_code})"
    if resp.status_code >= 400:
        return "unverified", f"HTTP {resp.status_code}"

    text = resp.text.lower()

    for phrase in DEAD_PHRASES:
        if phrase in text:
            return "dead", f"dead-posting phrase: '{phrase}'"

    age_days = _extract_posting_age_days(text)
    if age_days is not None and age_days > MAX_POSTING_AGE_DAYS:
        return "dead", f"posting is {age_days}+ days old (max {MAX_POSTING_AGE_DAYS})"

    return "live", "ok"


def search_jobs(query: str, max_results: int = 4) -> list:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY is not set.")
        return []

    try:
        tavily = TavilyClient(api_key=api_key)
        response = tavily.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=False
        )

        results = response.get("results", [])
        jobs = []
        for r in results:
            title = r.get("title", "Unknown")
            url = r.get("url", "")
            if not _is_individual_posting(title, url):
                continue

            status, reason = _verify_posting_live(url)
            if status == "dead":
                print(f"Skipping dead/expired posting: {title} ({reason})")
                continue
            if status == "unverified":
                print(f"Could not verify freshness for: {title} ({reason}) — including anyway")

            jobs.append({
                "title": title,
                "url": url,
                "content": r.get("content", "No description")[:600],
                "verified_live": status == "live",
            })
        return jobs
    except Exception as e:
        print(f"Tavily search error for '{query}': {e}")
        return []


def search_jobs_multi_site(role_query: str, location: str = "") -> list:
    all_jobs = []
    for site in JOB_SITES:
        q = f"site:{site} {role_query} {location}".strip()
        all_jobs.extend(search_jobs(q, max_results=3))
    return all_jobs
