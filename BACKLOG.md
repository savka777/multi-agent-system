# Backlog

## Bugs

- [ ] **Fix inverted success rate calculation** (`src/workflow/routing.py:34`)
  - Current: `success_rate = total_count / success_count` (wrong)
  - Should be: `success_rate = success_count / total_count`
  - Impact: Validation always passes even when most agents fail

- [ ] **Increment retry_count in validate_research_node** (`src/workflow/nodes.py:108`)
  - `retry_count` is checked in routing but never incremented
  - Add `retry_count += 1` when validation fails and return it in state
  - Impact: Retry logic never triggers correctly

## Refactoring

- [ ] **Use enums instead of hardcoded strings** (`src/state/enums.py`)
  - `StateField` — use for `state.get()` calls (e.g., `state.get(StateField.RETRY_COUNT)`)
  - `Stage` — use for `current_stage` values (e.g., `Stage.RESEARCH_COMPLETE`)
  - `AgentName` — use for agent name lists (e.g., `AgentName.COMPANY_PROFILER`)
  - Files to update: `nodes.py`, `routing.py`, `graph.py`
