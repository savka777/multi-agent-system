from ..base import run_agent, AgentResult, parse_json_from_output
from ...config.agent_configs import COMPANY_PROFILER


async def run_company_profiler(startup_name: str, startup_description: str) -> AgentResult:
    """
    Research basic company information.
    ONE task: Find founding year, headquarters, employee count, and business model.
    """
    prompt = f"""Research {startup_name}.

Company description: {startup_description}

YOUR TASK: Find basic company facts. Use 1-2 web searches maximum.

Return JSON:
{{
    "name": "{startup_name}",
    "founded_year": 2010,
    "headquarters": "City, Country",
    "employee_count": "1000-5000",
    "business_model": "B2B SaaS payments infrastructure",
    "key_products": ["Payments", "Billing", "Connect"]
}}
"""

    result = await run_agent(
        agent_name=COMPANY_PROFILER.name,
        prompt=prompt,
        tools=COMPANY_PROFILER.tools,
        model=COMPANY_PROFILER.model,
        system_prompt=COMPANY_PROFILER.system_prompt,
        timeout_seconds=COMPANY_PROFILER.timeout_seconds,
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output, agent_name=result.agent_name)
        if parsed:
            result.output = parsed
        else:
            # JSON parse failed despite successful execution - mark as failed
            result.success = False
            result.error = "JSON parse failed: could not extract structured output"

    return result