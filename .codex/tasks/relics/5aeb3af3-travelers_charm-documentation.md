# Add Documentation Fields to Travelers Charm Relic

## Objective

Add `full_about` and `summarized_about` fields to the Travelers Charm relic plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand relic mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/relics/travelers_charm.py`

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
class TravelersCharmRelic(RelicBase):
    id: str = "travelers_charm"
    name: str = "Travelers Charm"
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
   - `full_about` present: "When hit, gain +25% DEF and +10% mitigation next turn. Stacks additively (+25% DEF and +10% mitigation per stack)."
   - `summarized_about` present: "When hit, gain temporary defensive bonuses next turn"
   
2. ✅ **Accuracy Check**: Verified descriptions match implementation
   - DEF bonus: +25% per stack (line 36: `d_pct = 0.25 * stacks`) ✓
   - Mitigation bonus: +10% per stack (line 37: `m_pct = 0.10 * stacks`) ✓
   - Duration: 1 turn (line 72: `turns=1`) ✓
   - Trigger: When hit via damage_taken event (line 120) ✓
   - Timing: Buff applied at next turn start (lines 58-98) ✓
   - Stacking: Additively (documented and implemented correctly) ✓
   
3. ✅ **Format Compliance**: Verified description format standards
   - `summarized_about` has NO numbers/percentages (qualitative only) ✓
   - `full_about` includes specific values (+25% DEF, +10% mitigation) ✓
   - `full_about_stacks()` method provides stack-specific formatting via describe() ✓
   
4. ✅ **Code Style**: Ran `uv tool run ruff check` - All checks passed
   
5. ✅ **Functionality**: Relic loads successfully with proper effect management and delayed buff application

### Recommendation:
Implementation is complete and accurate. All acceptance criteria met with proper reactive defensive mechanics.

requesting review from the Task Master
