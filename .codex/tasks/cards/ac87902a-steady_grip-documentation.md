# Add Documentation Fields to Steady Grip Card

## Objective

Add `full_about` and `summarized_about` fields to the Steady Grip card plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand card mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/cards/steady_grip.py`

**Changes required:**
1. Remove the existing `about` field
2. Add a `full_about` field to the card class with a detailed description of the card's mechanics
3. Add a `summarized_about` field to the card class with a brief, concise description (1-2 sentences)

**Guidelines:**
- The `full_about` should explain all mechanics, triggers, and interactions in detail
- The `summarized_about` should be suitable for quick reference in game UI
- Keep descriptions clear, accurate, and consistent with the content from the old `about` field
- Reference the current `about` field content for accuracy
- Follow the style and tone of other card descriptions in the game

## Example Structure

```python
@dataclass
class SteadyGripCard(CardBase):
    id: str = "steady_grip"
    name: str = "Steady Grip"
    # ... existing fields ...
    # about field removed - replaced with full_about and summarized_about
    full_about: str = "Detailed description explaining all mechanics..."
    summarized_about: str = "Brief summary for UI"
```

## Acceptance Criteria

- [ ] Old `about` field removed
- [ ] `full_about` field added with comprehensive description
- [ ] `summarized_about` field added with concise description
- [ ] Both descriptions are accurate to the card's actual mechanics
- [ ] Code follows existing style and conventions
- [ ] Changes are tested (card still loads and functions correctly)
