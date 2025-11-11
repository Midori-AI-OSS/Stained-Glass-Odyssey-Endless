# Add Documentation Fields to Iron Resolve Card

## Objective

Add `full_about` and `summarized_about` fields to the Iron Resolve card plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand card mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/cards/iron_resolve.py`

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

## Example Structure

```python
@dataclass
class IronResolveCard(CardBase):
    id: str = "iron_resolve"
    name: str = "Iron Resolve"
    # ... existing fields ...
    # about field removed - replaced with full_about and summarized_about
    full_about: str = "Detailed description explaining all mechanics..."
    summarized_about: str = "Brief summary for UI"
```

## Acceptance Criteria

- [x] Old `about` field removed
- [x] `full_about` field added with comprehensive description
- [x] `summarized_about` field added with concise description
- [x] Both descriptions are accurate to the card's actual mechanics
- [x] Code follows existing style and conventions
- [x] Changes are tested (card still loads and functions correctly)

## Audit Results (2025-11-11)

**Auditor:** GitHub Copilot Coding Agent  
**Status:** ✅ APPROVED

### Verification Performed:
1. ✅ **Code Review**: Verified all acceptance criteria met
   - No `about` field present (correctly removed)
   - `full_about` present: "+500% DEF & +500% HP; the first time an ally dies, revive them at 30% HP. This effect refreshes every 3 turns."
   - `summarized_about` present: "Boosts def and hp; revives fallen allies with a cooldown"
   
2. ✅ **Accuracy Check**: Verified descriptions match implementation
   - Stat boosts: `effects: dict[str, float] = field(default_factory=lambda: {"defense": 5, "max_hp": 5})` = 500% DEF & HP ✓
   - Revive HP: `revive_hp = int(target.max_hp * 0.30)` = 30% max HP ✓
   - Cooldown: `cooldowns[pid] = 3` = 3 turns ✓
   - Cooldown decrement on `turn_end` verified ✓
   
3. ✅ **Format Compliance**: Verified description format standards
   - `summarized_about` has NO numbers/percentages (qualitative only) ✓
   - `full_about` includes specific values (+500%, 30% HP, 3 turns) ✓
   
4. ✅ **Code Style**: Ran `uv tool run ruff check` - All checks passed
   
5. ✅ **Functionality**: Card loads successfully and instantiates correctly

### Notes:
- Powerful revival mechanic well-implemented with per-member cooldown tracking
- Clean event-driven logic with proper death detection (hp <= 0 check after damage)
- No dedicated test file (acceptable for documentation-only task)
- Excellent use of dictionary to track individual cooldowns per party member

### Recommendation:
Task is complete and meets all acceptance criteria. Requesting review from the Task Master.
