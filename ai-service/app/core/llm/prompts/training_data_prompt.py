TRAINING_DATA_SYSTEM = """You are generating training data pairs for fine-tuning a model to understand system design documents and generate test cases."""

QA_PAIR_PROMPT = """Based on the following documentation section, generate 3-5 question-answer pairs that test understanding of the system design. Output as JSON array.

Documentation:
{content}

Generate pairs in this format:
[
  {{"instruction": "question about the documentation", "input": "", "output": "detailed answer based on the documentation"}}
]"""

GHERKIN_PAIR_PROMPT = """Based on the following documentation section, generate a training pair where the input is a description of a feature/requirement and the output is a complete Gherkin test case. Output as JSON.

Documentation:
{content}

Generate a pair in this format:
{{"instruction": "Generate Gherkin test cases for: <feature description>", "input": "<relevant context>", "output": "<complete Gherkin feature with positive and negative scenarios>"}}"""
