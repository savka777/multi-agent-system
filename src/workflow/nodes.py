# Nodes = functions, our graph connects there nodes, in order for agents to 1) perfrom tasks, 2) return outputs
# and 3) update memory

from typing import Dict, Any, List
from ..state.schema import DueDiligenceState
import time, asyncio

from ..agents.research.company_profiler import run_company_profiler
from ..agents.research.competitor_scout import run_competitor_scout
from ..agents.research.market_researcher import run_market_researcher
from ..agents.research.news_monitor import run_news_monitor
from ..agents.research.team_investigator import run_team_investigator

from ..agents.analysis.financial_analyst import run_financial_analyst
from ..agents.analysis.legal_reviewer import run_legal_reviewer
from ..agents.analysis.risk_assessor import run_risk_assessor
from ..agents.analysis.tech_evaluator import run_tech_evaluator


from ..agents.synthesis.report_generator import run_report_generator
from ..agents.synthesis.decision_agent import run_decision_agent

async def init_node(state: DueDiligenceState) -> Dict[str, Any]:
    """Initialize the workflow."""
    print("Running: init_node")
    print(f"  Startup: {state.get('startup_name')}")
    return {"current_stage": "init_complete"}

async def research_node(state: DueDiligenceState) -> Dict[str, Any]:
    """
    Run research agents with:
    - Semaphore limiting (max 2 concurrent to avoid rate limits)
    - Targeted retry (only run failed agents on retry)
    """
    # Check if this is a retry - only run failed agents
    failed_agents = state.get('failed_research_agents', [])
    existing_outputs = state.get('research_outputs', [])

    # Map agent names to their runner functions
    agent_runners = {
        "company_profiler": lambda: run_company_profiler(state['startup_name'], state['startup_description']),
        "market_researcher": lambda: run_market_researcher(state['startup_name'], state['startup_description']),
        "competitor_scout": lambda: run_competitor_scout(state['startup_name'], state['startup_description']),
        "team_investigator": lambda: run_team_investigator(state['startup_name']),
        "news_monitor": lambda: run_news_monitor(state['startup_name']),
    }

    all_agents = list(agent_runners.keys())

    # Determine which agents to run
    if failed_agents:
        agents_to_run = failed_agents
        print("\n" + "=" * 60)
        print(f"STAGE 2: RESEARCH (RETRY - {len(agents_to_run)} failed agents)")
        print("=" * 60)
    else:
        agents_to_run = all_agents
        print("\n" + "=" * 60)
        print(f"STAGE 2: RESEARCH ({len(agents_to_run)} agents, max 2 concurrent)")
        print("=" * 60)

    for name in agents_to_run:
        print(f"  Queued: {name}")

    start_time = time.time()

    # Semaphore limits concurrent execution to avoid rate limits
    semaphore = asyncio.Semaphore(2)

    async def run_with_limit(agent_name: str):
        async with semaphore:
            print(f"  RUNNING: {agent_name}")
            return await agent_runners[agent_name]()

    # Run only the agents we need
    tasks = [run_with_limit(name) for name in agents_to_run]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Start with existing successful outputs (from previous run)
    research_outputs = [o for o in existing_outputs if o.get('success')]
    errors = []
    new_failed_agents = []

    for i, result in enumerate(results):
        agent_name = agents_to_run[i]

        if isinstance(result, Exception):
            errors.append(f"{agent_name}: {str(result)}")
            research_outputs.append({
                "agent": agent_name,
                "output": None,
                "success": False,
                "error": str(result)
            })
            new_failed_agents.append(agent_name)
            print(f"  FAILED: {agent_name} - {str(result)[:50]}")

        elif not result.success:
            errors.append(f"{agent_name}: {result.error}")
            research_outputs.append({
                "agent": agent_name,
                "output": None,
                "success": False,
                "error": result.error
            })
            new_failed_agents.append(agent_name)
            print(f"  FAILED: {agent_name} - {result.error[:50] if result.error else 'Unknown'}")

        else:
            research_outputs.append({
                "agent": agent_name,
                "output": result.output,
                "raw_output": result.raw_output,
                "success": True,
                "execution_time_ms": result.execution_time_ms
            })
            print(f"  DONE: {agent_name} ({result.execution_time_ms/1000:.1f}s)")

        # Debug: Show if we got partial output even on failure
        if not result.success and result.raw_output:
            print(f"    (Has partial output: {len(result.raw_output)} chars)")

    elapsed = time.time() - start_time
    success_count = sum(1 for r in research_outputs if r.get("success"))
    total_count = len(all_agents)

    print(f"\nResearch complete: {success_count}/{total_count} agents in {elapsed:.1f}s")
    if new_failed_agents:
        print(f"  Failed agents: {', '.join(new_failed_agents)}")

    return {
        "research_outputs": research_outputs,
        "errors": errors,
        "failed_research_agents": new_failed_agents,
        "current_stage": "research_complete"
    }

