from dataclasses import dataclass
from typing import List

@dataclass
class AgentConfig:
    name: str
    model: str
    tools: List[str]
    timeout_seconds: int
    system_prompt: str

# =============================================================================
# LAYER 1: RESEARCH AGENTS (5 agents)
# =============================================================================

COMPANY_PROFILER = AgentConfig(
    name="company_profiler",
    model="haiku",
    tools=["WebSearch", "WebFetch"],
    timeout_seconds=90,
    system_prompt="""You are a company research specialist. Research companies thoroughly and return structured data about their business, founding, and operations."""
)

MARKET_RESEARCHER = AgentConfig(
    name="market_researcher",
    model="haiku",
    tools=["WebSearch", "WebFetch"],
    timeout_seconds=90,
    system_prompt="""You are a market research analyst. Analyze market opportunities, TAM/SAM/SOM, trends, and competitive landscape."""
)

COMPETITOR_SCOUT = AgentConfig(
    name="competitor_scout",
    model="haiku",
    tools=["WebSearch", "WebFetch"],
    timeout_seconds=90,
    system_prompt="""You are a competitive intelligence specialist. Identify and analyze competitors, their strengths, weaknesses, and market positioning."""
)

TEAM_INVESTIGATOR = AgentConfig(
    name="team_investigator",
    model="haiku",
    tools=["WebSearch", "WebFetch"],
    timeout_seconds=90,
    system_prompt="""You are a team research specialist. Research founders and key team members, their backgrounds, experience, and track records."""
)

NEWS_MONITOR = AgentConfig(
    name="news_monitor",
    model="haiku",
    tools=["WebSearch", "WebFetch"],
    timeout_seconds=90,
    system_prompt="""You are a news analyst. Find recent news, press releases, and media coverage about companies."""
)

# =============================================================================
# LAYER 2: ANALYSIS AGENTS (4 agents)
# =============================================================================

FINANCIAL_ANALYST = AgentConfig(
    name="financial_analyst",
    model="sonnet",
    tools=[],
    timeout_seconds=120,
    system_prompt="""You are a financial analyst. Analyze financial data, funding history, burn rate, and financial health indicators."""
)

RISK_ASSESSOR = AgentConfig(
    name="risk_assessor",
    model="haiku",
    tools=[],
    timeout_seconds=120,
    system_prompt="""You are a risk assessment specialist. Identify and evaluate business, market, technical, and regulatory risks."""
)

TECH_EVALUATOR = AgentConfig(
    name="tech_evaluator",
    model="sonnet",
    tools=[],
    timeout_seconds=120,
    system_prompt="""You are a technology evaluator. Assess technical architecture, innovation, defensibility, and scalability."""
)

LEGAL_REVIEWER = AgentConfig(
    name="legal_reviewer",
    model="haiku",
    tools=[],
    timeout_seconds=90,
    system_prompt="""You are a legal analyst. Identify potential legal issues, regulatory concerns, and compliance requirements."""
)

# =============================================================================
# LAYER 3: SYNTHESIS AGENTS (2 agents)
# =============================================================================

REPORT_GENERATOR = AgentConfig(
    name="report_generator",
    model="sonnet",
    tools=[],
    timeout_seconds=180,
    system_prompt="""You are a report writer. Synthesize research and analysis into comprehensive, well-structured due diligence reports."""
)

DECISION_AGENT = AgentConfig(
    name="decision_agent",
    model="opus",
    tools=[],
    timeout_seconds=180,
    system_prompt="""You are an investment decision advisor. Synthesize all available information to provide investment recommendations with confidence levels and key factors."""
)

# =============================================================================
# AGENT GROUPS
# =============================================================================

RESEARCH_AGENTS = [
    COMPANY_PROFILER,
    MARKET_RESEARCHER,
    COMPETITOR_SCOUT,
    TEAM_INVESTIGATOR,
    NEWS_MONITOR,
]

ANALYSIS_AGENTS = [
    FINANCIAL_ANALYST,
    RISK_ASSESSOR,
    TECH_EVALUATOR,
    LEGAL_REVIEWER,
]

SYNTHESIS_AGENTS = [
    REPORT_GENERATOR,
    DECISION_AGENT,
]

ALL_AGENTS = RESEARCH_AGENTS + ANALYSIS_AGENTS + SYNTHESIS_AGENTS