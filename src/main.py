import asyncio
from .workflow import run_due_diligence


async def main():
    """Run the due diligence workflow."""
    print("Starting Due Diligence Workflow...")
    print("=" * 60)

    result = await run_due_diligence(
        startup_name="beatvest",
        startup_descrption="Your app for creating long-term wealth. Whether you're a beginner or already investing, start at the level that is right for you."
    )

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Status: {result.get('current_stage')}")
    print(f"Research outputs: {len(result.get('research_outputs', []))}")
    print(f"Errors: {len(result.get('errors', []))}")

    # Show research summary
    for output in result.get("research_outputs", []):
        status = "OK" if output.get("success") else "FAIL"
        print(f"  [{status}] {output.get('agent')}")


if __name__ == "__main__":
    asyncio.run(main())