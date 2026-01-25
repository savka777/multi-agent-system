import asyncio
import time
import json
from typing import List, Optional, Any
from pydantic import BaseModel
from dataclasses import dataclass, field

from ..config.settings import get_model_id


@dataclass
class ExecutionTrace:
    """Tracks execution state - survives timeout for debugging."""
    turns: int = 0
    tool_calls: List[str] = field(default_factory=list)
    tokens_input: int = 0
    tokens_output: int = 0
    last_activity: str = "initialized"
    last_activity_time: float = 0.0
    partial_output: str = ""

    def log_turn(self, message_type: str, elapsed: float):
        self.turns += 1
        self.last_activity = f"turn_{self.turns}_{message_type}"
        self.last_activity_time = elapsed

    def log_tool(self, tool_name: str, tool_input: dict, elapsed: float):
        self.tool_calls.append(f"{tool_name}({json.dumps(tool_input)[:100]})")
        self.last_activity = f"tool_call:{tool_name}"
        self.last_activity_time = elapsed

    def log_tokens(self, input_tokens: int, output_tokens: int):
        self.tokens_input += input_tokens
        self.tokens_output += output_tokens

    def timeout_summary(self) -> str:
        return (
            f"Timed out during '{self.last_activity}' at t={self.last_activity_time:.1f}s | "
            f"turns={self.turns} | tools={len(self.tool_calls)} | "
            f"tokens_in={self.tokens_input} tokens_out={self.tokens_output}"
        )


class AgentResult(BaseModel):
    success: bool
    output: Optional[Any] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None
    agent_name: str
    execution_time_ms: int
    # Production diagnostics
    turns: int = 0
    tool_calls: List[str] = []
    tokens_input: int = 0
    tokens_output: int = 0
    timeout_context: Optional[str] = None  # What was happening when it timed out


async def run_agent(
    agent_name: str,
    prompt: str,
    tools: Optional[List[str]] = None,
    model: str = "sonnet",
    system_prompt: Optional[str] = None,
    timeout_seconds: int = 60
) -> AgentResult:
    start_time = time.time()
    model_id = get_model_id(model)

    # Track state OUTSIDE execute() so we have it on timeout
    trace = ExecutionTrace()

    try:
        from claude_agent_sdk import (
            query,
            ClaudeAgentOptions,
            AssistantMessage,
            ResultMessage,
            TextBlock,
            ToolUseBlock
        )

        options = ClaudeAgentOptions(
            model=model_id,
            allowed_tools=tools if tools else [],
            permission_mode="bypassPermissions",
            system_prompt=system_prompt,
            cwd="/tmp"
        )

        async def execute():
            async for message in query(prompt=prompt, options=options):
                elapsed = time.time() - start_time
                message_type = type(message).__name__
                trace.log_turn(message_type, elapsed)

                # Log every turn
                print(f"  [{agent_name}] t={elapsed:.1f}s turn={trace.turns} {message_type}")

                if isinstance(message, AssistantMessage):
                    # Extract token usage if available
                    if hasattr(message, 'usage') and message.usage:
                        trace.log_tokens(
                            getattr(message.usage, 'input_tokens', 0),
                            getattr(message.usage, 'output_tokens', 0)
                        )

                    for block in message.content:
                        if isinstance(block, TextBlock):
                            trace.partial_output += block.text
                        elif isinstance(block, ToolUseBlock):
                            tool_input = getattr(block, 'input', {})
                            trace.log_tool(block.name, tool_input, elapsed)
                            print(f"    -> Tool: {block.name}")
                            # Log what's being searched/fetched
                            if 'query' in tool_input:
                                print(f"       Query: {tool_input['query'][:80]}")
                            elif 'url' in tool_input:
                                print(f"       URL: {tool_input['url'][:80]}")

                elif isinstance(message, ResultMessage):
                    # Extract final token usage if available
                    if hasattr(message, 'usage') and message.usage:
                        trace.log_tokens(
                            getattr(message.usage, 'input_tokens', 0),
                            getattr(message.usage, 'output_tokens', 0)
                        )
                    if message.result and not trace.partial_output:
                        trace.partial_output = message.result

        # Execute with timeout
        await asyncio.wait_for(execute(), timeout=timeout_seconds)

        elapsed_ms = int((time.time() - start_time) * 1000)
        print(f"  [{agent_name}] COMPLETE: {trace.turns} turns, {len(trace.tool_calls)} tools, "
              f"{trace.tokens_input}+{trace.tokens_output} tokens")

        return AgentResult(
            success=True,
            output=None,
            raw_output=trace.partial_output,
            error=None,
            agent_name=agent_name,
            execution_time_ms=elapsed_ms,
            turns=trace.turns,
            tool_calls=trace.tool_calls,
            tokens_input=trace.tokens_input,
            tokens_output=trace.tokens_output,
        )

    except asyncio.TimeoutError:
        elapsed_ms = int((time.time() - start_time) * 1000)
        timeout_context = trace.timeout_summary()
        print(f"  [{agent_name}] TIMEOUT: {timeout_context}")

        return AgentResult(
            success=False,
            output=None,
            raw_output=trace.partial_output if trace.partial_output else None,
            error=f"Timeout after {timeout_seconds}s",
            agent_name=agent_name,
            execution_time_ms=elapsed_ms,
            turns=trace.turns,
            tool_calls=trace.tool_calls,
            tokens_input=trace.tokens_input,
            tokens_output=trace.tokens_output,
            timeout_context=timeout_context,
        )

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return AgentResult(
            success=False,
            output=None,
            raw_output=trace.partial_output if trace.partial_output else None,
            error=str(e),
            agent_name=agent_name,
            execution_time_ms=elapsed_ms,
            turns=trace.turns,
            tool_calls=trace.tool_calls,
            tokens_input=trace.tokens_input,
            tokens_output=trace.tokens_output,
        )
    

def parse_json_from_output(output: str) -> Optional[dict]:
    if not output:
        return None

    # Try direct JSON parse
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        pass

    # Try to extract from markdown code block
    import re
    json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    matches = re.findall(json_pattern, output)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Try to find JSON object in text
    start_idx = output.find('{')
    end_idx = output.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(output[start_idx:end_idx + 1])
        except json.JSONDecodeError:
            pass

    return None