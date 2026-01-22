from typing import Optional, Dict, Any
from ...config.agent_configs import FINANCIAL_ANALYST
from ..base import run_agent, AgentResult, parse_json_from_output
import asyncio

async def run_financial_analyst(
    company_profile: Optional[Dict[str, Any]] = None,
    market_analysis: Optional[Dict[str, Any]] = None,
    startup_name: str = "",
    startup_description: str = ""
) -> AgentResult:
    """Analyze financial health based on research data."""
    # Build context from available data
    context_parts = []

    if startup_name:
        context_parts.append(f"Startup Name: {startup_name}")
    if startup_description:
        context_parts.append(f"Description: {startup_description}")
    if company_profile:
        context_parts.append(f"\n## Company Profile Data:\n{_format_dict(company_profile)}")
    if market_analysis:
        context_parts.append(f"\n## Market Analysis Data:\n{_format_dict(market_analysis)}")

    context = "\n".join(context_parts)

    prompt = f"""Analyze the financial health and sustainability of this startup:

{context}

Please provide:
1. Total funding raised (sum from funding history)
2. Estimated runway based on funding stage
3. Revenue model assessment
4. Financial health score (1-10)
5. Key financial concerns

Format your response as valid JSON:
{{
    "total_funding": {{"amount": 50000000, "currency": "USD"}},
    "estimated_runway": "18-24 months",
    "revenue_model": "SaaS subscription",
    "financial_health_score": 7,
    "concerns": ["High burn rate", "Need path to profitability"]
}}

Base analysis on available data. Note if data is missing.
"""

    result = await run_agent(
        agent_name=FINANCIAL_ANALYST.name,
        prompt=prompt,
        tools=FINANCIAL_ANALYST.tools,
        model=FINANCIAL_ANALYST.model,
        system_prompt=FINANCIAL_ANALYST.system_prompt,
        timeout_seconds=FINANCIAL_ANALYST.timeout_seconds
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output)
        if parsed:
            result.output = parsed

    return result


def _format_dict(d: Dict[str, Any], indent: int = 0) -> str:
    """Format a dictionary for readable output."""
    lines = []
    prefix = "  " * indent
    for key, value in d.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_format_dict(value, indent + 1))
        else:
            lines.append(f"{prefix}{key}: {value}")
    return "\n".join(lines)