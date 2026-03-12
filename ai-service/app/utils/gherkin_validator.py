import re


def validate_gherkin(content: str) -> dict:
    """Validate basic Gherkin syntax and extract structure info."""
    errors = []
    warnings = []

    lines = content.strip().split("\n")
    has_feature = False
    has_scenario = False
    scenario_count = 0
    tags = set()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped.startswith("Feature:"):
            has_feature = True
        elif stripped.startswith(("Scenario:", "Scenario Outline:")):
            has_scenario = True
            scenario_count += 1
        elif stripped.startswith("@"):
            for tag in stripped.split():
                if tag.startswith("@"):
                    tags.add(tag)

    if not has_feature:
        errors.append("Missing 'Feature:' keyword")
    if not has_scenario:
        errors.append("Missing 'Scenario:' or 'Scenario Outline:' keyword")

    # Check for Given/When/Then steps
    step_pattern = re.compile(r"^\s*(Given|When|Then|And|But)\s+.+", re.MULTILINE)
    steps = step_pattern.findall(content)
    if not steps:
        errors.append("No Given/When/Then steps found")

    # Check Scenario Outline has Examples
    outline_pattern = re.compile(r"Scenario Outline:", re.MULTILINE)
    examples_pattern = re.compile(r"Examples:", re.MULTILINE)
    outlines = len(outline_pattern.findall(content))
    examples = len(examples_pattern.findall(content))
    if outlines > examples:
        warnings.append(f"Found {outlines} Scenario Outline(s) but only {examples} Examples section(s)")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "scenario_count": scenario_count,
        "tags": list(tags),
    }


def extract_feature_name(gherkin_content: str) -> str:
    """Extract the feature name from Gherkin content."""
    match = re.search(r"Feature:\s*(.+)", gherkin_content)
    if match:
        return match.group(1).strip()
    return "Unnamed Feature"


def split_features(content: str, separator: str = "---FEATURE_SEPARATOR---") -> list[str]:
    """Split multiple features from LLM output."""
    if separator in content:
        features = content.split(separator)
    else:
        # Try splitting by "Feature:" keyword
        parts = re.split(r"(?=^Feature:)", content, flags=re.MULTILINE)
        features = [p for p in parts if p.strip()]

    # Clean up each feature
    cleaned = []
    for f in features:
        f = f.strip()
        if f and "Feature:" in f:
            # Remove any markdown code fences
            f = re.sub(r"```(?:gherkin)?\s*", "", f)
            f = re.sub(r"```\s*$", "", f)
            cleaned.append(f.strip())

    return cleaned
