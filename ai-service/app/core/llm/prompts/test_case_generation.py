SYSTEM_PROMPT = """You are an expert QA engineer specializing in BDD (Behavior-Driven Development) test case design.
You generate comprehensive Gherkin test cases from system design documentation.

Rules:
1. Generate BOTH positive and negative test scenarios
2. For API endpoints, generate individual API-level tests
3. For workflows, generate end-to-end scenario tests
4. Use Scenario Outline with Examples for parameterized tests
5. Tag each scenario appropriately: @positive, @negative, @api, @e2e, @smoke
6. Each Feature block should be self-contained and represent one logical feature
7. Include Background section when multiple scenarios share common setup
8. Use realistic test data in Examples tables
9. Cover edge cases, boundary values, and error conditions in negative tests
10. Output valid Gherkin syntax only — no explanations outside of Gherkin blocks"""

GENERATION_PROMPT = """Based on the following system design documentation, generate comprehensive Gherkin test cases.

DOCUMENTATION CONTEXT:
{context}

{feature_instruction}

Requirements:
- Generate one or more Feature blocks (each as a complete, standalone feature)
- Include positive scenarios (happy path, valid inputs, expected behavior)
- Include negative scenarios (error handling, invalid inputs, edge cases, boundary values)
- Include individual API tests for each endpoint mentioned
- Include end-to-end scenario tests for complete workflows
- Use Scenario Outline with Examples tables for parameterized testing
- Tag scenarios: @positive, @negative, @api, @e2e, @smoke (as appropriate)
- Use descriptive scenario names that explain the test purpose
- Include proper Given/When/Then steps with realistic data

Output ONLY valid Gherkin. Separate each Feature block with a line containing exactly "---FEATURE_SEPARATOR---".

Generate the test cases now:"""


def build_generation_prompt(
    context: str,
    feature_description: str | None = None,
    include_positive: bool = True,
    include_negative: bool = True,
    include_api_tests: bool = True,
    include_e2e_tests: bool = True,
) -> str:
    """Build the test case generation prompt."""
    instructions = []

    if feature_description:
        instructions.append(f"Focus on this specific feature: {feature_description}")

    test_types = []
    if include_positive:
        test_types.append("positive (happy path)")
    if include_negative:
        test_types.append("negative (error handling, edge cases, boundary values)")
    if include_api_tests:
        test_types.append("individual API endpoint tests")
    if include_e2e_tests:
        test_types.append("end-to-end scenario tests")

    if test_types:
        instructions.append(f"Include these test types: {', '.join(test_types)}")

    feature_instruction = "\n".join(instructions) if instructions else "Generate comprehensive test cases covering all features found in the documentation."

    return GENERATION_PROMPT.format(
        context=context,
        feature_instruction=feature_instruction,
    )
