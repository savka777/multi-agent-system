from ...config.agent_configs import LEGAL_REVIEWER
from typing import Optional, Dict, Any
from ..base import run_agent, AgentResult, parse_json_from_output
import asyncio

async def run_legal_reviewer(
    startup_name: str,
    market_analysis: Optional[Dict[str, Any]] = None
) -> AgentResult:
    """Conduct legal due diligence review."""
    market_context = ""
    if market_analysis:
        market_def = market_analysis.get("market_definition", "")
        if market_def:
            market_context = f"\nMarket: {market_def}"

    prompt = f"""Conduct a legal due diligence review for this startup:

Startup Name: {startup_name}{market_context}

Please search for and analyze:
1. Known lawsuits or legal disputes
2. Regulatory environment for their industry
3. IP concerns (patent disputes, trademark issues)
4. Key compliance requirements
5. Overall legal risk score (1-10)

Format your response as valid JSON:
{{
    "known_legal_issues": ["Patent claim pending"],
    "regulatory_environment": "Regulated financial services space",
    "ip_concerns": ["Core tech may overlap with existing patents"],
    "compliance_requirements": ["SOC 2", "GDPR"],
    "legal_risk_score": 5
}}

If no legal issues found, indicate that clearly.
"""

    result = await run_agent(
        agent_name=LEGAL_REVIEWER.name,
        prompt=prompt,
        tools=LEGAL_REVIEWER.tools,
        model=LEGAL_REVIEWER.model,
        system_prompt=LEGAL_REVIEWER.system_prompt,
        timeout_seconds=LEGAL_REVIEWER.timeout_seconds
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output, agent_name=result.agent_name)
        if parsed:
            result.output = parsed
        else:
            result.success = False
            result.error = "JSON parse failed: could not extract structured output"

    return result