import os
import re
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


def _is_individual_posting(title: str, url: str) -> bool:
    t = title.lower()
    u = url.lower()
    for pat in AGGREGATOR_PATTERNS:
        if re.search(pat, t) or re.search(pat, u):
            return False
    return True


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
            jobs.append({
                "title": title,
                "url": url,
                "content": r.get("content", "No description")[:600]
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
