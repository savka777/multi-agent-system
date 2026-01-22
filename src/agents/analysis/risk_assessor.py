from ...config.agent_configs import RISK_ASSESSOR
from typing import Optional, Dict, Any
from ..base import run_agent, AgentResult, parse_json_from_output
import asyncio

"""Risk Assessor Agent - identifies risks across all domains."""

import json
from typing import Optional, Dict, Any, List
from ..base import run_agent, AgentResult, parse_json_from_output
from ...config.agent_configs import RISK_ASSESSOR


async def run_risk_assessor(
    research_outputs: List[Dict[str, Any]],
    analysis_outputs: Optional[List[Dict[str, Any]]] = None,
    startup_name: str = ""
) -> AgentResult:
    """Perform comprehensive risk assessment using all available data."""
    # Compile all available data
    context_parts = []

    if startup_name:
        context_parts.append(f"Startup: {startup_name}\n")

    context_parts.append("## Research Findings:")
    for output in research_outputs:
        if output.get("success") and output.get("output"):
            agent_name = output.get("agent", "Unknown")
            context_parts.append(f"\n### {agent_name}:")
            context_parts.append(json.dumps(output.get("output"), indent=2, default=str))

    if analysis_outputs:
        context_parts.append("\n## Analysis Findings:")
        for output in analysis_outputs:
            if output.get("success") and output.get("output"):
                agent_name = output.get("agent", "Unknown")
                context_parts.append(f"\n### {agent_name}:")
                context_parts.append(json.dumps(output.get("output"), indent=2, default=str))

    context = "\n".join(context_parts)

    prompt = f"""Based on all research and analysis, perform a comprehensive risk assessment:

{context}

Identify risks across these domains:
1. Market Risks - market size, timing, adoption
2. Competitive Risks - competition, pricing pressure
3. Execution Risks - team capability, scaling
4. Financial Risks - runway, profitability
5. Regulatory Risks - compliance, legal exposure

For each risk provide: category, description, severity (1-10), likelihood (1-10), mitigation.

Format as JSON:
{{
    "market_risks": [{{"description": "...", "severity": 6, "likelihood": 4, "mitigation": "..."}}],
    "competitive_risks": [...],
    "execution_risks": [...],
    "financial_risks": [...],
    "regulatory_risks": [...],
    "overall_risk_score": 6,
    "top_risks": ["Risk 1", "Risk 2", "Risk 3"],
    "mitigation_suggestions": ["Suggestion 1", "Suggestion 2"]
}}
"""

    result = await run_agent(
        agent_name=RISK_ASSESSOR.name,
        prompt=prompt,
        tools=RISK_ASSESSOR.tools,
        model=RISK_ASSESSOR.model,
        system_prompt=RISK_ASSESSOR.system_prompt,
        timeout_seconds=RISK_ASSESSOR.timeout_seconds
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output)
        if parsed:
            result.output = parsed

    return result