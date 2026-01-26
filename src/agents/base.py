import asyncio
import time
import json
import traceback
import logging
import sys
from typing import List, Optional, Any
from pydantic import BaseModel
from dataclasses import dataclass, field

from ..config.settings import get_model_id

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('agent')


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
    # Enhanced error diagnostics
    error_type: Optional[str] = None  # Exception class name
    error_traceback: Optional[str] = None  # Full traceback for debugging


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

    # Capture stderr from CLI subprocess - defined outside try so it survives exceptions
    stderr_lines: List[str] = []

    try:
        from claude_agent_sdk import (
            query,
            ClaudeAgentOptions,
            AssistantMessage,
            ResultMessage,
            TextBlock,
            ToolUseBlock
        )

        # Callback to capture stderr from the CLI subprocess
        def stderr_callback(line: str):
            stderr_lines.append(line)
            # Also log immediately so we see errors in real-time
            if "error" in line.lower() or "exception" in line.lower() or "traceback" in line.lower():
                logger.error(f"[{agent_name}] CLI stderr: {line}")
            else:
                logger.debug(f"[{agent_name}] CLI stderr: {line}")

        options = ClaudeAgentOptions(
            model=model_id,
            allowed_tools=tools if tools else [],
            permission_mode="bypassPermissions",
            system_prompt=system_prompt,
            cwd="/tmp",
            stderr=stderr_callback,  # Capture actual stderr from CLI
            extra_args={"debug-to-stderr": None},  # Enable CLI debug mode
        )

        async def execute():
            async for message in query(prompt=prompt, options=options):
                elapsed = time.time() - start_time
                message_type = type(message).__name__
                trace.log_turn(message_type, elapsed)

                # Log every turn
                logger.info(f"[{agent_name}] t={elapsed:.1f}s turn={trace.turns} {message_type}")

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
                            logger.debug(f"[{agent_name}] Tool: {block.name}")
                            # Log what's being searched/fetched
                            if 'query' in tool_input:
                                logger.debug(f"[{agent_name}]   Query: {tool_input['query'][:80]}")
                            elif 'url' in tool_input:
                                logger.debug(f"[{agent_name}]   URL: {tool_input['url'][:80]}")

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
        logger.info(
            f"[{agent_name}] COMPLETE: {trace.turns} turns, {len(trace.tool_calls)} tools, "
            f"{trace.tokens_input}+{trace.tokens_output} tokens"
        )

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
        logger.warning(f"[{agent_name}] TIMEOUT: {timeout_context}")

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
        exc_type = type(e).__name__
        exc_traceback = traceback.format_exc()

        # Include captured stderr in error message
        stderr_output = "\n".join(stderr_lines) if stderr_lines else "No stderr captured"
        full_error = f"{exc_type}: {str(e)}"
        if stderr_lines:
            full_error += f"\n\nCLI stderr:\n{stderr_output}"

        # Log full error details
        logger.error(
            f"[{agent_name}] FAILED: {exc_type}: {str(e)}\n"
            f"CLI stderr ({len(stderr_lines)} lines):\n{stderr_output}\n"
            f"Traceback:\n{exc_traceback}"
        )

        return AgentResult(
            success=False,
            output=None,
            raw_output=trace.partial_output if trace.partial_output else None,
            error=full_error,
            error_type=exc_type,
            error_traceback=exc_traceback,
            agent_name=agent_name,
            execution_time_ms=elapsed_ms,
            turns=trace.turns,
            tool_calls=trace.tool_calls,
            tokens_input=trace.tokens_input,
            tokens_output=trace.tokens_output,
        )
    

def parse_json_from_output(output: str, agent_name: str = "unknown") -> Optional[dict]:
    """
    Parse JSON from agent output with detailed error logging.

    Tries three strategies:
    1. Direct JSON parse
    2. Extract from markdown code blocks
    3. Find JSON object in text

    Returns None and logs warnings if all strategies fail.
    """
    if not output:
        logger.warning(f"[{agent_name}] JSON parse failed: empty output")
        return None

    errors = []  # Collect all parsing errors for debugging

    # Strategy 1: Try direct JSON parse
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        errors.append(f"Direct parse: {e.msg} at position {e.pos}")

    # Strategy 2: Try to extract from markdown code block
    import re
    json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    matches = re.findall(json_pattern, output)
    for i, match in enumerate(matches):
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError as e:
            errors.append(f"Code block {i}: {e.msg} at position {e.pos}")

    # Strategy 3: Try to find JSON object in text
    start_idx = output.find('{')
    end_idx = output.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(output[start_idx:end_idx + 1])
        except json.JSONDecodeError as e:
            errors.append(f"Extracted object: {e.msg} at position {e.pos}")

    # All strategies failed - log details
    output_preview = output[:200] + "..." if len(output) > 200 else output
    logger.warning(
        f"[{agent_name}] JSON parse failed after 3 strategies:\n"
        f"  Errors: {errors}\n"
        f"  Output preview: {output_preview}"
    )
    return None