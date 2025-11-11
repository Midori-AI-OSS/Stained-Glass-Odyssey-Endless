# Add Documentation Fields to Equilibrium Prism Card

## Objective

Add `full_about` and `summarized_about` fields to the Equilibrium Prism card plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand card mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/cards/equilibrium_prism.py`

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
class EquilibriumPrismCard(CardBase):
    id: str = "equilibrium_prism"
    name: str = "Equilibrium Prism"
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

---

## Audit Results (2025-11-11)

**Auditor:** AI Agent (Auditor Mode)  
**Status:** ✅ APPROVED

### Verification Performed:

1. ✅ **Code Review**: All acceptance criteria verified
   - No `about` field present (correctly removed)
   - `full_about` present: "+1500% ATK & +1500% DEF; at turn start, heal allies toward the party's HP average without harming them. Each healed ally grants a Balance token; at 5 tokens, grant allies +50% Crit Rate & +50% Mitigation for 1 turn and deal 200% Light damage to the highest-HP foe."
   - `summarized_about` present: "Boosts atk and def; balances party HP each turn, builds tokens to trigger burst buffs and damage"
   
2. ✅ **Accuracy Check**: Verified descriptions match implementation
   - Stat effects: +1500% ATK & +1500% DEF (lines 23-25) ✓
   - HP averaging logic: Heals allies toward party HP average without harming them (lines 77-132) ✓
   - Balance token system: Gains tokens per healed ally, triggers at 5 tokens (lines 138-164) ✓
   - Burst buffs: +50% Crit Rate & +50% Mitigation for 1 turn (lines 172-198) ✓
   - Burst damage: 200% Light damage to highest-HP foe (lines 200-262) ✓
   
3. ✅ **Format Compliance**: Verified description format standards
   - `summarized_about` has NO numbers/percentages (qualitative only) ✓
   - `full_about` includes specific values (+1500%, +50%, 1 turn, 200%, 5 tokens) ✓
   
4. ✅ **Code Style**: Ran `uv tool run ruff check` - All checks passed
   
5. ✅ **Functionality**: Card loads successfully and functions correctly

### Notes:
- Implementation is clean and well-structured
- Complex mechanics (HP averaging, token system, burst effects) are all correctly documented
- Descriptions accurately reflect the sophisticated card behavior

### Recommendation:
Implementation is complete and excellent. All acceptance criteria met.

requesting review from the Task Master
