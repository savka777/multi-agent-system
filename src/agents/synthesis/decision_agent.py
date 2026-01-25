"""Decision Agent - makes final investment recommendation using Opus."""

import json
from typing import Optional, Dict, Any, List
from ..base import run_agent, AgentResult, parse_json_from_output
from ...config.agent_configs import DECISION_AGENT


async def run_decision_agent(
    startup_name: str,
    full_report: str,
    risk_assessment: Optional[Dict[str, Any]] = None,
    research_outputs: Optional[List[Dict[str, Any]]] = None,
    analysis_outputs: Optional[List[Dict[str, Any]]] = None
) -> AgentResult:
    """Make final investment recommendation."""
    # Build context
    context_parts = []
    context_parts.append(f"# Investment Decision: {startup_name}\n")
    context_parts.append("## Due Diligence Report\n")
    context_parts.append(full_report)

    if risk_assessment:
        context_parts.append("\n## Risk Assessment Summary\n")
        context_parts.append(json.dumps(risk_assessment, indent=2, default=str))

    context = "\n".join(context_parts)

    prompt = f"""As a senior investment decision maker, provide your recommendation:

{context}

Consider:
1. Market opportunity and timing
2. Competitive positioning
3. Team capability
4. Financial health
5. Technical defensibility
6. Risk profile

Recommendation Options:
- strong_invest: Compelling, priority investment
- invest: Good opportunity, standard terms
- hold: Interesting but wait for more traction
- pass: Does not meet criteria
- strong_pass: Significant concerns, avoid

Format as JSON:
{{
    "recommendation": "invest",
    "confidence": 0.75,
    "key_factors_for": ["Large market", "Strong team"],
    "key_factors_against": ["High burn rate"],
    "conditions": ["Want to see 3 more months of data"],
    "summary_rationale": "Compelling opportunity despite concerns..."
}}

Be balanced and objective.
"""

    result = await run_agent(
        agent_name=DECISION_AGENT.name,
        prompt=prompt,
        tools=DECISION_AGENT.tools,
        model=DECISION_AGENT.model,
        system_prompt=DECISION_AGENT.system_prompt,
        timeout_seconds=DECISION_AGENT.timeout_seconds
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output)
        if parsed:
            result.output = parsed

    return result