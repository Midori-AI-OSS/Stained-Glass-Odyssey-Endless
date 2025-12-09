# Update Chat Room Implementation for Agent Framework

## Task ID
`c0f04e25-update-chat-room`

## Priority
High

## Status
WIP - Needs Redesign

## Description
Redesign the chat room system to use a more sophisticated per-character agent architecture with Midori AI Vector Manager for memory management and event-driven character interactions.

## Context
Current implementation in `autofighter/rooms/chat.py`:
- Uses `load_llm()` with custom streaming interface
- Sends raw JSON payload as prompt
- Manually concatenates streamed chunks
- No structured payload/response format
- No per-character memory or context management
- No event-driven character responses

## Revised Vision (Updated 2025-12-09)

### Architecture Overview
Instead of a simple chat room that generates responses on-demand, implement a sophisticated per-character agent system:

1. **Per-Character Agent Setup**
   - Each character in the party gets their own dedicated "agent" instance
   - Agents are initialized when characters join the party
   - Each agent maintains its own context and memory through Midori AI Vector Manager
   - Agents use Midori AI Context Manager for persistent memory

2. **Event-Driven Responses**
   - Characters can be triggered by multiple events:
     - Name mentioned in conversation
     - Significant healing received
     - Heavy damage taken
     - Death events (in-game)
     - Joining the party
     - Custom plugin-defined events via the event bus
   - Responses are cached in RAM for the game session to prevent redundant generation and token waste

3. **Memory Management**
   - Each character's agent uses Midori AI Vector Manager for long-term memory
   - Context Manager maintains conversation history and character state
   - Memory persists across game sessions for the character
   - Efficient retrieval of relevant context for responses

4. **Plugin System Integration**
   - Leverage existing plugin system for custom triggers
   - New contributors can easily add custom character reactions
   - Observe event bus for triggers (e.g., light character hit by dark character with relevant backstory)
   - Clean separation between character logic and trigger logic

### Implementation Steps

#### Phase 1: Agent Infrastructure
1. Create `backend/autofighter/agents/` directory structure
2. Implement `CharacterAgent` base class:
   - Wraps Midori AI Agent Framework
   - Integrates Vector Manager for memory
   - Integrates Context Manager for conversation history
   - Provides trigger registration API
3. Create agent factory for initializing character agents
4. Add agent lifecycle management to party

#### Phase 2: Memory Integration
1. Integrate Midori AI Vector Manager:
   - Per-character vector store for memories
   - Efficient similarity search for context retrieval
2. Integrate Midori AI Context Manager:
   - Maintain conversation threads
   - Track character state and relationships
3. Implement response caching:
   - RAM-based cache for game session
   - Cache key based on trigger type and context
   - Invalidation strategy for significant state changes

#### Phase 3: Event System
1. Define standard trigger events:
   - `character_mentioned`
   - `character_healed`
   - `character_damaged`
   - `character_died`
   - `character_joined_party`
   - Custom plugin events
2. Integrate with existing event bus
3. Implement trigger handlers in CharacterAgent
4. Add response generation for each trigger type

#### Phase 4: Chat Room Update
1. Update `ChatRoom` to use new agent system:
   - Get relevant character agent(s)
   - Check trigger conditions
   - Retrieve cached responses or generate new ones
   - Return formatted responses
2. Maintain backward compatibility with existing API
3. Update tests for new architecture

#### Phase 5: Plugin Examples
1. Create example custom trigger plugin
2. Document plugin API for character reactions
3. Add developer documentation for extending system

## Objectives
1. Create per-character agent architecture
2. Integrate Midori AI Vector Manager for memory
3. Integrate Midori AI Context Manager for conversation
4. Implement event-driven response system
5. Add response caching for efficiency
6. Leverage plugin system for extensibility
7. Maintain or improve existing functionality

## Acceptance Criteria
- [ ] CharacterAgent class implemented with Vector/Context Manager integration
- [ ] Agent factory creates agents when characters join party
- [ ] Memory system stores and retrieves character-specific context
- [ ] Event-driven triggers work for standard events
- [ ] Response caching prevents redundant generation
- [ ] Plugin system allows custom triggers and reactions
- [ ] Chat room uses new agent system
- [ ] All existing tests pass with new architecture
- [ ] New tests cover agent lifecycle and memory
- [ ] Documentation updated for new system
- [ ] Example plugin demonstrates extensibility

## Dependencies
- Requires: `32e92203-migrate-llm-loader.md` (agent_loader.py)
- Requires: Midori AI Vector Manager integration
- Requires: Midori AI Context Manager integration
- Related: Plugin system documentation

## Notes for Task Master
This is a significant architectural change that requires:
1. Breaking down into smaller, manageable subtasks
2. Coordination with other systems (party management, event bus, plugins)
3. Careful planning of memory and caching strategies
4. Clear API design for plugin developers

The original simple migration to Agent Framework was too limited. This new design provides:
- Better separation of concerns
- More efficient resource usage (caching)
- Greater extensibility (plugin system)
- Better contributor experience (clean APIs)
- More engaging character interactions (event-driven)

## References
- Current: `backend/autofighter/rooms/chat.py`
- Framework: [midori-ai-agent-base docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-base/docs.md)
- Vector Manager: [midori-ai-vector-manager docs](https://github.com/Midori-AI-OSS/agents-packages)
- Context Manager: [midori-ai-agent-context-manager docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-context-manager/docs.md)
- Event System: `backend/autofighter/events/` (existing event bus)