# conditional edge, after research is done we validate it? 
async def validate_research_node(state: DueDiligenceState) -> Dict[str, Any]:
    print("\nValidating research completeness...")
    research_outputs = state.get('research_outputs', [])
    retry_count = state.get('retry_count',0)
    success_count = sum(1 for research in research_outputs
                        if research.get('success', False))
    total_count = len(research_outputs)
    errors = []

    if total_count > 0 and success_count / total_count < 0.5:
        errors.append(f"CRITICAL: Only {success_count}/{total_count} research agents succeeded")
        print(f"CRITICAL: Only {success_count}/{total_count} succeeded")
        retry_count += 1
    
    else:
        print(f"Validation passed: {success_count}/{total_count} succeeded")

    return {
        'current_stage': 'research_completed', 
        'errors': errors,
        'retry_count' : retry_count
    }

def _get_agent_output(outputs: List[Dict], agent_name: str) -> Any:
    """Extract a specific agent's output from the outputs list."""
    for output in outputs:
        if output.get("agent") == agent_name and output.get("success"):
            return output.get("output")
    return None

async def analysis_node(state: DueDiligenceState) -> Dict[str, Any]:
    """
    Run analysis agents.

    Some will run in parallel, but the risk assessor needs other outputs first.
    """
    print("\n" + "=" * 60)
    print("STAGE 3: ANALYSIS (4 agents)")
    print("=" * 60)

    startup_name = state["startup_name"]
    startup_description = state["startup_description"]
    research_outputs = state.get("research_outputs", [])

    # Extract specific research outputs for analysis
    company_profile = _get_agent_output(research_outputs, "company_profiler")
    market_analysis = _get_agent_output(research_outputs, "market_researcher")
    team_analysis = _get_agent_output(research_outputs, "team_investigator")

    print("  Starting: financial_analyst, tech_evaluator, legal_reviewer (parallel)")
    start_time = time.time()

    # Run first batch in parallel
    first_batch = await asyncio.gather(
        run_financial_analyst(
            company_profile=company_profile,
            market_analysis=market_analysis,
            startup_name=startup_name,
            startup_description=startup_description
        ),
        run_tech_evaluator(
            startup_name=startup_name,
            startup_description=startup_description,
            team_analysis=team_analysis
        ),
        run_legal_reviewer(
            startup_name=startup_name,
            market_analysis=market_analysis
        ),
        return_exceptions=True
    )

    analysis_outputs = []
    errors = []

    # Process first batch
    first_batch_names = ["financial_analyst", "tech_evaluator", "legal_reviewer"]
    for i, result in enumerate(first_batch):
        agent_name = first_batch_names[i]
        if isinstance(result, Exception):
            errors.append(f"{agent_name}: {str(result)}")
            analysis_outputs.append({
                "agent": agent_name, "output": None,
                "success": False, "error": str(result)
            })
            print(f"  FAILED: {agent_name}")
        elif not result.success:
            errors.append(f"{agent_name}: {result.error}")
            analysis_outputs.append({
                "agent": agent_name, "output": None,
                "success": False, "error": result.error
            })
            print(f"  FAILED: {agent_name}")
        else:
            analysis_outputs.append({
                "agent": agent_name,
                "output": result.output,
                "raw_output": result.raw_output,
                "success": True,
                "execution_time_ms": result.execution_time_ms
            })
            print(f"  DONE: {agent_name} ({result.execution_time_ms/1000:.1f}s)")

    # Now run risk assessor with ALL outputs
    print("  Starting: risk_assessor (needs other analysis)")
    risk_result = await run_risk_assessor(
        research_outputs=research_outputs,
        analysis_outputs=analysis_outputs,
        startup_name=startup_name
    )

    if isinstance(risk_result, Exception) or not risk_result.success:
        error_msg = str(risk_result) if isinstance(risk_result, Exception) else risk_result.error
        errors.append(f"risk_assessor: {error_msg}")
        analysis_outputs.append({
            "agent": "risk_assessor", "output": None,
            "success": False, "error": error_msg
        })
        print(f"  FAILED: risk_assessor")
    else:
        analysis_outputs.append({
            "agent": "risk_assessor",
            "output": risk_result.output,
            "raw_output": risk_result.raw_output,
            "success": True,
            "execution_time_ms": risk_result.execution_time_ms
        })
        print(f"  DONE: risk_assessor ({risk_result.execution_time_ms/1000:.1f}s)")

    elapsed = time.time() - start_time
    success_count = sum(1 for r in analysis_outputs if r.get("success"))
    print(f"\nAnalysis complete: {success_count}/4 agents in {elapsed:.1f}s")
    
    # update the state after node has completed... langgraph automatically consumes this.
    return {
        "analysis_outputs": analysis_outputs,
        "errors": errors,
        "current_stage": "analysis_complete"
    }

