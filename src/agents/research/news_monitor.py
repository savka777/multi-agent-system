from ..base import run_agent, AgentResult, parse_json_from_output
from ...config.agent_configs import NEWS_MONITOR


async def run_news_monitor(
    startup_name: str
) -> AgentResult:
    """Find recent news and press coverage."""

    prompt = f"""Find recent news about: {startup_name}

Search for:
1. Recent press releases
2. News articles and media coverage
3. Funding announcements
4. Product launches or major updates
5. Any controversies or concerns

Output as JSON: {{...}}
"""

    result = await run_agent(
        agent_name=NEWS_MONITOR.name,
        prompt=prompt,
        tools=NEWS_MONITOR.tools,
        model=NEWS_MONITOR.model,
        system_prompt=NEWS_MONITOR.system_prompt,
        timeout_seconds=NEWS_MONITOR.timeout_seconds
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output)
        if parsed:
            result.output = parsed

    return result