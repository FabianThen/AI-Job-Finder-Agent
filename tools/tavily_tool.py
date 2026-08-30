import os
from tavily import TavilyClient


def search_jobs(query: str) -> list:
    """
    Search for the latest job posting based on the given query.
    Returns a list of job dicts with title, url, and content.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY is not set.")
        return []

    try:
        tavily = TavilyClient(api_key=api_key)
        response = tavily.search(
            query=query,
            search_depth="basic",
            max_results=1,
            include_answer=False
        )

        results = response.get("results", [])
        jobs = []
        for r in results:
            jobs.append({
                "title": r.get("title", "Unknown"),
                "url": r.get("url", ""),
                "content": r.get("content", "No description")[:150]
            })
        return jobs
    except Exception as e:
        print(f"Tavily search error for '{query}': {e}")
        return []
