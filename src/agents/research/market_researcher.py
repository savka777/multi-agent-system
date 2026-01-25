from ..base import run_agent, AgentResult, parse_json_from_output
from ...config.agent_configs import MARKET_RESEARCHER


async def run_market_researcher(
    startup_name: str,
    startup_description: str
) -> AgentResult:
    """
    Research market size only.
    ONE task: Find TAM/SAM/SOM and growth rate.
    """
    prompt = f"""Research market size for {startup_name}.

Company description: {startup_description}

YOUR TASK: Find market size numbers. Use 1-2 web searches maximum.

Return JSON:
{{
    "target_market": "Online payments processing",
    "tam_billions": 100,
    "sam_billions": 40,
    "som_billions": 5,
    "growth_rate_percent": 12,
    "source": "where you found this data"
}}
"""

    result = await run_agent(
        agent_name=MARKET_RESEARCHER.name,
        prompt=prompt,
        tools=MARKET_RESEARCHER.tools,
        model=MARKET_RESEARCHER.model,
        system_prompt=MARKET_RESEARCHER.system_prompt,
        timeout_seconds=MARKET_RESEARCHER.timeout_seconds,
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output)
        if parsed:
            result.output = parsed

    return result