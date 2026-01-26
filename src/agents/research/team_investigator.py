from ..base import run_agent, AgentResult, parse_json_from_output
from ...config.agent_configs import TEAM_INVESTIGATOR


async def run_team_investigator(startup_name: str) -> AgentResult:
    """
    Find founders and key executives only.
    ONE task: Identify founding team and their backgrounds.
    """
    prompt = f"""Find the founding team of {startup_name}.

YOUR TASK: Identify founders and CEO. Use 1-2 web searches maximum.

Return JSON:
{{
    "founders": [
        {{"name": "John Doe", "role": "CEO", "background": "Previously at PayPal"}}
    ],
    "founding_year": 2010,
    "key_executives": ["CFO name", "CTO name"],
    "team_size_estimate": "1000-5000"
}}
"""

    result = await run_agent(
        agent_name=TEAM_INVESTIGATOR.name,
        prompt=prompt,
        tools=TEAM_INVESTIGATOR.tools,
        model=TEAM_INVESTIGATOR.model,
        system_prompt=TEAM_INVESTIGATOR.system_prompt,
        timeout_seconds=TEAM_INVESTIGATOR.timeout_seconds,
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output, agent_name=result.agent_name)
        if parsed:
            result.output = parsed
        else:
            result.success = False
            result.error = "JSON parse failed: could not extract structured output"

    return result