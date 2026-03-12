from app.core.parsers.docx_parser import parse_docx
from app.core.parsers.xlsx_parser import parse_xlsx
from app.core.parsers.pdf_parser import parse_pdf
from app.core.parsers.markdown_parser import parse_markdown
from app.core.parsers.text_parser import parse_text

PARSERS = {
    "docx": parse_docx,
    "xlsx": parse_xlsx,
    "xls": parse_xlsx,
    "pdf": parse_pdf,
    "md": parse_markdown,
    "markdown": parse_markdown,
    "txt": parse_text,
    "text": parse_text,
}


def parse_document(file_path: str, file_type: str) -> dict:
    """Route document to the appropriate parser based on file type."""
    ext = file_type.lower().lstrip(".")

    parser = PARSERS.get(ext)
    if parser is None:
        raise ValueError(f"Unsupported file type: {file_type}. Supported: {list(PARSERS.keys())}")

    return parser(file_path)
