from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


def chunk_by_sections(sections: list[dict], chunk_size: int = 0, chunk_overlap: int = 0) -> list[dict]:
    """Chunk document sections. If a section is too large, split it further."""
    cs = chunk_size or settings.chunk_size
    co = chunk_overlap or settings.chunk_overlap

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cs,
        chunk_overlap=co,
        separators=["\n\n", "\n", ". ", " "],
    )

    chunks = []
    for section in sections:
        content = section.get("content", "")
        if not content.strip():
            continue

        if len(content) <= cs:
            chunks.append({
                "text": content,
                "section_title": section.get("title", ""),
                "heading_path": section.get("heading_path", ""),
                "page_number": section.get("page_number"),
            })
        else:
            sub_chunks = splitter.split_text(content)
            for sub in sub_chunks:
                chunks.append({
                    "text": sub,
                    "section_title": section.get("title", ""),
                    "heading_path": section.get("heading_path", ""),
                    "page_number": section.get("page_number"),
                })

    # Add chunk indices
    for i, chunk in enumerate(chunks):
        chunk["chunk_index"] = i

    return chunks


def chunk_general(text: str, chunk_size: int = 0, chunk_overlap: int = 0) -> list[dict]:
    """General purpose chunking for plain text without sections."""
    cs = chunk_size or settings.chunk_size
    co = chunk_overlap or settings.chunk_overlap

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cs,
        chunk_overlap=co,
        separators=["\n\n", "\n", ". ", " "],
    )

    texts = splitter.split_text(text)
    return [
        {
            "text": t,
            "section_title": "",
            "heading_path": "",
            "page_number": None,
            "chunk_index": i,
        }
        for i, t in enumerate(texts)
    ]
