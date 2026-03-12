PYTHON_SYSTEM_PROMPT = """You are an expert Python test engineer. Generate pytest-bdd test code from Gherkin feature files.
Follow these conventions:
- Use pytest-bdd decorators (@scenario, @given, @when, @then)
- Use parsers.parse for parameterized steps
- Use requests library for API calls
- Use pytest fixtures for shared state
- Include proper assertions with descriptive messages
- Generate complete, runnable code"""

PYTHON_PROMPT = """Generate pytest-bdd test code for the following Gherkin feature:

```gherkin
{gherkin_content}
```

{context_section}

Generate the following files:
1. conftest.py - shared fixtures (API session, base URL, common setup)
2. test_{{feature_name}}.py - scenario imports and test functions
3. step_defs/{{feature_name}}_steps.py - step definitions with @given/@when/@then

Requirements:
- Use `requests` library for HTTP calls
- Use `pytest.fixture` for shared state between steps
- Handle both Scenario and Scenario Outline (Examples tables)
- Include proper error assertions for negative test cases
- Use environment variables for BASE_URL configuration
- Each file should be complete and runnable

Output each file as:
===FILE: filename.py===
<code>
===END_FILE==="""

JAVASCRIPT_SYSTEM_PROMPT = """You are an expert JavaScript test engineer. Generate Cucumber.js test code from Gherkin feature files.
Follow these conventions:
- Use @cucumber/cucumber package
- Use Given, When, Then from @cucumber/cucumber
- Use axios for API calls
- Use chai for assertions
- Use World class for shared state
- Generate complete, runnable code"""

JAVASCRIPT_PROMPT = """Generate Cucumber.js test code for the following Gherkin feature:

```gherkin
{gherkin_content}
```

{context_section}

Generate the following files:
1. support/world.js - World class with shared state (API client, base URL)
2. step_definitions/{{feature_name}}.steps.js - step definitions with Given/When/Then

Requirements:
- Use `axios` for HTTP calls
- Use `chai` expect for assertions
- Use Cucumber World class for sharing state between steps
- Handle both Scenario and Scenario Outline (Examples tables)
- Handle DataTable parameters
- Include proper error assertions for negative test cases
- Use environment variables for BASE_URL configuration
- Each file should be complete and runnable

Output each file as:
===FILE: filename.js===
<code>
===END_FILE==="""


def build_code_generation_prompt(
    gherkin_content: str,
    language: str,
    context: str | None = None,
) -> tuple[str, str]:
    """Build the test code generation prompt. Returns (system_prompt, user_prompt)."""
    context_section = ""
    if context:
        context_section = f"""Additional context from system documentation (for understanding API structure):
{context}"""

    if language == "python":
        return (
            PYTHON_SYSTEM_PROMPT,
            PYTHON_PROMPT.format(
                gherkin_content=gherkin_content,
                context_section=context_section,
            ),
        )
    elif language == "javascript":
        return (
            JAVASCRIPT_SYSTEM_PROMPT,
            JAVASCRIPT_PROMPT.format(
                gherkin_content=gherkin_content,
                context_section=context_section,
            ),
        )
    else:
        raise ValueError(f"Unsupported language: {language}. Use 'python' or 'javascript'.")
