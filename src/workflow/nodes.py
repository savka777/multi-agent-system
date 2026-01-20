# Nodes = functions, our graph connects there nodes, in order for agents to 1) perfrom tasks, 2) return outputs
# and 3) update memory

from typing import Dict, Any
from state.schema import DueDiligenceState


async def init_node(state: DueDiligenceState) -> Dict[str, Any]:
    """Initialize the workflow."""
    print("Running: init_node")
    print(f"  Startup: {state.get('startup_name')}")
    return {"current_stage": "init_complete"}


async def research_node(state: DueDiligenceState) -> Dict[str, Any]:
    """Run all research agents in parallel."""
    print("Running: research_node")
    print("  Would run 5 research agents here...")
    return {
        "research_outputs": [{"agent": "stub", "success": True}],
        "current_stage": "research_complete"
    }

# conditional edge, after research is done we validate it? 
async def validate_research_node(state: DueDiligenceState) -> Dict[str, Any]:
    """Validate research completeness."""
    print("Running: validate_research_node")
    return {"current_stage": "research_validated"}

async def analysis_node(state: DueDiligenceState) -> Dict[str, Any]:
    """Run analysis agents."""
    print("Running: analysis_node")
    print("  Would run 4 analysis agents here...")
    return {
        "analysis_outputs": [{"agent": "stub", "success": True}],
        "current_stage": "analysis_complete"
    }

async def synthesis_node(state: DueDiligenceState) -> Dict[str, Any]:
    """Run synthesis agents to generate report and decision."""
    print("Running: synthesis_node")
    return {
        "full_report": "Stub report",
        "investment_decision": {"recommendation": "hold"},
        "current_stage": "synthesis_complete"
    }

async def output_node(state: DueDiligenceState) -> Dict[str, Any]:
    """Finalize output."""
    print("Running: output_node")
    print("  Workflow complete!")
    return {"current_stage": "complete"}