from pathlib import Path


def parse_text(file_path: str) -> dict:
    """Parse a plain text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "text": content,
        "sections": [
            {
                "title": "",
                "heading_path": "",
                "content": content.strip(),
            }
        ],
        "tables": [],
        "metadata": {
            "filename": Path(file_path).name,
        },
    }
