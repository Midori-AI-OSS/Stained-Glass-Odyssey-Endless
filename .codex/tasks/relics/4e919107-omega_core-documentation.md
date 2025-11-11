# Add Documentation Fields to Omega Core Relic

## Objective

Add `full_about` and `summarized_about` fields to the Omega Core relic plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand relic mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/relics/omega_core.py`

**Changes required:**
1. Remove the existing `about` field
2. Add a `full_about` field to the relic class with a detailed description of the relic's mechanics
3. Add a `summarized_about` field to the relic class with a brief, concise description (1-2 sentences)

**Guidelines:**
- The `full_about` should explain all mechanics, triggers, stacking behavior, and interactions in detail
- The `summarized_about` should be suitable for quick reference in game UI
- Keep descriptions clear, accurate, and consistent with the content from the old `about` field
- Reference the current `about` field content and `describe()` method for accuracy
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

## Example Structure

```python
@dataclass
class OmegaCoreRelic(RelicBase):
    id: str = "omega_core"
    name: str = "Omega Core"
    # ... existing fields ...
    # about field removed - replaced with full_about and summarized_about
    full_about: str = "Detailed description explaining all mechanics, stacking..."
    summarized_about: str = "Brief summary for UI"
```

## Acceptance Criteria

- [x] Old `about` field removed
- [x] `full_about` field added with comprehensive description
- [x] `summarized_about` field added with concise description
- [x] Both descriptions are accurate to the relic's actual mechanics
- [x] Stacking behavior is mentioned if applicable
- [x] Code follows existing style and conventions
- [x] Changes are tested (relic still loads and functions correctly)

---

## Audit Results (2025-11-11)

**Auditor:** AI Agent (Auditor Mode)  
**Status:** ✅ APPROVED

### Verification Performed:

1. ✅ **Code Review**: All acceptance criteria verified
   - No `about` field present (correctly removed)
   - `full_about` present: "+600% ATK & +600% DEF (and all other stats by 6x) for the entire fight. After 10 turns, allies begin losing 1% of Max HP each turn, increasing by 1% per turn."
   - `summarized_about` present: "Massively boosts all stats for entire fight but drains hp after delay"
   
2. ✅ **Accuracy Check**: Verified descriptions match implementation
   - Stat boost: 6x multiplier (600%) for all stats (lines 57-71: atk_mult, defense_mult, crit_rate_mult, etc. all set to `mult` which is 6.0 for 1 stack) ✓
   - Duration: Entire fight (line 60: turns=9999) ✓
   - HP drain delay: 10 turns for 1 stack (line 34: `delay = 10 + 2 * (stacks - 1)`) ✓
   - HP drain: 1% per turn, increasing by 1% each turn (line 83: `drain = (state["turn"] - delay) * 0.01`) ✓
   - Stacking: Delay increases by 2 turns per stack, multiplier increases by 1x per stack (lines 34-35, 116-122) ✓
   
3. ✅ **Format Compliance**: Verified description format standards
   - `summarized_about` has NO numbers/percentages (qualitative only) ✓
   - `full_about` includes specific values (+600% ATK, +600% DEF, 6x, 10 turns, 1%) ✓
   - `full_about_stacks()` method provides stack-specific formatting via describe() ✓
   
4. ✅ **Code Style**: Ran `uv tool run ruff check` - All checks passed
   
5. ✅ **Functionality**: Relic loads successfully with proper effect management and event handling

### Recommendation:
Implementation is complete and accurate. All acceptance criteria met with comprehensive stat boost and escalating HP drain mechanics.

requesting review from the Task Master
