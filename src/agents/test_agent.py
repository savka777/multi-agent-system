import asyncio
from src.agents.research.company_profiler import run_company_profiler


async def test():
    """Test the Company Profiler agent."""
    print("Testing Company Profiler agent...\n")
    
    result = await run_company_profiler(
        startup_name="Stripe",
        startup_description="Online payment processing platform"
    )

    print(f"Success: {result.success}")
    print(f"Time: {result.execution_time_ms}ms")

    if result.success:
        print(f"\nOutput type: {type(result.output)}")
        if isinstance(result.output, dict):
            print(f"Founded: {result.output.get('founded')}")
            print(f"Location: {result.output.get('location')}")
            print(f"Employees: {result.output.get('employee_count')}")
    else:
        print(f"Error: {result.error}")
        if result.raw_output:
            print(f"Raw output (first 500 chars): {result.raw_output[:500]}")


if __name__ == "__main__":
    asyncio.run(test())