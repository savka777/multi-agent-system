from ..base import run_agent, AgentResult, parse_json_from_output
from ...config.agent_configs import TEAM_INVESTIGATOR


async def run_team_investigator(
    startup_name: str
) -> AgentResult:
    """Research the founding team and key personnel."""

    prompt = f"""Research the team behind: {startup_name}

Find and report:
1. Founders - names, backgrounds, previous companies
2. Key executives and their experience
3. Notable advisors or board members
4. Team's track record and expertise fit

Output as JSON: {{...}}
"""

    result = await run_agent(
        agent_name=TEAM_INVESTIGATOR.name,
        prompt=prompt,
        tools=TEAM_INVESTIGATOR.tools,
        model=TEAM_INVESTIGATOR.model,
        system_prompt=TEAM_INVESTIGATOR.system_prompt,
        timeout_seconds=TEAM_INVESTIGATOR.timeout_seconds
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output)
        if parsed:
            result.output = parsed

    return result