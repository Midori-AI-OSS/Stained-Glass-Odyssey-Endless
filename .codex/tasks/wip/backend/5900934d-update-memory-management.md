# Update Memory Management Integration

## Task ID
`5900934d-update-memory-management`

## Priority
Medium

## Status
WIP

## CODER NOTES (2025-12-14)

**Current Assessment**: This task is blocked by the chat room redesign task (c0f04e25-update-chat-room). Memory management integration requires a clear understanding of where and how agents will be used.

**Agent Framework Memory Features Available**:
- `memory` field in AgentPayload (list of MemoryEntryData)
- Structured conversation history support
- Compatible with midori-ai-agent-context-manager for persistence

**Simple Implementation Path** (if chat room redesign deferred):
1. Add memory field to existing agent calls in routes/config.py test endpoint
2. Store last N messages in session/party object
3. Convert to MemoryEntryData format when calling agent

**Complex Implementation Path** (requires chat room redesign):
1. Per-character agent with persistent memory
2. Vector storage for long-term context
3. Context manager for conversation threads
4. Event-driven memory updates

**Recommendation**: Keep in WIP until chat room architectural decisions are made. Consider implementing simple path first for proof-of-concept.

**Dependencies**:
- Blocked by: c0f04e25-update-chat-room (architectural design)
- Optional: midori-ai-agent-context-manager package (not yet in pyproject.toml)
- Optional: midori-ai-vector-manager package (not yet in pyproject.toml)

---

## Description
Integrate the Agent Framework's memory management features with AutoFighter's existing memory systems. The framework provides a `memory` field in `AgentPayload` and integrates with `midori-ai-agent-context-manager`.

## Context
Current state:
- `routes/players.py` mentions `lrm_memory` field
- Character stats exclude `lrm_memory` from serialization
- No structured conversation history

Agent Framework provides:
- `memory` field in `AgentPayload` (list of `MemoryEntryData`)
- `midori-ai-agent-context-manager` for persistence
- Structured conversation history

## Objectives
1. Review current `lrm_memory` usage
2. Integrate `memory` field in agent calls
3. Consider using `midori-ai-agent-context-manager`
4. Maintain conversation context in chat room
5. Add memory to player characters if needed

## Implementation Steps

### Step 1: Review Current Usage
```bash
cd backend
grep -rn "lrm_memory" . --include="*.py" | grep -v ".venv"
```

### Step 2: Add Memory to Chat Room
```python
# In chat.py
from midori_ai_agent_base import MemoryEntryData

async def resolve(self, party: Party, data: dict[str, Any]):
    # Load previous conversation from party or session
    memory = []
    if hasattr(party, 'chat_history'):
        for entry in party.chat_history[-10:]:  # Last 10 messages
            memory.append(MemoryEntryData(
                role=entry['role'],
                content=entry['content'],
            ))
    
    payload = AgentPayload(
        user_message=message,
        memory=memory,  # Add conversation history
        # ... other fields
    )
    
    response = await agent.invoke(payload)
    
    # Save to history
    if not hasattr(party, 'chat_history'):
        party.chat_history = []
    party.chat_history.append({'role': 'user', 'content': message})
    party.chat_history.append({'role': 'assistant', 'content': response.response})
```

### Step 3: Consider Context Manager Integration
```python
# Optional: Use persistent memory
from midori_ai_agent_context_manager import MemoryStore

memory_store = MemoryStore(agent_id=f"chat-{party.id}")
await memory_store.load(f"data/chat_memory/{party.id}.json")

# Convert to AgentPayload format
memory = [
    MemoryEntryData(role=e.role, content=e.content)
    for e in memory_store.entries[-10:]
]
```

## Acceptance Criteria
- [ ] Current memory usage reviewed and documented
- [ ] Memory field integrated into agent calls
- [ ] Conversation history maintained in chat room
- [ ] Memory persistence considered (optional)
- [ ] Tests updated
- [ ] Linting passes

## Dependencies
- Requires: `32e92203-migrate-llm-loader.md`
- Related: `c0f04e25-update-chat-room.md`

## References
- Current: `backend/routes/players.py`, `backend/autofighter/rooms/chat.py`
- Framework: [midori-ai-agent-context-manager docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-context-manager/docs.md)
