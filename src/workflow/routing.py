from typing import Literal
from state.schema import DueDiligenceState

def check_init_success(state : DueDiligenceState) -> Literal['success', 'failure']:
    errors = state.get('error', [])

    critical_errors = []
    for e in errors:
        if e.lower() == 'required':
            critical_errors.append(e.lower())
    
    if critical_errors:
        return 'failure'

    return 'success'

def check_research_completeness(state : DueDiligenceState) -> Literal['complete', 'incomplete', 'failed']:
    research_outputs = state.get('research_outputs', [])
    retry_counts = state.get('retry_count', 0)

    if not research_outputs:
        if retry_counts < 2: 
            return 'incomplete'
        return 'failed'
    
    success_count = sum(1 for results in research_outputs
                        if results.get('success',False))
    
    total_count = len(research_outputs)

    if total_count == 0:
        return 'failed'

    success_rate = total_count / success_count

    # need 50% to pass:
    if success_rate > 0.5:
        return 'complete'
    
    if retry_counts < 2:
        return 'incomplete'

    # to many retries:
    return 'complete'
