from ..base import run_agent, AgentResult, parse_json_from_output
from ...config.agent_configs import MARKET_RESEARCHER


async def run_market_researcher(
    startup_name: str,
    startup_description: str
) -> AgentResult:
    """Research market opportunity for the startup."""

    prompt = f"""Analyze the market opportunity for:

Startup: {startup_name}
Description: {startup_description}

Research and report:
1. Target market definition
2. TAM, SAM, SOM
3. Growth rate and trends
4. Market timing

Output as JSON: {{...}}
"""

    result = await run_agent(
        agent_name=MARKET_RESEARCHER.name,
        prompt=prompt,
        tools=MARKET_RESEARCHER.tools,
        model=MARKET_RESEARCHER.model,
        system_prompt=MARKET_RESEARCHER.system_prompt,
        timeout_seconds=MARKET_RESEARCHER.timeout_seconds
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output)
        if parsed:
            result.output = parsed

    return result