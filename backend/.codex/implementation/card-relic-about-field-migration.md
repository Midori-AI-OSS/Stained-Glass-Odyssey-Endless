# Card and Relic About Field Migration

## Overview

As of commit 8a373e0, the card and relic base classes have been updated to use structured documentation fields instead of the single `about` field. This change enables better in-game tooltips, future LLM integration, and consistent documentation patterns.

## Changes to Base Classes

### CardBase (`backend/plugins/cards/_base.py`)

**Removed:**
- `about: str = ""`

**Added:**
- `full_about: str = ""` - Detailed description of card mechanics, triggers, and interactions
- `summarized_about: str = ""` - Brief 1-2 sentence description for UI tooltips

**Behavior Changes:**
- `__post_init__()` now auto-generates `summarized_about` from effects if not provided
- `preview_summary()` now returns `summarized_about` instead of `about`

### RelicBase (`backend/plugins/relics/_base.py`)

**Removed:**
- `about: str = ""`

**Added:**
- `full_about: str = ""` - Detailed description including stacking behavior
- `summarized_about: str = ""` - Brief 1-2 sentence description for UI tooltips

**Behavior Changes:**
- `describe(stacks)` now returns `summarized_about` instead of `about`
- `preview_summary()` now returns `summarized_about` instead of `about`

### Battle Resolution (`backend/autofighter/rooms/battle/resolution.py`)

**Updated:**
- Card reward payload now uses `card.summarized_about` instead of `card.about`
- Relic reward payload continues to use `relic.describe()` which now returns `summarized_about`

## Migration Guide for Plugin Authors

### For Card Plugins

**Before:**
```python
@dataclass
class MyCard(CardBase):
    id: str = "my_card"
    name: str = "My Card"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 0.05})
    about: str = "+5% ATK and grants bonus damage on crits"
```

**After:**
```python
@dataclass
class MyCard(CardBase):
    id: str = "my_card"
    name: str = "My Card"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 0.05})
    full_about: str = (
        "Permanently increases party ATK by 5%. Additionally, whenever a party "
        "member lands a critical hit, they deal 8% bonus damage of their "
        "elemental type. This bonus damage does not trigger on-hit effects."
    )
    summarized_about: str = "+5% ATK; crits deal +8% bonus elemental damage"
```

### For Relic Plugins

**Before:**
```python
@dataclass
class MyRelic(RelicBase):
    id: str = "my_relic"
    name: str = "My Relic"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "After an Ultimate, grant shield equal to 20% Max HP."
```

**After:**
```python
@dataclass
class MyRelic(RelicBase):
    id: str = "my_relic"
    name: str = "My Relic"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = (
        "After any party member uses their Ultimate ability, that member "
        "receives a shield equal to 20% of their Max HP per stack. The shield "
        "persists until depleted or the battle ends. This effect stacks "
        "multiplicatively: 2 stacks grant 40% Max HP, 3 stacks grant 60%, etc."
    )
    summarized_about: str = "After an Ultimate, grant shield equal to 20% Max HP per stack."
```

### Custom `describe()` Methods

Some relics override the `describe()` method to provide stack-aware descriptions. These should be updated:

**Before:**
```python
def describe(self, stacks: int) -> str:
    return self.about
```

**After:**
```python
def describe(self, stacks: int) -> str:
    pct = 20 * stacks
    return f"After an Ultimate, grant shield equal to {pct}% Max HP."
```

Or if the description doesn't need to change based on stacks:
```python
def describe(self, stacks: int) -> str:
    return self.summarized_about
```

## Best Practices

### Writing `full_about`

- Explain all mechanics in detail
- Describe trigger conditions explicitly
- Mention any edge cases or interactions
- For relics, explain stacking behavior
- Use clear, technical language
- Include percentage values and formulas where relevant

Example:
```
Whenever a party member uses an attack action, there is a 15% chance per stack 
to trigger Aftertaste, dealing 3 additional hits of 25% damage each. Every 
100% chance becomes a guaranteed trigger with the remainder as an additional 
roll. At 7 stacks (105% chance), the effect guarantees one trigger and has a 
5% chance for a second trigger.
```

### Writing `summarized_about`

- Keep it to 1-2 sentences maximum
- Focus on core functionality
- Use player-friendly language
- Include key percentages
- Suitable for tooltip display

Example:
```
Attacks have a 15% chance per stack to deal 3 additional hits of 25% damage.
```

## Test Impact

The following tests will fail until plugins are migrated:

1. `test_relic_effects_advanced.py` - Line 413 accesses `relic.about`
2. `test_fallback_relic.py` - Line 32 checks `relic.about` content
3. `test_battle_loot_items.py` - Line 134 creates test card with `about` field

These tests should be updated to use `summarized_about` or `full_about` as appropriate.

## Task Files

Individual migration tasks for all cards and relics are available in:
- `.codex/tasks/cards/` - 61 card migration tasks
- `.codex/tasks/relics/` - 41 relic migration tasks

See `.codex/tasks/00-card-relic-documentation-overview.md` for the complete migration plan.

## Timeline

This is a breaking change that requires all existing card and relic plugins to be updated. The migration is tracked through individual task files, with contributors able to pick up tasks as they have time.

## Backward Compatibility

There is **no backward compatibility** for the `about` field. All plugins must be updated to use the new fields. The base classes will auto-generate `summarized_about` from effects if not provided, but this is only a temporary fallback for cards with simple stat modifications.
