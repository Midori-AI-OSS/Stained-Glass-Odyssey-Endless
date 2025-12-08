# Update Chat Room Implementation for Agent Framework

## Task ID
`c0f04e25-update-chat-room`

## Priority
Medium

## Status
WIP

## Description
Update `autofighter/rooms/chat.py` to use the Agent Framework's `AgentPayload` and `AgentResponse` instead of the custom streaming interface.

## Context
Current implementation in `autofighter/rooms/chat.py`:
- Uses `load_llm()` with custom streaming interface
- Sends raw JSON payload as prompt
- Manually concatenates streamed chunks
- No structured payload/response format

Agent Framework provides:
- `AgentPayload` structured input
- `AgentResponse` structured output
- Built-in streaming support
- System context and memory management

## Objectives
1. Replace `load_llm()` with `load_agent()`
2. Convert JSON prompt to `AgentPayload`
3. Use `agent.invoke()` or `agent.stream()`
4. Extract response from `AgentResponse`
5. Maintain existing functionality

## Implementation Steps

### Step 1: Update Imports
```python
from llms.agent_loader import load_agent
from midori_ai_agent_base import AgentPayload
```

### Step 2: Update resolve() Method
```python
async def resolve(self, party: Party, data: dict[str, Any]) -> dict[str, Any]:
    message = data.get("message", "")
    party_data = [_serialize(p) for p in party.members]
    
    # Load agent
    agent = await load_agent()
    
    # Create structured payload
    payload = AgentPayload(
        user_message=message,
        thinking_blob="",
        system_context=f"You are a character in an auto-battler game. Party: {json.dumps(party_data)}",
        user_profile={},
        tools_available=[],
        session_id=f"chat-{party.id or 'unknown'}",
    )
    
    # Get response
    if await agent.supports_streaming():
        reply = ""
        async for chunk in agent.stream(payload):
            reply += chunk
    else:
        response = await agent.invoke(payload)
        reply = response.response
    
    # Rest of method stays the same...
```

### Step 3: Test
```bash
cd backend
uv run pytest tests/ -k chat -v
```

## Acceptance Criteria
- [ ] Chat room uses `load_agent()` instead of `load_llm()`
- [ ] Uses `AgentPayload` for input
- [ ] Uses `AgentResponse` or streaming for output
- [ ] All existing functionality preserved
- [ ] Tests pass
- [ ] Linting passes

## Dependencies
- Requires: `32e92203-migrate-llm-loader.md`

## References
- Current: `backend/autofighter/rooms/chat.py`
- Framework: [midori-ai-agent-base docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-base/docs.md)
