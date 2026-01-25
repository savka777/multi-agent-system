from ..base import run_agent, AgentResult, parse_json_from_output
from ...config.agent_configs import COMPETITOR_SCOUT


async def run_competitor_scout(
    startup_name: str,
    startup_description: str
) -> AgentResult:
    """
    Find top competitors only.
    ONE task: Identify 3-5 main competitors.
    """
    prompt = f"""Find competitors for {startup_name}.

Company description: {startup_description}

YOUR TASK: Identify top 3-5 competitors. Use 1-2 web searches maximum.

Return JSON:
{{
    "competitors": [
        {{"name": "Square", "type": "direct", "strength": "SMB focus"}},
        {{"name": "PayPal", "type": "direct", "strength": "Consumer brand"}},
        {{"name": "Adyen", "type": "direct", "strength": "Enterprise"}}
    ],
    "market_leader": "Stripe or competitor name",
    "competitive_landscape": "fragmented/consolidated/emerging"
}}
"""

    result = await run_agent(
        agent_name=COMPETITOR_SCOUT.name,
        prompt=prompt,
        tools=COMPETITOR_SCOUT.tools,
        model=COMPETITOR_SCOUT.model,
        system_prompt=COMPETITOR_SCOUT.system_prompt,
        timeout_seconds=COMPETITOR_SCOUT.timeout_seconds,
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output)
        if parsed:
            result.output = parsed

    return result