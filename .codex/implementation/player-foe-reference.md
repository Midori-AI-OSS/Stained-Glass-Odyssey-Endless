# Character Roster Reference

The `plugins/characters/` package now hosts every combatant plugin, regardless
of allegiance. Playable roster members inherit from `PlayerBase`, while AI
opponents share `FoeBase`; both base classes reside in the same package so the
shared logic for stats, memory, and voice metadata stays centralized.

When a character does not define a damage type the base classes assign one
randomly. Battle generation respects this element so characters remain consistent
between runs.

Each instance initializes LangChain-backed memory storage tied to the current
run. Use `send_lrm_message` to interact with the memory system and
`receive_lrm_message` to log responses. Conversations remain isolated per
combatant and reset for new runs. Both bases also accept optional `voice_sample`
and `voice_gender` metadata. When dialogue is generated the TTS pipeline writes
audio assets to `assets/voices/<id>.wav` using those hints.

## LLM Integration

All characters support LLM interactions through their `lrm_memory` system:

- **Memory System**: ChromaDB vector storage with HuggingFace embeddings when
  dependencies are available, otherwise a lightweight in-memory history.
- **Async Loading**: `send_lrm_message()` uses `asyncio.to_thread()` so model
  initialization never blocks the event loop.
- **Torch Detection**: The centralized torch checker gracefully handles missing
  GPU dependencies.
- **Fallback Behavior**: When dependencies are unavailable, calls resolve to
  empty responses instead of raising errors.

The LLM stack remains optional—the combat loop operates normally without it.

## Character Roster

All legacy combatants have been ported into `plugins/characters/`. The gacha
system reads each plugin's `gacha_rarity` flag to seed five- and six-star pulls.
Every entry also defines `prompt` and `about` strings for future narrative work.

Roster members share placeholder stats: 1000 HP, 100 attack, 50 defense, 5%
crit chance, 2× crit damage, 1% effect hit, 100 mitigation, 0 dodge, and 1 for
remaining values. Aggro defaults to `0.1` for both playable and hostile
variants. Characters marked as "random" roll one of the six elements on first
spawn and reuse it for future sessions. Passives should remain uncapped unless
design calls out a limit explicitly.

- **Ally** (B, random) – applies `ally_overload` on load to grant ally-specific bonuses.
- **Becca** (B, random) – builds high attack but takes more damage from lower defense.
- **Bubbles** (A, random) – starts with a default item and applies `bubbles_bubble_burst`, switching elements each turn and bursting after three hits per foe.
- **Carly** (B, Light) – Guardian's Aegis heals the most injured ally, converts attack growth into defense, builds mitigation stacks that can overcharge to add defense to attack while stacks decay each turn, and shares mitigation on ultimate.
- **Ixia** (A, Lightning) – gains four times the normal benefit from Vitality.
- **Graygray** (B, random) – applies `graygray_counter_maestro`, counterattacking when hit and unleashing a max-HP burst every 50 stacks.
- **Hilander** (A, random) – builds increased crit rate and crit damage, unleashing Aftertaste on crit; stack gain odds drop 5% per stack past 20, but never below 1%.
- **Kboshi** (A, Dark) – channels his `kboshi_flux_cycle` from a Dark baseline, cycling stored power into stacking bonuses and expending those stacks to debuff foes when he forces a flux shift.
- **Lady Darkness** (B, Dark) – baseline fighter themed around darkness.
- **Lady Echo** (B, Lightning) – baseline fighter themed around echoes.
- **Lady Fire and Ice** (B, Fire or Ice) – baseline fighter themed around fire and ice. Duality Engine alternates elements to build Flux and reduces foe mitigation when repeating an element.
- **Lady Light** (B, Light) – baseline fighter themed around light.
- **Lady Lightning** (B, Lightning) – 5★ gacha recruit whose Stormsurge stacks add +3 Speed and +5% effect hit per action, then discharge into two-turn shocks that slow foes and cut 3% effect resistance while granting her a brief attack overload.
- **Lady of Fire** (B, Fire) – baseline fighter themed around fire.
- **Lady Storm** (B, Wind or Lightning, 6★) – rotates between slipstreaming allies and overcharging lightning. Supercell Convergence grants permanent tailwinds, alternating action buffs that haste the party or stack charges, and detonates charged hits for bonus damage and mitigation shred.
- **Lady Wind** (B, Wind) – 5★ aeromancer and twin of Lady Lightning whose manic, wind-lashed experiments leave her workspace in constant disarray. Tempest Guard wraps her in a permanent slipstream of dodge and mitigation, bleeds off stacks at the start of her turn, then adds one for every foe she critically strikes to fuel gust boosts and siphon a slice of incoming damage into healing.
- **Luna** (B, Generic) – applies `luna_passive`; boss-ranked variants pre-summon astral swords that inherit her stats, mirror her action cadence, and funnel their hits into Lunar Reservoir charge.
- **Mezzy** (B, random) – raises Max HP, takes less damage, and siphons stats from healthy allies each turn.
- **Mimic** (C, random) – copies allied passives and mimics stat gains earned during battle.
- **Persona Ice** (A, Ice) – 5★ cryo tank who shields his sisters with Cryo Cycle, layering mitigation and thawing the stored frost into end-of-turn healing barriers for the party.
- **Persona Light and Dark** (A, Light or Dark) – 6★ dual-persona duelist. `persona_light_and_dark_duality` flips her element after every action, bathing allies in Light-form mitigation pulses and heals before pivoting into Dark-form crit bursts that strip foe defenses.
- **Player** (C, chosen) – avatar representing the user and may select any non-Generic damage type.
- **Slime** (C, random) – non-selectable training dummy that mirrors the baseline stat line and supplies fallback foes.

## Hostile Variants

The package exposes a `CHARACTER_FOES` dictionary that maps roster IDs to
automatically wrapped foe subclasses. When `plugins.characters` loads, each
`PlayerBase` subclass receives a matching foe variant that mixes in `FoeBase`
and applies a random adjective from the `themedadj` plugins. These wrappers are
exported beside their player counterparts (for example, `AllyFoe`).

Encounter generation supplements any dedicated foe plugins with these wrapped
variants. `autofighter.rooms.foes.catalog.load_catalog()` scans the
`plugins/characters/` directory via the `PluginLoader`, filters out base classes,
and merges in `CHARACTER_FOES` so the spawn table always contains a hostile form
for every roster member.

`FoeBase` mirrors `PlayerBase` stats but starts with minimal mitigation and
vitality to keep fights brisk. Supported `rank` values remain `normal`, `prime`,
`glitched prime`, `boss`, and `glitched boss`. Battle and boss room responses
include this field so the frontend can render appropriate tags. Adjective
plugins still prefix foe names and apply stat modifiers through
`StatModifier` buffs, ensuring those adjustments fall away once an encounter
ends.

Standard battles may also spawn characters that are not currently in the party.
Because foe wrappers reuse the player implementations, they benefit from
character-specific passives, customization hooks, and scaling logic without
duplicating code.
