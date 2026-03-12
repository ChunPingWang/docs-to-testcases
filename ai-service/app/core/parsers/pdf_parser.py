import pdfplumber
from pathlib import Path


def _table_to_markdown(table: list[list]) -> str:
    """Convert a pdfplumber table to markdown format."""
    if not table or not table[0]:
        return ""
    header = [str(c or "") for c in table[0]]
    md = "| " + " | ".join(header) + " |\n"
    md += "| " + " | ".join("---" for _ in header) + " |\n"
    for row in table[1:]:
        cells = [str(c or "") for c in row]
        md += "| " + " | ".join(cells) + " |\n"
    return md.strip()


def parse_pdf(file_path: str) -> dict:
    """Parse a PDF file and extract text with page metadata.

    Tables are converted to markdown and embedded in-place within page content
    rather than appended at the end.
    """
    sections = []
    tables = []

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""

            # Extract tables from page and convert to markdown
            page_tables = page.extract_tables()
            table_markdowns = []
            for table in page_tables:
                if not table:
                    continue
                md = _table_to_markdown(table)
                if md:
                    table_markdowns.append(md)
                    tables.append(md)

            # Combine page text with inline tables
            page_content = text.strip()
            if table_markdowns:
                page_content += "\n\n" + "\n\n".join(table_markdowns)

            if page_content.strip():
                sections.append({
                    "title": f"Page {i + 1}",
                    "heading_path": f"Page {i + 1}",
                    "content": page_content,
                    "page_number": i + 1,
                })

    full_text = "\n\n".join(s["content"] for s in sections)

    return {
        "text": full_text,
        "sections": sections,
        "tables": tables,
        "metadata": {
            "filename": Path(file_path).name,
            "page_count": len(sections),
            "table_count": len(tables),
        },
    }
