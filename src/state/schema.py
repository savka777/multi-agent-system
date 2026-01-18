from typing import Annotated, Optional, List, TypedDict
from operator import add
from .enums import StateField

class DueDiligenceState(TypedDict):
    startup_name : str
    startup_description : str
    funding_state: Optional[str]
    research_outputs : Annotated[List[str], add] # what happens when 2 or more agents try to write here? Needs Reducer
    analysis_outputs : Annotated[List[str], add]
    full_report: Optional[str]
    investment_decision : Optional[dict]
    current_stage : str
    error : Annotated[List[str], add]
    retry_count : int

def create_initial_state(startup_name: str, 
                         startup_description: str,
                         funding_stage: Optional[str]=None):
    # Returns a DueDiligenceState with empty lists and sensible defaults
    initial_state = DueDiligenceState(
        startup_name=startup_name,
        startup_description=startup_description,
        funding_stage=funding_stage,
        research_outputs=[],
        analysis_outputs=[],
        full_report=[],
        investment_decision={},
        current_stage="",
        error=[],
        retry_count=0
    )
    return initial_state



