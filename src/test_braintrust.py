"""
Toy example to test Braintrust integration.
Run with: uv run python src/test_braintrust.py
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import braintrust
from anthropic import Anthropic

# Wrap Anthropic client for automatic tracing
client = braintrust.wrap_anthropic(Anthropic())

# Initialize logger for a project
logger = braintrust.init_logger(project="test-project")


def simple_qa(question: str) -> str:
    """Simple Q&A function to test."""
    with logger.start_span(name="simple_qa") as span:
        span.log(input=question)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=256,
            messages=[{"role": "user", "content": question}],
        )
        result = response.content[0].text
        span.log(output=result)
        return result


def test_basic_tracing():
    """Test basic Braintrust tracing."""
    print("Testing basic tracing...")
    result = simple_qa("What is 2 + 2?")
    print(f"Result: {result}")
    print("\nCheck your Braintrust dashboard for the trace!")
    print("https://www.braintrust.dev")


if __name__ == "__main__":
    print("=" * 50)
    print("Braintrust Test")
    print("=" * 50)

    # Verify API keys are set
    if not os.getenv("BRAINTRUST_API_KEY"):
        print("ERROR: BRAINTRUST_API_KEY not set in .env file")
        exit(1)
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set in .env file")
        exit(1)

    print("API keys loaded successfully!\n")

    # Run test
    test_basic_tracing()

    # Flush logs to ensure they're sent
    braintrust.flush()
