import asyncio
import time
import json
from typing import List, Optional, Any
from pydantic import BaseModel

from ..config.settings import get_model_id

class AgentResult(BaseModel):
    success: bool
    output: Optional[Any] = None
    raw_output: Optional[str] = None
    error: Optional[str] = None
    agent_name: str
    execution_time_ms: int


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

    try:
        from claude_agent_sdk import (
            query, 
            ClaudeAgentOptions, 
            AssistantMessage,
            ResultMessage, 
            TextBlock,
        )

        options = ClaudeAgentOptions(
            model=model_id,
            allowed_tools=tools if tools else [],
            permission_mode="bypassPermissions",
            system_prompt=system_prompt,
            cwd="/tmp"
        )

        output_text = ""

        # main agent function:
        async def execute():
            nonlocal output_text
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            output_text += block.text # accumalate chunks 
                elif isinstance(message, ResultMessage):
                    if message.result and not output_text:
                        output_text = message.result

        # await the results: if timeout, throw expcetion and log
        await asyncio.wait_for(execute(), timeout=timeout_seconds)

        elapsed_ms = int((time.time() - start_time) * 1000)
        return AgentResult(
            success=True,
            output=None,
            raw_output=output_text,
            error=None,
            agent_name=agent_name,
            execution_time_ms=elapsed_ms
        )

    except asyncio.TimeoutError:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return AgentResult(
            success=False,
            output=None,
            raw_output=None,
            error=f"Timeout after {timeout_seconds}s",
            agent_name=agent_name,
            execution_time_ms=elapsed_ms
        )

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return AgentResult(
            success=False,
            output=None,
            raw_output=None,
            error=str(e),
            agent_name=agent_name,
            execution_time_ms=elapsed_ms
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