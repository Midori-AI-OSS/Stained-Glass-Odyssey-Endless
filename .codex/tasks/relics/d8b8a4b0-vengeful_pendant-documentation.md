# Add Documentation Fields to Vengeful Pendant Relic

## Objective

Add `full_about` and `summarized_about` fields to the Vengeful Pendant relic plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand relic mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/relics/vengeful_pendant.py`

**Changes required:**
1. Remove the existing `about` field
2. Add a `full_about` field to the relic class with a detailed description of the relic's mechanics
3. Add a `summarized_about` field to the relic class with a concise description (1-2 sentences)

**Guidelines:**
- The `full_about` should explain all mechanics, triggers, stacking behavior, and interactions in detail
- The `summarized_about` should be suitable for quick reference in game UI
- Keep descriptions clear, accurate, and consistent with the content from the old `about` field
- Reference the current `about` field content and `describe()` method for accuracy
- Note that relics can stack, so mention stacking behavior when relevant
- Follow the style and tone of other relic descriptions in the game

## Example Structure

```python
@dataclass
class VengefulPendantRelic(RelicBase):
    id: str = "vengeful_pendant"
    name: str = "Vengeful Pendant"
    # ... existing fields ...
    # about field removed - replaced with full_about and summarized_about
    full_about: str = "Detailed description explaining all mechanics, stacking..."
    summarized_about: str = "Brief summary for UI"
```

## Acceptance Criteria

- [ ] Old `about` field removed
- [ ] `full_about` field added with comprehensive description
- [ ] `summarized_about` field added with concise description
- [ ] Both descriptions are accurate to the relic's actual mechanics
- [ ] Stacking behavior is mentioned if applicable
- [ ] Code follows existing style and conventions
- [ ] Changes are tested (relic still loads and functions correctly)
