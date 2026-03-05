"""
Groq LLM service.

Wraps the Groq SDK to generate student-friendly, Markdown-formatted
educational content in the requested language.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from groq import Groq, AuthenticationError, APIError

from app.config import get_settings, SUPPORTED_LANGUAGES

log = logging.getLogger(__name__)
settings = get_settings()


@lru_cache
def _get_client() -> Groq:
    """Singleton Groq client (thread-safe, reused across requests)."""
    return Groq(api_key=settings.GROQ_API_KEY)


# ── System prompt template ────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are **Smart Shiksha**, an expert educational tutor built for students in \
rural India. Your mission is to explain academic topics in the simplest, most \
engaging way possible — while being **thorough and comprehensive**.

RULES:
1. **Language**: Write your ENTIRE response in {language_name} ({language_code}).
   If the target language is not English, transliterate technical terms in \
   parentheses so students can look them up.
2. **Format**: Use well-structured **Markdown** with DETAILED content:
   - Start with a clear `## Title`
   - `### Introduction` — brief real-world motivation for the topic
   - `### Key Concepts` — explain each concept with sub-bullets
   - `### Important Formulas` — list ALL relevant formulas using clear notation
     (e.g. `F = m × a`). Explain what each symbol stands for.
   - `### Worked Examples` — at least 2-3 fully solved step-by-step problems \
     showing how to apply the formulas
   - `### Real-World Analogy` — at least one relatable analogy
   - `### Common Mistakes` — pitfalls students usually encounter
   - `### Practice Questions` — 5 practice problems of increasing difficulty. \
     Use a **flat numbered list** (1. 2. 3. 4. 5.) — do NOT indent or nest \
     the items. Put answers in a `<details><summary>Answers</summary>` block \
     using the same flat numbered list format (1. 2. 3. 4. 5.).\
     Close with `</details>`.
   - `### Quick Summary` — 5-7 bullet points covering the essentials
3. **Depth**: Be detailed. Explain *why* things work, not just *what* they are. \
   Show derivations for key formulas when helpful.
4. **Simplicity**: Use vocabulary a 10th-grade student would understand. \
   Avoid jargon unless you immediately explain it.
5. **Accuracy**: If reference context is provided below, base your answer on \
   it to avoid hallucination. Cite facts from the context when possible.
6. **Tone**: Encouraging, patient, friendly — like a caring older sibling.

{context_block}\
"""


def _build_system_prompt(
    language_code: str,
    context: str | None = None,
) -> str:
    """Build the system prompt with language and optional RAG context."""
    language_name = SUPPORTED_LANGUAGES.get(language_code, "English")

    if context:
        context_block = (
            "REFERENCE CONTEXT (use this to ground your answer):\n"
            "```\n" + context + "\n```\n"
        )
    else:
        context_block = ""

    return SYSTEM_PROMPT.format(
        language_name=language_name,
        language_code=language_code,
        context_block=context_block,
    )


async def generate(
    question: str,
    language_code: str = "en",
    context: str | None = None,
) -> str:
    """
    Generate a detailed educational explanation using Groq.

    Runs the synchronous Groq SDK in a thread to keep the event loop free.

    Args:
        question:      The student's question.
        language_code: Target language for the response.
        context:       Optional RAG context from Serper search.

    Returns:
        Markdown-formatted lesson string.
    """
    client = _get_client()
    system_prompt = _build_system_prompt(language_code, context)

    def _call() -> str:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.4,       # factual but not robotic
            max_tokens=4096,
            top_p=0.9,
        )
        return response.choices[0].message.content or ""

    # Run blocking SDK call off the async event loop
    try:
        return await asyncio.to_thread(_call)
    except AuthenticationError:
        log.error("Groq API key is invalid or expired — please update GROQ_API_KEY in .env")
        raise RuntimeError(
            "AI service authentication failed. The GROQ_API_KEY is invalid or expired. "
            "Please update it in the .env file and restart the server."
        )
    except APIError as exc:
        log.error("Groq API error: %s", exc)
        raise RuntimeError(f"AI service error: {exc}")


# Convenience alias used by quiz / competitive routers
async def call_groq(prompt: str, language: str = "en") -> str:
    """Simple wrapper: prompt in → text out."""
    return await generate(question=prompt, language_code=language)
