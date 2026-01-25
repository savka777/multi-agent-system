import json
from typing import Dict, Any, List
from ..base import run_agent, AgentResult
from ...config.agent_configs import REPORT_GENERATOR


async def run_report_generator(
    startup_name: str,
    startup_description: str,
    research_outputs: List[Dict[str, Any]],
    analysis_outputs: List[Dict[str, Any]]
) -> AgentResult:

    # Compile all findings into context
    context = _compile_findings(
        startup_name, 
        startup_description,
        research_outputs, 
        analysis_outputs
    )

    prompt = f"""Generate a comprehensive due diligence report:

{context}

Create a professional Markdown report with these sections:

# Report: {startup_name}

## Executive Summary
2-3 paragraph overview of the opportunity

## Company Overview
Profile, products, funding history

## Market Opportunity
TAM/SAM/SOM, growth trends, timing

## Competitive Landscape
Competitors, positioning, advantages

## Team Assessment
Founders, executives, expertise

## Financial Analysis
Funding, runway, revenue model

## Technical Evaluation
Tech stack, moat, patents

## Risk Assessment
Top risks with severity and mitigation

## Conclusion
Summary of key findings

Make the report professional and data-driven.
"""

    result = await run_agent(
        agent_name=REPORT_GENERATOR.name,
        prompt=prompt,
        tools=REPORT_GENERATOR.tools,
        model=REPORT_GENERATOR.model,
        system_prompt=REPORT_GENERATOR.system_prompt,
        timeout_seconds=REPORT_GENERATOR.timeout_seconds
    )

    # For report generator, output IS the raw text
    if result.success:
        result.output = result.raw_output

    return result

def _compile_findings(
    startup_name: str,
    startup_description: str,
    research_outputs: List[Dict[str, Any]],
    analysis_outputs: List[Dict[str, Any]]
) -> str:
    """Compile all findings into structured context."""
    sections = []
    sections.append(f"# Startup: {startup_name}")
    sections.append(f"Description: {startup_description}\n")

    sections.append("## RESEARCH FINDINGS\n")
    for output in research_outputs:
        agent = output.get("agent", "Unknown")
        success = output.get("success", False)
        data = output.get("output")
        sections.append(f"### {agent.replace('_', ' ').title()}")
        if success and data:
            sections.append(json.dumps(data, indent=2, default=str)[:1500])
        else:
            sections.append("*Data not available*")
        sections.append("")

    sections.append("## ANALYSIS FINDINGS\n")
    for output in analysis_outputs:
        agent = output.get("agent", "Unknown")
        success = output.get("success", False)
        data = output.get("output")
        sections.append(f"### {agent.replace('_', ' ').title()}")
        if success and data:
            sections.append(json.dumps(data, indent=2, default=str)[:1500])
        else:
            sections.append("*Data not available*")
        sections.append("")

    return "\n".join(sections)