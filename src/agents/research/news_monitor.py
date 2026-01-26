from ..base import run_agent, AgentResult, parse_json_from_output
from ...config.agent_configs import NEWS_MONITOR


async def run_news_monitor(startup_name: str) -> AgentResult:
    """
    Find recent news only.
    ONE task: Get latest funding/product news.
    """
    prompt = f"""Find recent news about {startup_name}.

YOUR TASK: Find 3-5 recent news items. Use 1-2 web searches maximum.

Return JSON:
{{
    "recent_news": [
        {{"date": "2024-01", "headline": "...", "type": "funding/product/partnership"}}
    ],
    "latest_funding": {{"amount": "$100M", "round": "Series D", "date": "2024"}},
    "sentiment": "positive/neutral/negative"
}}
"""

    result = await run_agent(
        agent_name=NEWS_MONITOR.name,
        prompt=prompt,
        tools=NEWS_MONITOR.tools,
        model=NEWS_MONITOR.model,
        system_prompt=NEWS_MONITOR.system_prompt,
        timeout_seconds=NEWS_MONITOR.timeout_seconds,
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output, agent_name=result.agent_name)
        if parsed:
            result.output = parsed
        else:
            result.success = False
            result.error = "JSON parse failed: could not extract structured output"

    return result