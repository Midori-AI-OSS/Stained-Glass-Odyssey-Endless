# Character Description Migration Reference (Optional Follow-up)

## Context

This task documents the character files that would need migration if the project decides to implement true concise/verbose description modes for characters, following the pattern established for cards and relics.

**Status:** Optional - only pursue if task `62a63444` (immediate fix) is completed AND concise descriptions are desired for characters.

## Background

The immediate issue (empty description strings) can be fixed with a simple fallback in the roster endpoint. However, if we want characters to have distinct concise and verbose descriptions like cards and relics do, each character needs individual migration.

## Characters Requiring Migration

All 25 character files would need the following changes:

### Pattern to Follow

Replace:
```python
about: str = "Long detailed description..."
```

With:
```python
full_about: str = "Long detailed description with mechanics and lore..."
summarized_about: str = "Short 1-2 sentence hook without numbers or mechanics."
```

### Character List

1. `ally.py` - Ally
2. `becca.py` - Becca
3. `bubbles.py` - Bubbles
4. `carly.py` - Carly
5. `casno.py` - Casno
6. `graygray.py` - GrayGray
7. `hilander.py` - Hilander
8. `ixia.py` - Ixia
9. `kboshi.py` - Kboshi
10. `lady_darkness.py` - Lady Darkness
11. `lady_echo.py` - Lady Echo
12. `lady_fire_and_ice.py` - Lady Fire and Ice
13. `lady_light.py` - Lady Light
14. `lady_lightning.py` - Lady Lightning
15. `lady_of_fire.py` - Lady of Fire
16. `lady_storm.py` - Lady Storm
17. `lady_wind.py` - Lady Wind
18. `luna.py` - Luna (has extensive `about` and `looks` text)
19. `mezzy.py` - Mezzy
20. `mimic.py` - Mimic
21. `persona_ice.py` - Persona Ice
22. `persona_light_and_dark.py` - Persona Light and Dark
23. `player.py` - Player (main character)
24. `ryne.py` - Ryne
25. `slime.py` - Slime

**Note:** Luna has exceptionally long description text including separate `looks` field - may need special handling.

## Migration Guidelines

Each character migration should:

1. **Preserve existing `about` text** as `full_about` (don't lose lore)
2. **Write concise summary** as `summarized_about`:
   - 1-2 sentences maximum
   - Focus on character hook/identity
   - No numbers, mechanics, or stat details
   - Suitable for quick scanning in Party Picker
3. **Update tests** if character descriptions are tested
4. **Update `.codex/implementation/player-foe-reference.md`** with new descriptions

## Example Migration

**Before:**
```python
@dataclass
class LadyEcho(PlayerBase):
    id = "lady_echo"
    name = "LadyEcho"
    about = "Echo, a 22-year-old Aasimar inventor with distinctive light yellow hair and a brilliant mind shaped by Asperger's Syndrome. Her high intelligence manifests in an obsessive passion for building and creating, constantly tinkering with devices that blur the line between magic and technology. In combat, her resonant static abilities create powerful lightning echoes that reverberate across the battlefield—but every use of her powers comes with a cost. Minor abilities de-age her by 12 hours, while major powers can steal up to a year from her apparent age. This limitation drives her inventive nature as she seeks to build devices that might mitigate or reverse the de-aging effect. Despite social challenges from her neurodiversity, her heroic drive compels her to help others, even when the price is measured in lost time."
```

**After:**
```python
@dataclass
class LadyEcho(PlayerBase):
    id = "lady_echo"
    name = "LadyEcho"
    full_about = "Echo, a 22-year-old Aasimar inventor with distinctive light yellow hair and a brilliant mind shaped by Asperger's Syndrome. Her high intelligence manifests in an obsessive passion for building and creating, constantly tinkering with devices that blur the line between magic and technology. In combat, her resonant static abilities create powerful lightning echoes that reverberate across the battlefield—but every use of her powers comes with a cost. Minor abilities de-age her by 12 hours, while major powers can steal up to a year from her apparent age. This limitation drives her inventive nature as she seeks to build devices that might mitigate or reverse the de-aging effect. Despite social challenges from her neurodiversity, her heroic drive compels her to help others, even when the price is measured in lost time."
    summarized_about = "A brilliant Aasimar inventor whose resonant lightning powers drain her youth with each use, compelling her to constantly create new devices while racing against time."
```

## Dependencies

- Task `62a63444` must be completed first (provides fallback mechanism)
- Requires coordination to avoid merge conflicts if multiple characters are worked on simultaneously
- Consider creating subtasks in `.codex/tasks/chars/` for individual characters if this work is pursued

## Decision Point

This migration is **NOT required** for basic functionality. Only pursue if:
- The immediate fix is in place and working
- Product team wants distinct concise/verbose character descriptions
- Resources are available for writing 25+ concise summaries
- Testing capacity exists for verifying 25+ character changes

## Alternative Approaches

1. **Gradual migration**: Update only high-priority characters (Player, Luna, popular characters) first
2. **Generated summaries**: Use LLM to generate initial drafts of `summarized_about`, then human-review
3. **Leave as-is**: Keep using fallback indefinitely; characters show same text in both modes
