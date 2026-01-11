"""
Gemini embedding wrapper for generating job description embeddings.
"""

import os
from typing import Any

from google import genai
from google.genai import types

# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMENSION = 768

# Global client instance
_client: genai.Client | None = None


def configure_gemini() -> None:
    """Configure Gemini API with the API key from environment."""
    global _client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    _client = genai.Client(api_key=api_key)


async def generate_embedding(text: str) -> list[float]:
    """
    Generate a 768-dimensional embedding for the given text.

    Uses Gemini's text-embedding-004 model with retrieval_document task type.

    Args:
        text: Text to embed (typically job title + location + department + description)

    Returns:
        768-dimensional embedding vector
    """
    global _client
    
    if not text or not text.strip():
        # Return zero vector for empty text
        return [0.0] * EMBEDDING_DIMENSION

    if _client is None:
        configure_gemini()

    try:
        # Use the async client via .aio
        result = await _client.aio.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=EMBEDDING_DIMENSION,
            ),
        )
        return list(result.embeddings[0].values)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return zero vector on error
        return [0.0] * EMBEDDING_DIMENSION


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.

    Args:
        texts: List of texts to embed

    Returns:
        List of 768-dimensional embedding vectors
    """
    # Simple sequential async implementation for now
    # Could be improved with asyncio.gather if needed
    results = []
    for text in texts:
        results.append(await generate_embedding(text))
    return results


def create_job_embedding_text(job: dict[str, Any]) -> str:
    """
    Create the text to embed from a job document.

    Combines title, location, department, and plain text description.

    Args:
        job: Job document with title, location, department, description_text fields

    Returns:
        Combined text for embedding
    """
    parts = []

    if job.get("title"):
        parts.append(f"Title: {job['title']}")

    if job.get("location"):
        parts.append(f"Location: {job['location']}")

    if job.get("department"):
        parts.append(f"Department: {job['department']}")

    if job.get("description_text"):
        parts.append(f"Description: {job['description_text']}")

    return "\n".join(parts)
