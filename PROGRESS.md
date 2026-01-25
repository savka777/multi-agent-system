# Progress Log

## Session: 2026-01-25 ~19:00

### Summary
Production-hardening the multi-agent due diligence system. Focused on timeout issues, rate limiting, logging, and retry logic.

---

### Completed This Session

#### 1. Production Diagnostics (`src/agents/base.py`)
- Added `ExecutionTrace` dataclass that tracks execution state and survives timeouts
- Tracks: turns, tool_calls, tokens_input, tokens_output, last_activity, partial_output
- Enhanced `AgentResult` with diagnostic fields
- Console now shows real-time agent activity:
  ```
  [market_researcher] t=2.7s turn=3 AssistantMessage
    -> Tool: WebSearch
       Query: Stripe market opportunity TAM SAM payments industry 2026
  ```

#### 2. Semaphore Rate Limiting (`src/workflow/nodes.py`)
- Added `asyncio.Semaphore(2)` to research_node
- Only 2 agents run concurrently (was 5)
- Prevents API rate limit errors

#### 3. Targeted Retry Logic (`src/workflow/nodes.py`)
- Added `failed_research_agents` tracking in state
- On retry, only re-runs agents that failed
- Preserves successful outputs from previous run

#### 4. Fixed State Schema (`src/state/schema.py`)
- Added `failed_research_agents: List[str]` field
- Fixed `error` → `errors` naming inconsistency
- Fixed type annotations (`List[Dict[str, Any]]` not `List[str]`)
- Added proper reducer for failed_agents

#### 5. Simplified Agent Prompts (`src/agents/research/*.py`)
- Each agent has ONE clear task
- Startup name at top of prompt
- Instructions: "Use 1-2 web searches maximum"
- Clear JSON output format

---

### Files Modified
```
src/agents/base.py                        # ExecutionTrace, AgentResult diagnostics
src/workflow/nodes.py                     # Semaphore, targeted retry
src/state/schema.py                       # failed_research_agents, type fixes
src/agents/research/company_profiler.py   # Simplified prompt
src/agents/research/market_researcher.py  # Simplified prompt
src/agents/research/competitor_scout.py   # Simplified prompt
src/agents/research/team_investigator.py  # Simplified prompt
src/agents/research/news_monitor.py       # Simplified prompt
```

---

### Current Blocker: claude_agent_sdk Cleanup Crash

**Error:**
```
[company_profiler] t=0.9s turn=3 ResultMessage
Fatal error in message reader: Command failed with exit code 1 (exit code: 1)
```

**What's happening:**
1. Agent completes successfully (reaches `ResultMessage` in ~0.7s)
2. Agent responds from memory (no tool calls) because Haiku knows Stripe
3. SDK subprocess crashes during cleanup phase
4. Crash is raised as exception → marks result as `success=False`

**Key insight:** The agent DID complete. The crash happens AFTER `ResultMessage` during SDK cleanup. Output may be captured in `trace.partial_output` but the exception overwrites success status.

**Debug line added to nodes.py:**
```python
if not result.success and result.raw_output:
    print(f"    (Has partial output: {len(result.raw_output)} chars)")
```

---

### Next Steps

1. **Test with obscure company** - Forces tool use, may avoid the no-tool cleanup bug
2. **Check if partial_output has data** - The debug line will show this
3. **Consider catching cleanup errors** - If ResultMessage received, treat as success
4. **Check claude_agent_sdk version** - May be a known bug
5. **Alternative:** Wrap SDK call to ignore post-completion crashes

---

### What's Working
- [x] Semaphore limiting (max 2 concurrent)
- [x] Targeted retry (only failed agents)
- [x] Diagnostic logging (turns, tools, timing)
- [x] Partial output capture on timeout
- [x] Simplified focused prompts
- [ ] Full end-to-end completion (blocked by SDK crash)