async def synthesis_node(state: DueDiligenceState) -> Dict[str, Any]:
    """
    Run synthesis agents to generate final report and decision.
    Report generator runs first, then decision agent uses the report.
    """
    print("\n" + "=" * 60)
    print("STAGE 4: SYNTHESIS (2 agents)")
    print("=" * 60)

    startup_name = state["startup_name"]
    startup_description = state["startup_description"]
    research_outputs = state.get("research_outputs", [])
    analysis_outputs = state.get("analysis_outputs", [])
    errors = []

    start_time = time.time()

    # Run report generator first
    print("  Starting: report_generator")
    report_result = await run_report_generator(
        startup_name=startup_name,
        startup_description=startup_description,
        research_outputs=research_outputs,
        analysis_outputs=analysis_outputs
    )

    full_report = None
    if isinstance(report_result, Exception) or not report_result.success:
        error_msg = str(report_result) if isinstance(report_result, Exception) else report_result.error
        errors.append(f"report_generator: {error_msg}")
        print(f"  FAILED: report_generator")
    else:
        full_report = report_result.output or report_result.raw_output
        print(f"  DONE: report_generator ({report_result.execution_time_ms/1000:.1f}s)")

    # Run decision agent with the report
    print("  Starting: decision_agent")
    risk_assessment = _get_agent_output(analysis_outputs, "risk_assessor")

    decision_result = await run_decision_agent(
        startup_name=startup_name,
        full_report=full_report[:4000] if full_report else "",
        risk_assessment=risk_assessment,
        research_outputs=research_outputs,
        analysis_outputs=analysis_outputs
    )

    investment_decision = None
    if isinstance(decision_result, Exception) or not decision_result.success:
        error_msg = str(decision_result) if isinstance(decision_result, Exception) else decision_result.error
        errors.append(f"decision_agent: {error_msg}")
        print(f"  FAILED: decision_agent")
    else:
        investment_decision = decision_result.output
        print(f"  DONE: decision_agent ({decision_result.execution_time_ms/1000:.1f}s)")

    elapsed = time.time() - start_time
    success_count = (1 if full_report else 0) + (1 if investment_decision else 0)
    print(f"\nSynthesis complete: {success_count}/2 agents in {elapsed:.1f}s")

    return {
        "full_report": full_report,
        "investment_decision": investment_decision,
        "errors": errors,
        "current_stage": "synthesis_complete"
    }

async def output_node(state: DueDiligenceState) -> Dict[str, Any]:
    print("\n" + "=" * 60)
    print("STAGE 5: OUTPUT")
    print("=" * 60)

    errors = state.get("errors", [])
    full_report = state.get("full_report")
    investment_decision = state.get("investment_decision")

    # Determine final status
    if full_report and investment_decision:
        status = "complete"
        print("Workflow completed successfully!")
    elif full_report or investment_decision:
        status = "partial"
        print("Workflow completed with partial results")
    else:
        status = "failed"
        print("Workflow failed")

    if errors:
        print(f"Total errors encountered: {len(errors)}")

    return {
        "current_stage": status
    }