# Add Looks String to Ixia Character

⚠️ **DO NOT WORK ON THIS TASK** - Awaiting character description from user.

## Description
Add a `looks` field to the Ixia character class (`backend/plugins/characters/ixia.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

## Background
The repository is standardizing character descriptions by adding a `looks` string that provides detailed visual descriptions for each character. This supports future AI-powered features and provides rich context for character appearance.

## Reference Examples
See these files for the expected format:
- `backend/plugins/characters/luna.py` (lines 193-201)
- `backend/plugins/characters/ryne.py` (lines 24-54)
- `backend/plugins/characters/lady_light.py` (lines 16-24)
- `backend/plugins/characters/lady_darkness.py` (lines 16-25)

## Proposed appearance description
Below is a multi-paragraph `looks` string you can copy directly into the Ixia dataclass. It follows the same triple-quoted, multi-paragraph format used by other characters (Luna, Ryne, Lady Light, Lady Darkness) and is positioned to be placed after `summarized_about` and before `char_type`.

```python
"""
Ixia is a petite lalafel mage with a delicate, childlike silhouette—short in stature but perfectly proportioned, giving her a nimble, sprightly presence. Her skin is pale and smooth, with a subtle, healthy sheen that catches light in soft highlights. She carries herself with an easy, purposeful gait that blends curiosity and quiet confidence.

Her face is small and finely featured: a gently rounded jaw, a small nose, and high, gently arched brows. Large, expressive eyes glow a deep, crystalline red—bright and alert, hinting at constant arcane awareness. Her ears are long and tapered to a sharp point, unmistakably lalafel and often framed by her hair.

She wears a sleek bob cut that falls to chin length, dyed a deep midnight-blue that appears almost black in shadow but flashes navy in sunlight. Her bangs are cut straight across the forehead, with subtle inward curls that soften the face. Stray wisps and a few shorter layers around the ears give the style a natural, slightly windswept look.

Ixia's outfit blends practical adventurer's tailoring with arcane ornamentation. She favors a fitted, sleeveless bodice of layered leather and cloth in rich violet and onyx tones, trimmed with silver filigree and geometric motifs. A ruffled white chemise peeks from under the collar and sleeves, adding a touch of contrast and old-world charm. Her skirt is short and tiered—dark pleats beneath purple panels embossed with subtle runes—allowing freedom of movement while retaining a refined silhouette.

Her boots are knee-high, black leather with small engraved metal plates at the cuffs and practical straps; they look built to last yet are light enough for quick steps and leaps. A decorative belt with interlocking silver clasps cinches the waist and supports small satchels and trinkets—components for her craft.

The most striking accessory is her staff: a slender, dark shaft topped with a multifaceted crystal that pulses between magenta and violet. The staff's metalwork is ornate and slightly gothic—twisting vines and crescent motifs that echo the silver patterns on her clothing. When she channels magic, faint motes of purple and pale blue light orbit the crystal and her hands, and thin threads of energy trail from her fingertips.

Her posture is compact and poised—ready to dart or unleash a spell at a moment's notice. Mannerisms are minimal but expressive: a brief, contemplative tilt of the head when considering a new idea, a quick, precise adjustment of her staff before casting, and joyful, sudden bursts of speed when excited. Visual magical effects around her favor crystalline shards, soft luminescent motes, and cold, starlike flares that match the violet-pink glow of her staff.

Overall, Ixia presents as a refined, small-statured lalafel spellcaster—equal parts determined apprentice and precise arcane practitioner—whose dark-violet, silver-accented wardrobe and radiant crystal staff make her presence unmistakable on any battlefield or moonlit glade.
"""
```

## Acceptance Criteria
- [ ] `looks` field added to the Ixia dataclass
- [ ] Content follows multi-paragraph format used in reference examples
- [ ] Triple-quoted string format used for multiline text
- [ ] Positioned after `summarized_about` and before `char_type`
- [ ] No changes to existing functionality

## Task Type
Documentation / Character Enhancement

## Priority
Low - Quality of life improvement

## Notes
- This is part of a batch update to add looks strings to all characters
- User will provide the actual appearance description
- Task should only add the field, not modify any game mechanics
