from ..base import run_agent, AgentResult, parse_json_from_output
from ...config import COMPANY_PROFILER

async def run_company_profiler(startup_name: str,startup_description: str) -> AgentResult:
    prompt = f"""Research the following startup...
    
    Format your response as valid JSON:
    {{
        "name": "{startup_name}",
        "founded": "year or null",
        ...
    }}
    """

    result = await run_agent(
        agent_name=COMPANY_PROFILER.name,
        prompt=prompt,
        tools=COMPANY_PROFILER.tools,
        model=COMPANY_PROFILER.model,
        system_prompt=COMPANY_PROFILER.system_prompt,
        timeout_seconds=COMPANY_PROFILER.timeout_seconds
)

    if result.success == True and result.raw_output:
        parsed = parse_json_from_output(result.raw_output)
        if parsed:
            result.output = parsed

    return result