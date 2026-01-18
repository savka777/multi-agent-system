from enum import Enum

class StateField(str, Enum):
    STARTUP_NAME = "startup_name"
    STARTUP_DESCRIPTION = "startup_description"
    FUNDING_STAGE = "funding_stage"
    RESEARCH_OUTPUTS = "research_outputs"
    ANALYSIS_OUTPUTS = "analysis_outputs"
    FULL_REPORT = "full_report"
    INVESTMENT_DECISION = "investment_decision"
    CURRENT_STAGE = "current_stage"
    ERRORS = "errors"
    RETRY_COUNT = "retry_count"

class Stage(Enum):
    INIT = "init"
    INIT_COMPLETE = "init_complete"
    RESEARCH_COMPLETE = "research_complete"
    RESEARCH_VALIDATED = "research_validated"
    ANALYSIS_COMPLETE = "analysis_complete"
    SYNTHESIS_COMPLETE = "synthesis_complete"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"

class AgentName(Enum):
      # Research agents (Layer 1)
    COMPANY_PROFILER = "company_profiler"
    MARKET_RESEARCHER = "market_researcher"
    COMPETITOR_SCOUT = "competitor_scout"
    TEAM_INVESTIGATOR = "team_investigator"
    NEWS_MONITOR = "news_monitor"

    # Analysis agents (Layer 2)
    FINANCIAL_ANALYST = "financial_analyst"
    RISK_ASSESSOR = "risk_assessor"
    TECH_EVALUATOR = "tech_evaluator"
    LEGAL_REVIEWER = "legal_reviewer"

    # Synthesis agents (Layer 3)
    REPORT_GENERATOR = "report_generator"
    DECISION_AGENT = "decision_agent"

