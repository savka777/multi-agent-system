"""
Startup Due Diligence Platform

Run a complete due diligence analysis on any startup using
a multi-agent AI system built with LangGraph and Claude.
"""

import asyncio
import json
from datetime import datetime

from src.workflow import run_due_diligence


def print_header():
    print("\n" + "=" * 70)
    print("  STARTUP DUE DILIGENCE PLATFORM")
    print("  Multi-Agent AI Analysis System")
    print("=" * 70)


def print_section(title: str):
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print("─" * 70)


def print_decision(decision: dict):
    """Pretty print the investment decision."""
    if not decision:
        print("  No decision generated")
        return

    rec = decision.get("recommendation", "unknown").upper().replace("_", " ")
    confidence = decision.get("confidence", 0) * 100

    # Color-code recommendation (terminal colors)
    if "INVEST" in rec and "PASS" not in rec:
        color = "\033[92m"  # Green
    elif "PASS" in rec:
        color = "\033[91m"  # Red
    else:
        color = "\033[93m"  # Yellow

    reset = "\033[0m"

    print(f"\n  {color}> {rec}{reset}")
    print(f"    Confidence: {confidence:.0f}%\n")

    print("  Factors FOR investment:")
    for factor in decision.get("key_factors_for", [])[:3]:
        print(f"    + {factor}")

    print("\n  Factors AGAINST investment:")
    for factor in decision.get("key_factors_against", [])[:3]:
        print(f"    - {factor}")

    print(f"\n  Rationale: {decision.get('summary_rationale', 'N/A')}")


async def main():
    """Run the due diligence workflow."""
    print_header()

    # Example startup - change this to analyze different companies!
    startup_name = "Stripe"
    startup_description = """
    Stripe is a technology company that builds economic infrastructure
    for the internet. Businesses of every size use Stripe's software
    to accept payments and manage their businesses online.
    """

    print(f"\n  Analyzing: {startup_name}")
    print(f"  Started: {datetime.now().strftime('%H:%M:%S')}")

    # Run the workflow
    result = await run_due_diligence(
        startup_name=startup_name,
        startup_descrption=startup_description.strip(),
        funding_stage="Growth"
    )

    # Results summary
    print_section("RESULTS SUMMARY")

    status = result.get("current_stage", "unknown")
    research_count = len(result.get("research_outputs", []))
    analysis_count = len(result.get("analysis_outputs", []))
    error_count = len(result.get("errors", []))

    research_success = sum(
        1 for r in result.get("research_outputs", [])
        if r.get("success")
    )
    analysis_success = sum(
        1 for a in result.get("analysis_outputs", [])
        if a.get("success")
    )

    print(f"  Status: {status.upper()}")
    print(f"  Research: {research_success}/{research_count} agents succeeded")
    print(f"  Analysis: {analysis_success}/{analysis_count} agents succeeded")
    print(f"  Errors: {error_count}")

    # Investment Decision
    print_section("INVESTMENT DECISION")
    print_decision(result.get("investment_decision"))

    # Report preview
    print_section("REPORT PREVIEW")
    report = result.get("full_report", "")
    if report:
        # Show first 500 chars
        preview = report[:500]
        if len(report) > 500:
            preview += "\n\n  [...report continues...]"
        print(f"\n{preview}")
    else:
        print("  No report generated")

    # Errors (if any)
    if error_count > 0:
        print_section("ERRORS ENCOUNTERED")
        for error in result.get("errors", [])[:5]:
            print(f"  * {error[:80]}")

    print("\n" + "=" * 70)
    print(f"  Completed: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())