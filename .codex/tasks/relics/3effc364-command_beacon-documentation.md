# Add Documentation Fields to Command Beacon Relic

## Objective

Add `full_about` and `summarized_about` fields to the Command Beacon relic plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand relic mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/relics/command_beacon.py`

**Changes required:**
1. Add a `full_about` field to the relic class with a detailed description of the relic's mechanics
2. Add a `summarized_about` field to the relic class with a brief, concise description (1-2 sentences)

**Guidelines:**
- The `full_about` should explain all mechanics, triggers, stacking behavior, and interactions in detail
- The `summarized_about` should be suitable for quick reference in game UI
- Keep descriptions clear, accurate, and consistent with the existing `about` field
- Reference the current `about` field content and `describe()` method for accuracy
- Note that relics can stack, so mention stacking behavior when relevant
- Follow the style and tone of other relic descriptions in the game

## Example Structure

```python
@dataclass
class CommandBeaconRelic(RelicBase):
    id: str = "command_beacon"
    name: str = "Command Beacon"
    # ... existing fields ...
    about: str = "existing description"
    full_about: str = "Detailed description explaining all mechanics, stacking..."
    summarized_about: str = "Brief summary for UI"
```

## Acceptance Criteria

- [ ] `full_about` field added with comprehensive description
- [ ] `summarized_about` field added with concise description
- [ ] Both descriptions are accurate to the relic's actual mechanics
- [ ] Stacking behavior is mentioned if applicable
- [ ] Code follows existing style and conventions
- [ ] Changes are tested (relic still loads and functions correctly)
