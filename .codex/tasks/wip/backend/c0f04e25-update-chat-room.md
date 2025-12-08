# Update Chat Room Implementation for Agent Framework

## Task ID
`c0f04e25-update-chat-room`

## Priority
Medium

## Status
COMPLETED

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

## Implementation Summary

### Changes Made
1. **Updated imports**: Replaced `llms.loader` imports with `llms.agent_loader`
2. **Removed ModelName dependency**: Agent framework handles model selection internally
3. **Added configuration support**: 
   - Reads `lrm_model`, `lrm_backend`, `lrm_api_url`, `lrm_api_key` from options
   - Sets environment variables for API configuration
4. **Updated resolve() method**:
   - Load agent using `load_agent()` with backend and model parameters
   - Create structured `AgentPayload` with party context in `system_context`
   - Support both streaming and non-streaming responses
   - Maintain all existing voice, party data, and return structure
5. **Updated test**: 
   - Created `FakeAgent` mock for agent framework interface
   - Mocked `midori_ai_agent_base.AgentPayload`
   - Fixed Stats and MapNode initialization

### Code Changes
- `backend/autofighter/rooms/chat.py`: 31 lines changed (imports + resolve method)
- `backend/tests/test_chat_room.py`: 61 lines changed (new mock + test structure)

## Acceptance Criteria
- [x] Chat room uses `load_agent()` instead of `load_llm()`
- [x] Uses `AgentPayload` for input
- [x] Uses `AgentResponse` or streaming for output
- [x] All existing functionality preserved
- [x] Tests pass (8/8 tests passing)
- [x] Linting passes (7 fixes applied, 0 remaining)

## Completion Notes
- Task completed successfully with minimal, surgical changes
- Configuration options are respected (model, backend, API settings)
- Both streaming and non-streaming agent responses supported
- Test validates model selection and message passing
- All linting checks pass
- Ready for review

## Dependencies
- Requires: `32e92203-migrate-llm-loader.md` (agent_loader.py exists and functional)

## References
- Modified: `backend/autofighter/rooms/chat.py`
- Modified: `backend/tests/test_chat_room.py`
- Framework: [midori-ai-agent-base docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-base/docs.md)
