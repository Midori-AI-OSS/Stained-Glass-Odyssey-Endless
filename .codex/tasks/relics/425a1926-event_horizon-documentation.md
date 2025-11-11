# Add Documentation Fields to Event Horizon Relic

## Objective

Add `full_about` and `summarized_about` fields to the Event Horizon relic plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand relic mechanics
- Consistent documentation patterns across all plugins

The Event Horizon relic was recently implemented but still uses the old `about` field instead of the new standardized fields.

## Task Details

**File to modify:** `backend/plugins/relics/event_horizon.py`

**Changes required:**
1. Remove the existing `about` field
2. Add a `full_about` field to the relic class with a detailed description of the relic's mechanics
3. Add a `summarized_about` field to the relic class with a brief, concise description (1-2 sentences)

**Guidelines:**
- The `full_about` should explain all mechanics, triggers, stacking behavior, and interactions in detail
- The `summarized_about` should be suitable for quick reference in game UI
- Keep descriptions clear, accurate, and consistent with the content from the old `about` field
- Reference the current `about` field content for accuracy
- Note that relics can stack, so mention stacking behavior when relevant
- Follow the style and tone of other relic descriptions in the game

**Description Format Standards:**

- **`summarized_about`**: Use qualitative descriptions WITHOUT specific numbers or percentages
  - Focus on the general effect type, not exact values
  - Use phrases like "boosts atk", "lowers def", "adds some hp", "reduces damage"
  - Example: "Boosts atk" instead of "Boosts atk by 500%"
  - Example: "Lowers def" instead of "Reduces def by 20%"
  - Example: "Grants shield based on max hp" instead of "Grants shield equal to 20% max HP"
  
- **`full_about`**: Include ALL specific numbers, percentages, and exact values
  - Explain all mechanics with precise details
  - Include exact values like "+500% ATK", "20% Max HP", "2 turns", "10% damage reduction", etc.
  - Example: "+500% ATK & +500% Effect Hit Rate; at the start of each battle, all allies gain +200% SPD for 2 turns"
  - Example: "+4% HP; if lethal damage would reduce you below 1 HP, reduce that damage by 10%"
  - Example: "After an Ultimate, grant a shield equal to 20% Max HP per stack"

## Current About Field Content

```python
about: str = (
    "Detonates a gravity pulse at the start of every ally turn. Each pulse rips "
    "6% of current HP (minimum 1) from every living foe per stack, while draining "
    "the acting ally for 3% of their Max HP per stack. An all-or-nothing tempo engine."
)
```

## Example Structure

```python
@dataclass
class EventHorizon(RelicBase):
    id: str = "event_horizon"
    name: str = "Event Horizon"
    # ... existing fields ...
    # about field removed - replaced with full_about and summarized_about
    full_about: str = "Detailed description explaining all mechanics, stacking..."
    summarized_about: str = "Brief summary for UI"
```

## Acceptance Criteria

- [ ] Old `about` field removed
- [ ] `full_about` field added with comprehensive description including:
  - 6% of current HP damage per stack (minimum 1)
  - 3% of Max HP self-drain per stack
  - Trigger: start of every ally turn
  - Target: every living foe
- [ ] `summarized_about` field added with concise description (no numbers)
- [ ] Both descriptions are accurate to the relic's actual mechanics
- [ ] Stacking behavior is mentioned if applicable
- [ ] Code follows existing style and conventions
- [ ] Changes are tested (relic still loads and functions correctly)
