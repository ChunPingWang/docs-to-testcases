import pdfplumber
from pathlib import Path


def parse_pdf(file_path: str) -> dict:
    """Parse a PDF file and extract text with page metadata."""
    sections = []
    tables = []

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                sections.append({
                    "title": f"Page {i + 1}",
                    "heading_path": f"Page {i + 1}",
                    "content": text.strip(),
                    "page_number": i + 1,
                })

            # Extract tables from page
            page_tables = page.extract_tables()
            for table in page_tables:
                if not table:
                    continue
                header = [str(c or "") for c in table[0]]
                table_text = " | ".join(header) + "\n"
                for row in table[1:]:
                    cells = [str(c or "") for c in row]
                    table_text += " | ".join(cells) + "\n"
                tables.append(table_text)

    full_text = "\n\n".join(s["content"] for s in sections)
    if tables:
        full_text += "\n\n" + "\n\n".join(tables)

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
