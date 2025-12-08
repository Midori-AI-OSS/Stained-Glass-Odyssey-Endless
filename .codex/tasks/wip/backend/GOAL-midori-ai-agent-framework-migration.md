# GOAL: Migrate to Midori AI Agent Framework

## Overview

Migrate the AutoFighter backend from custom LRM/LLM management to the [Midori AI Agent Framework](https://github.com/Midori-AI-OSS/agents-packages) for standardized, maintainable, and feature-rich language model integration.

## Current State

The backend currently uses:
- Custom `llms/loader.py` module with manual model loading
- Direct imports of `langchain`, `openai-agents`, `transformers`
- Custom wrapper classes for different backends
- Manual protocol definitions and validation
- Environment variable-based configuration

## Target State

Migrate to Midori AI Agent Framework:
- Use `midori-ai-agents-all` meta-package
- Standardized `MidoriAiAgentProtocol` interface
- Pre-built backends (OpenAI, HuggingFace, Langchain)
- Config file support (`config.toml`)
- Built-in memory management and tool support
- Factory functions for agent creation

## Benefits

### Simplified Dependency Management
- Single meta-package vs many individual packages
- Automatic version compatibility
- Easier to update and maintain

### Standardized Interface
- Consistent `AgentPayload` and `AgentResponse` models
- Unified protocol across all backends
- Less custom code to maintain

### Enhanced Features
- Built-in memory management via `memory` field
- Tool support via `invoke_with_tools`
- Streaming support across all backends
- Config file-based configuration

### Better Maintainability
- Well-documented framework with examples
- Active development and support
- Easier to add new backends
- Separation of concerns

### Improved Developer Experience
- Factory functions reduce boilerplate
- Config files separate settings from code
- Embedded documentation in package
- Consistent patterns across services

## Migration Strategy

### Phase 1: Foundation (High Priority)
1. Update dependencies to use `midori-ai-agents-all`
2. Migrate core LLM loader to agent framework
3. Add config file support

### Phase 2: Feature Integration (Medium Priority)
4. Update chat room to use AgentPayload/AgentResponse
5. Update configuration routes
6. Integrate memory management features

### Phase 3: Quality Assurance (Low Priority)
7. Update and expand test coverage
8. Update documentation

## Success Criteria

- [ ] All LLM functionality works with agent framework
- [ ] No breaking changes to existing APIs
- [ ] All tests pass
- [ ] Performance is equal or better
- [ ] Linting passes
- [ ] Documentation is up to date
- [ ] Config file support implemented
- [ ] Memory management integrated

## Related Tasks

See individual task files in this directory:
- `12af34e9-update-dependencies.md`
- `32e92203-migrate-llm-loader.md`
- `656b2a7e-create-config-support.md`
- `c0f04e25-update-chat-room.md`
- `96e5fdb9-update-config-routes.md`
- `5900934d-update-memory-management.md`
- `f035537a-update-tests.md`
- `4bf8abe6-update-documentation.md`

## Timeline

Estimated effort: 3-5 days for complete migration
- Phase 1: 1-2 days
- Phase 2: 1-2 days
- Phase 3: 1 day

## Risks and Mitigations

### Risk: Breaking Changes
**Mitigation**: Maintain backward compatibility, thorough testing

### Risk: Performance Regression
**Mitigation**: Benchmark before and after, optimize if needed

### Risk: Configuration Complexity
**Mitigation**: Provide clear examples, good defaults

### Risk: Learning Curve
**Mitigation**: Reference framework docs, follow examples

## References

- [Midori AI agents-packages](https://github.com/Midori-AI-OSS/agents-packages)
- [midori-ai-agents-all docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agents-all/docs.md)
- [midori-ai-agent-base docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-base/docs.md)
- [midori-ai-agent-openai docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-openai/docs.md)
- [midori-ai-agent-huggingface docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-huggingface/docs.md)
- Current implementation: `backend/llms/`
