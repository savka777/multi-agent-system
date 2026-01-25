from typing import Annotated, Optional, List, Dict, Any, TypedDict
from operator import add
from .enums import StateField


def replace_list(old: List, new: List) -> List:
    """Reducer that replaces the list entirely (for failed_agents tracking)."""
    return new


class DueDiligenceState(TypedDict):
    startup_name: str
    startup_description: str
    funding_stage: Optional[str]

    # Agent outputs - stored as dicts, use add reducer to accumulate
    research_outputs: Annotated[List[Dict[str, Any]], add]
    analysis_outputs: Annotated[List[Dict[str, Any]], add]

    # Synthesis outputs
    full_report: Optional[str]
    investment_decision: Optional[Dict]

    # Workflow tracking
    current_stage: str
    errors: Annotated[List[str], add]
    retry_count: int

    # Failed agents tracking - replaced each run, not accumulated
    failed_research_agents: Annotated[List[str], replace_list]


def create_initial_state(
    startup_name: str,
    startup_description: str,
    funding_stage: Optional[str] = None
) -> DueDiligenceState:
    """Create initial state with empty lists and sensible defaults."""
    return DueDiligenceState(
        startup_name=startup_name,
        startup_description=startup_description,
        funding_stage=funding_stage,
        research_outputs=[],
        analysis_outputs=[],
        full_report=None,
        investment_decision=None,
        current_stage="",
        errors=[],
        retry_count=0,
        failed_research_agents=[],
    )



