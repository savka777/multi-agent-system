from ..base import run_agent, AgentResult, parse_json_from_output
from ...config.agent_configs import COMPETITOR_SCOUT


async def run_competitor_scout(
    startup_name: str,
    startup_description: str
) -> AgentResult:
    """Research competitors for the startup."""

    prompt = f"""Identify and analyze competitors for:

Startup: {startup_name}
Description: {startup_description}

Research and report:
1. Direct competitors (same solution, same market)
2. Indirect competitors (different solution, same problem)
3. Each competitor's strengths and weaknesses
4. Market positioning comparison

Output as JSON: {{...}}
"""

    result = await run_agent(
        agent_name=COMPETITOR_SCOUT.name,
        prompt=prompt,
        tools=COMPETITOR_SCOUT.tools,
        model=COMPETITOR_SCOUT.model,
        system_prompt=COMPETITOR_SCOUT.system_prompt,
        timeout_seconds=COMPETITOR_SCOUT.timeout_seconds
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output)
        if parsed:
            result.output = parsed

    return result