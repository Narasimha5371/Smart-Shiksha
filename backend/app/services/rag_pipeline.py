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


async def generate_lesson_with_file(
    question: str,
    target_language: str = "en",
    image_base64: str | None = None,
    image_mime: str = "image/jpeg",
    file_text: str | None = None,
) -> dict:
    """
    Extended RAG pipeline with optional image or file-text context.

    Flow:
      1. If image provided → analyze with Groq vision model
      2. Combine image description / file text with user question
      3. Run standard RAG pipeline (Serper → context → Groq)
    """
    extra_context_parts: list[str] = []

    # ── Step 1: Analyze uploaded image ──
    if image_base64:
        try:
            description = await groq_service.analyze_image(image_base64, image_mime)
            extra_context_parts.append(
                f"[Image Analysis]\n{description}"
            )
            logger.info("Image analyzed successfully (%d chars)", len(description))
        except Exception as exc:
            logger.warning("Image analysis failed: %s", exc)

    # ── Step 2: Include uploaded file text ──
    if file_text:
        extra_context_parts.append(
            f"[Uploaded Document]\n{file_text}"
        )

    # ── Step 3: Combine into augmented question ──
    augmented_question = question
    if extra_context_parts:
        augmented_question = (
            question + "\n\n---\nContext from uploaded content:\n"
            + "\n\n".join(extra_context_parts)
        )

    # ── Step 4: Standard RAG pipeline ──
    try:
        search_results = await serper_service.search(
            query=question,  # search with original question
            language_code=target_language,
            num_results=5,
        )
        snippets = search_results["snippets"]
        source_urls = search_results["urls"]
        context = "\n\n".join(snippets) if snippets else None
    except Exception as exc:
        logger.warning("Serper search failed: %s", exc)
        context = None
        source_urls = []

    # ── Step 5: Merge extra context with search context ──
    if extra_context_parts:
        extra = "\n\n".join(extra_context_parts)
        context = f"{extra}\n\n{context}" if context else extra

    content = await groq_service.generate(
        question=augmented_question,
        language_code=target_language,
        context=context,
    )

    topic = question.strip().rstrip("?").title()

    return {
        "topic": topic,
        "content": content,
        "language": target_language,
        "sources": source_urls,
    }
