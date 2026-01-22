from ...config.agent_configs import TECH_EVALUATOR
from typing import Optional, Dict, Any
from ..base import run_agent, AgentResult, parse_json_from_output
import asyncio

"""Tech Evaluator Agent - assesses technology and technical defensibility."""
async def run_tech_evaluator(
    startup_name: str,
    startup_description: str,
    team_analysis: Optional[Dict[str, Any]] = None
) -> AgentResult:
    """Evaluate technology and technical defensibility."""
    team_context = ""
    if team_analysis:
        team_context = f"\n## Team Technical Background:\n{_format_team_tech(team_analysis)}"

    prompt = f"""Evaluate the technology and technical defensibility of this startup:

Startup Name: {startup_name}
Description: {startup_description}
{team_context}

Please research and analyze:
1. Technology stack (languages, frameworks, infrastructure)
2. Technical defensibility - what makes it hard to replicate?
3. Patents or IP (search for any filed patents)
4. Technical moat strength (strong/moderate/weak/none)
5. Technical risks
6. Overall tech score (1-10)

Format your response as valid JSON:
{{
    "technology_stack": ["Python", "TensorFlow", "AWS"],
    "defensibility_assessment": "Proprietary ML models provide barrier to entry",
    "patents_identified": 3,
    "technical_moat": "moderate",
    "technical_risks": ["Key person dependency", "Scaling challenges"],
    "tech_score": 7
}}
"""

    result = await run_agent(
        agent_name=TECH_EVALUATOR.name,
        prompt=prompt,
        tools=TECH_EVALUATOR.tools,
        model=TECH_EVALUATOR.model,
        system_prompt=TECH_EVALUATOR.system_prompt,
        timeout_seconds=TECH_EVALUATOR.timeout_seconds
    )

    if result.success and result.raw_output:
        parsed = parse_json_from_output(result.raw_output)
        if parsed:
            result.output = parsed

    return result


def _format_team_tech(team_analysis: Dict[str, Any]) -> str:
    """Extract technical team information."""
    lines = []
    founders = team_analysis.get("founders", [])
    for founder in founders:
        if isinstance(founder, dict):
            name = founder.get("name", "Unknown")
            role = founder.get("role", "")
            if "tech" in role.lower() or "cto" in role.lower():
                lines.append(f"- {name} ({role})")
    return "\n".join(lines) if lines else "No technical team details available"