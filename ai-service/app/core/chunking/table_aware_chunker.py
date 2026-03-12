"""Table-aware chunker that preserves markdown tables as complete chunks."""

import re

from app.core.chunking.base_chunker import chunk_by_sections
from app.core.runtime_settings import runtime_settings

# Regex to detect markdown tables (header + separator + rows)
_TABLE_RE = re.compile(
    r"(\|[^\n]+\|\n\|[\s\-:|]+\|\n(?:\|[^\n]+\|\n?)+)",
    re.MULTILINE,
)


def chunk_table_aware(sections: list[dict]) -> list[dict]:
    """Chunk sections while preserving markdown tables as independent chunks.

    1. Detect markdown tables via regex → extract as standalone chunks (is_table=True)
    2. Remaining text is chunked via the standard chunk_by_sections()
    """
    table_chunks: list[dict] = []
    text_sections: list[dict] = []

    for section in sections:
        content = section.get("content", "")
        if not content.strip():
            continue

        # Find all tables in the section
        matches = list(_TABLE_RE.finditer(content))
        if not matches:
            text_sections.append(section)
            continue

        # Split content around tables
        last_end = 0
        for match in matches:
            # Text before the table
            before = content[last_end:match.start()].strip()
            if before:
                text_sections.append({
                    **section,
                    "content": before,
                })

            # The table itself
            table_chunks.append({
                "text": match.group(0),
                "section_title": section.get("title", ""),
                "heading_path": section.get("heading_path", ""),
                "page_number": section.get("page_number"),
                "is_table": True,
            })

            last_end = match.end()

        # Text after the last table
        after = content[last_end:].strip()
        if after:
            text_sections.append({
                **section,
                "content": after,
            })

    # Chunk the non-table text normally
    text_chunks = chunk_by_sections(text_sections) if text_sections else []

    # Mark text chunks as not tables
    for c in text_chunks:
        c["is_table"] = False

    # Combine and re-index
    all_chunks = text_chunks + table_chunks
    for i, chunk in enumerate(all_chunks):
        chunk["chunk_index"] = i

    return all_chunks
