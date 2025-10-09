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
variants. Characters marked as "Any" roll one of the available damage types on
first spawn and reuse it for future sessions unless customized.

| Character | Rank | Rarity | Element(s) | Signature traits | Availability |
| --- | --- | --- | --- | --- | --- |
| Ally | B | 5★ | Any (randomized) | `ally_overload` grants adaptive support bonuses, manipulating elements to dismantle enemy defenses. | Standard gacha recruit. |
| Becca | B | 5★ | Any (randomized) | `becca_menagerie_bond` reorganizes elemental pairings, pushing her attack growth at the cost of lowered defenses. | Standard gacha recruit. |
| Bubbles | A | 5★ | Any (randomized) | `bubbles_bubble_burst` rotates elements each turn, building chain reactions that detonate after repeated hits. | Standard gacha recruit. |
| Carly | B | 5★ | Light | `carly_guardians_aegis` heals the most injured ally, converts attack gains into defense, stacks mitigation, and shares shields on her ultimate. | Standard gacha recruit. |
| Casno | A | 5★ | Fire | `casno_phoenix_respite` enforces five-action cycles, cancelling the next move to trigger a full-heal Phoenix rest that adds permanent stat boons. | Standard gacha recruit. |
| Graygray | B | 5★ | Any (randomized) | `graygray_counter_maestro` retaliates when struck and periodically releases max-HP bursts after stacking counters. | Standard gacha recruit. |
| Hilander | A | 5★ | Any (randomized) | `hilander_critical_ferment` builds crit rate and crit damage with diminishing odds after 20 stacks, unleashing Aftertaste on crits. | Standard gacha recruit. |
| Ixia | A | 5★ | Lightning | `ixia_tiny_titan` quadruples Vitality scaling, turning the small-statured brawler into a lightning bruiser. | Standard gacha recruit. |
| Kboshi | A | 5★ | Dark | `kboshi_flux_cycle` channels dark energy, banking power in flux stacks and expending them to debuff foes. | Standard gacha recruit. |
| LadyDarkness | B | 5★ | Dark | `lady_darkness_eclipsing_veil` wraps the field in despair-laced shadows that sap enemy resolve. | Standard gacha recruit. |
| LadyEcho | B | 5★ | Lightning | `lady_echo_resonant_static` weaponizes echoed lightning at the cost of de-aging, driving her inventive combat style. | Standard gacha recruit. |
| LadyFireAndIce | B | 6★ | Fire / Ice (persona swap) | `lady_fire_and_ice_duality_engine` alternates between fire and ice personas, building Flux and shredding mitigation when repeating an element. | 6★ gacha headliner. |
| LadyLight | B | 5★ | Light | `lady_light_radiant_aegis` projects barriers that shield allies despite her Cotard's Syndrome limitations. | Standard gacha recruit. |
| LadyLightning | B | 5★ | Lightning | `lady_lightning_stormsurge` stacks speed and effect hit before discharging shocks that slow and weaken foes. | Standard gacha recruit. |
| LadyOfFire | B | 5★ | Fire | `lady_of_fire_infernal_momentum` converts defeated foes into escalating heat-wave stacks for overwhelming fire damage. | Standard gacha recruit. |
| LadyStorm | B | 6★ | Wind / Lightning (randomized) | `lady_storm_supercell` weaves slipstreams into charge detonations that grant tailwinds and shred mitigation. | 6★ gacha headliner. |
| LadyWind | B | 5★ | Wind | `lady_wind_tempest_guard` sustains a permanent slipstream of dodge and mitigation, feeding on critical hits. | Standard gacha recruit. |
| Luna | B | Story | Generic | `luna_lunar_reservoir` charges astral swords, doubling actions up to 32 per turn before adding +1 per extra 25 charge; boss-ranked variants pre-summon blades that mirror her actions, while glitched non-boss ranks cache twin Lightstream swords before combat. | Story antagonist only; cannot be unlocked or recruited. |
| Mezzy | B | 5★ | Any (randomized) | `mezzy_gluttonous_bulwark` devours incoming attacks, siphoning stats and reducing damage taken. | Standard gacha recruit. |
| Mimic | C | 0★ | Any (randomized) | `mimic_player_copy` mirrors allied passives and stat gains. | Mirrors an active party member during scripted mirror fights; non-selectable. |
| PersonaIce | A | 5★ | Ice | `persona_ice_cryo_cycle` layers mitigation and thaws stored frost into end-of-turn healing barriers. | Standard gacha recruit. |
| PersonaLightAndDark | A | 6★ | Light / Dark (alternating) | `persona_light_and_dark_duality` flips elements every action, pulsing Light-form heals before Dark-form crit bursts that strip defenses. | 6★ gacha headliner. |
| Player | C | Story | Chosen (player-selected) | `player_level_up_bonus` scales with run progress, representing the customizable avatar. | Always available starter. |
| Slime | C | 0★ | Any (randomized) | Baseline stat template that tags in as a helper for foe lineups, including boss slots. | Non-selectable foe support unit that appears when encounters need a fallback combatant. |

Characters flagged as non-selectable (Mimic, Slime) surface in mirrored or fallback encounters—Mimic copies an active party member, while Slime reinforces enemy teams as needed—but neither can join the active party. Story characters like Luna and the Player bypass the gacha pool; the Player is available from the start, whereas Luna remains an encounter-only boss.

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
