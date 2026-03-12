from docx import Document
from pathlib import Path


def parse_docx(file_path: str) -> dict:
    """Parse a .docx file and extract text with structural metadata."""
    doc = Document(file_path)
    sections = []
    current_heading = ""
    current_text = []
    heading_path = []

    for para in doc.paragraphs:
        style_name = para.style.name if para.style else ""

        if style_name.startswith("Heading"):
            # Save previous section
            if current_text:
                sections.append({
                    "title": current_heading,
                    "heading_path": " > ".join(heading_path),
                    "content": "\n".join(current_text),
                })
                current_text = []

            level = int(style_name.replace("Heading ", "").strip() or "1")
            current_heading = para.text.strip()
            heading_path = heading_path[: level - 1] + [current_heading]
        elif para.text.strip():
            current_text.append(para.text.strip())

    # Save last section
    if current_text:
        sections.append({
            "title": current_heading,
            "heading_path": " > ".join(heading_path),
            "content": "\n".join(current_text),
        })

    # Extract tables
    tables = []
    for table in doc.tables:
        rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(cells)
        if rows:
            header = rows[0]
            table_text = " | ".join(header) + "\n"
            for row in rows[1:]:
                table_text += " | ".join(row) + "\n"
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
            "section_count": len(sections),
            "table_count": len(tables),
        },
    }
