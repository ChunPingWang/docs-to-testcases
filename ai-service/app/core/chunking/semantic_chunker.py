"""Semantic chunker that splits text by embedding similarity between sentences."""

import re

from app.core.embedding.ollama_embedder import embed_texts
from app.core.runtime_settings import runtime_settings


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?。！？\n])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


async def chunk_semantic(sections: list[dict]) -> list[dict]:
    """Chunk sections using semantic similarity between adjacent sentences.

    Sentences are embedded, and a new chunk boundary is created when
    the cosine similarity between adjacent sentences drops below the threshold.
    """
    threshold = runtime_settings.semantic_chunk_threshold
    chunk_size = runtime_settings.chunk_size
    all_chunks: list[dict] = []

    for section in sections:
        content = section.get("content", "")
        if not content.strip():
            continue

        sentences = _split_sentences(content)
        if not sentences:
            continue

        # If very few sentences, keep as single chunk
        if len(sentences) <= 2:
            all_chunks.append({
                "text": content.strip(),
                "section_title": section.get("title", ""),
                "heading_path": section.get("heading_path", ""),
                "page_number": section.get("page_number"),
            })
            continue

        # Embed all sentences
        embeddings = await embed_texts(sentences, embed_type="db")

        # Find split points where similarity drops below threshold
        split_points = [0]
        for i in range(1, len(sentences)):
            sim = _cosine_similarity(embeddings[i - 1], embeddings[i])
            if sim < threshold:
                split_points.append(i)

        # Build chunks from split points
        for j in range(len(split_points)):
            start = split_points[j]
            end = split_points[j + 1] if j + 1 < len(split_points) else len(sentences)
            chunk_text = " ".join(sentences[start:end])

            # If chunk exceeds max size, further split
            if len(chunk_text) > chunk_size:
                # Simple sub-split by sentence groups
                sub_text = ""
                for s in sentences[start:end]:
                    if len(sub_text) + len(s) + 1 > chunk_size and sub_text:
                        all_chunks.append({
                            "text": sub_text.strip(),
                            "section_title": section.get("title", ""),
                            "heading_path": section.get("heading_path", ""),
                            "page_number": section.get("page_number"),
                        })
                        sub_text = ""
                    sub_text += " " + s
                if sub_text.strip():
                    all_chunks.append({
                        "text": sub_text.strip(),
                        "section_title": section.get("title", ""),
                        "heading_path": section.get("heading_path", ""),
                        "page_number": section.get("page_number"),
                    })
            else:
                all_chunks.append({
                    "text": chunk_text,
                    "section_title": section.get("title", ""),
                    "heading_path": section.get("heading_path", ""),
                    "page_number": section.get("page_number"),
                })

    # Add chunk indices
    for i, chunk in enumerate(all_chunks):
        chunk["chunk_index"] = i

    return all_chunks
