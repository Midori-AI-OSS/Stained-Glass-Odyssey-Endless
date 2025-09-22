# Boss Room Theme Concepts

## Goal
Outline per-character themes for `battle-boss-floor` rooms so each final encounter on a floor reflects the boss's personality and story role.

## Baseline Style
- Reuse shared room templates for layout and mechanics.
- Apply character-specific decorations, lighting, and ambient audio.
- Keep navigation simple to focus on the boss fight.
- Allow themes to modify boss mechanics (e.g., Luna's room grants low gravity).

## Example Themes
- **Luna**
  - Celestial motifs: starfields, moonlight beams, gentle chimes.
  - Floating platforms and holographic constellations.
- **Carly**
  - Corporate office: cubicles, filing cabinets, fluorescent lighting.
  - Background chatter and ringing phones for ambience.
- **Kboshi**
  - Neon dojo with holographic scrolls and sliding paper screens.
  - Driving synth percussion and glowing blade racks.
- **Lady Darkness**
  - Gothic hall draped in tattered banners and flickering candles.
  - Whispering choir pads and deep echoing footsteps.

## Actionable Next Steps
1. Confirm the roster of bosses and assign a theme to each character.
2. Prototype one themed room in the web UI to validate the decoration pipeline.
3. Define a naming convention for theme assets (textures, props, audio) to keep them organized.
4. Document how themes interact with floor-wide visual styles in `.codex/implementation`.

## Open Questions
- To reduce production load, which A/B/C body types and room props can be reused across themes?
- What fallback theme should we use if a character lacks custom assets in time (e.g., gender-appropriate generic body dressed in all pink)?
