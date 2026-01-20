from langgraph.graph import StateGraph, END
from ..state.schema import DueDiligenceState
from .nodes import (
    init_node,
    research_node,
    validate_research_node,
    analysis_node,
    synthesis_node,
    output_node,
)
from .routing import check_init_success, check_research_completeness

from typing import Optional

def create_due_diligence_graph() -> StateGraph:

    workflow = StateGraph(DueDiligenceState)

    # Add nodes
    workflow.add_node("init", init_node)
    workflow.add_node("research", research_node)
    workflow.add_node("validate_research", validate_research_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("output", output_node)

    # Set entry point
    workflow.set_entry_point("init")

    # Conditional: init -> research or output
    workflow.add_conditional_edges(
        "init",
        check_init_success,
        {"success": "research", "failed": "output"}
    )

    # Simple: research -> validate
    workflow.add_edge("research", "validate_research")

    # Conditional: validate -> analysis, retry, or fail
    workflow.add_conditional_edges(
        "validate_research",
        check_research_completeness,
        {"complete": "analysis", "incomplete": "research", "failed": "output"}
    )

    # Simple edges for rest of workflow
    workflow.add_edge("analysis", "synthesis")
    workflow.add_edge("synthesis", "output")
    workflow.add_edge("output", END)

    return workflow

def compile_workflow():
    graph = create_due_diligence_graph()
    return graph.compile()

compiled_graph = None

def get_compiled_graph():
    global compiled_graph
    if compiled_graph is None:
        compiled_graph = compile_workflow()
    return compiled_graph

async def run_due_diligence(startup_name : str,
                            startup_descrption: str,
                            funding_stage : Optional[str]=None ) -> DueDiligenceState:
    
    from ..state.schema import create_initial_state

    initial_state = create_initial_state(startup_name=startup_name, 
                                         startup_description=startup_descrption,
                                         funding_stage=funding_stage)

    graph = get_compiled_graph()
    print(graph.get_graph().draw_ascii())

    final_state = await graph.ainvoke(initial_state)
    return final_state
