import re
from pathlib import Path


def parse_markdown(file_path: str) -> dict:
    """Parse a Markdown file and extract text split by headings."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = []
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    # Find all headings and their positions
    headings = [(m.start(), len(m.group(1)), m.group(2).strip()) for m in heading_pattern.finditer(content)]

    if not headings:
        # No headings — treat entire content as one section
        sections.append({
            "title": "",
            "heading_path": "",
            "content": content.strip(),
        })
    else:
        # Content before first heading
        if headings[0][0] > 0:
            pre_content = content[: headings[0][0]].strip()
            if pre_content:
                sections.append({
                    "title": "",
                    "heading_path": "",
                    "content": pre_content,
                })

        heading_stack = []
        for i, (pos, level, title) in enumerate(headings):
            end = headings[i + 1][0] if i + 1 < len(headings) else len(content)
            section_content = content[pos:end]

            # Remove the heading line itself from content
            first_newline = section_content.find("\n")
            if first_newline >= 0:
                section_content = section_content[first_newline + 1:].strip()
            else:
                section_content = ""

            # Build heading path
            heading_stack = [h for h in heading_stack if h[0] < level]
            heading_stack.append((level, title))
            heading_path = " > ".join(h[1] for h in heading_stack)

            if section_content:
                sections.append({
                    "title": title,
                    "heading_path": heading_path,
                    "content": section_content,
                })

    full_text = content

    return {
        "text": full_text,
        "sections": sections,
        "tables": [],
        "metadata": {
            "filename": Path(file_path).name,
            "section_count": len(sections),
        },
    }
