"""
Serper (Google Search) service.

Sends localized queries to Google via the Serper API and extracts
the most relevant snippets + source URLs for RAG grounding.
"""

from __future__ import annotations

import httpx

from app.config import get_settings, LANGUAGE_TO_SERPER_HL

settings = get_settings()

SERPER_ENDPOINT = "https://google.serper.dev/search"


async def search(
    query: str,
    language_code: str = "en",
    num_results: int = 5,
) -> dict[str, list]:
    """
    Search Google via Serper and return cleaned results.

    Returns:
        {
            "snippets": ["snippet text", ...],
            "urls":     ["https://...", ...],
        }
    """
    headers = {
        "X-API-KEY": settings.SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "gl": "in",                                        # India-localized
        "hl": LANGUAGE_TO_SERPER_HL.get(language_code, "en"),
        "num": num_results,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(SERPER_ENDPOINT, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    organic: list[dict] = data.get("organic", [])

    snippets = [
        item["snippet"]
        for item in organic
        if "snippet" in item
    ]
    urls = [
        item["link"]
        for item in organic
        if "link" in item
    ]

    return {"snippets": snippets, "urls": urls}
