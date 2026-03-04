"""
RAG (Retrieval-Augmented Generation) pipeline.

Orchestration flow:
  1. Search Google via Serper for real-time context
  2. Compose context string from top snippets
  3. Feed context + student question into Groq LLM
  4. Return structured response with lesson + sources
"""

from __future__ import annotations

import logging

from app.services import serper_service, groq_service

logger = logging.getLogger(__name__)


async def generate_lesson(
    question: str,
    target_language: str = "en",
) -> dict:
    """
    Full RAG pipeline: Search → Context → Generate → Return.

    Returns:
        {
            "topic":    str,   # cleaned question as topic
            "content":  str,   # Markdown lesson
            "language": str,   # language code used
            "sources":  [str], # source URLs from search
        }
    """
    # ── Step 1: Retrieve real-time context via Serper ──
    try:
        search_results = await serper_service.search(
            query=question,
            language_code=target_language,
            num_results=5,
        )
        snippets = search_results["snippets"]
        source_urls = search_results["urls"]
        context = "\n\n".join(snippets) if snippets else None
    except Exception as exc:
        logger.warning("Serper search failed, proceeding without context: %s", exc)
        context = None
        source_urls = []

    # ── Step 2: Generate lesson via Groq + context ──
    content = await groq_service.generate(
        question=question,
        language_code=target_language,
        context=context,
    )

    # ── Step 3: Structure the response ──
    topic = question.strip().rstrip("?").title()

    return {
        "topic": topic,
        "content": content,
        "language": target_language,
        "sources": source_urls,
    }
