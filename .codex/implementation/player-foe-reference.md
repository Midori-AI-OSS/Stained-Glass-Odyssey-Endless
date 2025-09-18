# Player and Foe Reference

Player and Foe base classes assign a random damage type when one is not
provided, and battle rooms respect these preset elements without selecting new
types.

Each instance initializes its own LangChain ChromaDB memory tied to the current
run. Use `send_lrm_message` to interact with the LRM and `receive_lrm_message`
to log replies. Conversations remain isolated between combatants and reset for
new runs.

Each plugin may optionally define a `voice_sample`. `voice_gender` defaults to
an appropriate value based on the character's `char_type` but can be
overridden. When dialogue is generated, `generate_voice()` uses these hints and
writes the resulting audio to `assets/voices/<id>.wav`.

## LLM Integration

Both players and foes support LLM interactions through their `lrm_memory` system:

- **Memory System**: Uses ChromaDB vector storage with HuggingFace embeddings when LLM dependencies are available, falls back to simple in-memory conversation history otherwise
- **Async LLM Loading**: The `send_lrm_message()` method now loads LLMs using `asyncio.to_thread()` to prevent blocking the event loop during model downloads/initialization
- **Torch Dependencies**: Uses the centralized torch availability checker to gracefully handle missing LLM dependencies
- **Fallback Behavior**: When LLM dependencies are unavailable, returns empty responses without errors

The LLM system is fully optional - players and foes function normally without LLM dependencies installed.

## Player Roster
All legacy characters from the Pygame version have been ported as plugins.
Each entry notes the character's `CharacterType` and starting damage type.
Players currently share placeholder stats of 1000 HP, 100 attack, 50 defense,
5% crit rate, 2× crit damage, 1% effect hit, 100 mitigation, 0 dodge, 0.1 aggro,
and 1 for remaining values. Aggro defaults to `0.1` for both players and foes.

Player plugins also include a `gacha_rarity` field so the gacha system can
automatically discover 5★ and 6★ recruits.
Each player and foe defines `prompt` and `about` strings with placeholder text
to support future character-specific prompts.

Passives generally shouldn't be capped unless a designer explicitly specifies a limit.

- **Ally** (B, random) – applies `ally_passive` on load to grant ally-specific bonuses.
- **Becca** (B, random) – builds high attack but takes more damage from lower defense.
- **Bubbles** (A, random) – starts with a default item and applies `bubbles_bubble_burst`, switching elements each turn and bursting after three hits per foe.
- **Carly** (B, Light) – Guardian's Aegis heals the most injured ally, converts attack growth into defense, builds mitigation stacks that can overcharge to add defense to attack while stacks decay each turn, and shares mitigation on ultimate.
- **Ixia** (A, Lightning) – gains four times the normal benefit from Vitality.
- **Graygray** (B, random) – applies `graygray_counter_maestro`, counterattacking when hit and unleashing a max-HP burst every 50 stacks.
- **Hilander** (A, random) – builds increased crit rate and crit damage, unleashing Aftertaste on crit; stack gain odds drop 5% per stack past 20, but never below 1%.
- **Kboshi** (A, random) – randomly changes damage type; failed switches grant stacking bonuses. Switching elements consumes stacks and inflicts a brief mitigation debuff on all foes.
- **Lady Darkness** (B, Dark) – baseline fighter themed around darkness.
- **Lady Echo** (B, Lightning) – baseline fighter themed around echoes.
- **Lady Fire and Ice** (B, Fire or Ice) – baseline fighter themed around fire and ice. Duality Engine alternates elements to build Flux and reduces foe mitigation when repeating an element.
- **Lady Light** (B, Light) – baseline fighter themed around light.
- **Lady Lightning** (B, Lightning) – 5★ gacha recruit whose Stormsurge stacks add +3 Speed and +5% effect hit per action, then discharge into two-turn shocks that slow foes and cut 3% effect resistance while granting her a brief attack overload.
- **Lady of Fire** (B, Fire) – baseline fighter themed around fire.
- **Luna** (B, Generic) – applies `luna_passive`.
- **Mezzy** (B, random) – raises Max HP, takes less damage, and siphons stats from healthy allies each turn.
- **Player** (C, chosen) – avatar representing the user and may select any non-Generic damage type.

Characters marked as "random" roll one of the six elements when first loaded
and reuse that element in future sessions.

## Foe Generation
Foe plugins inherit from `FoeBase`, which mirrors `PlayerBase` stats but begins
with minimal mitigation and vitality (0.001 each) that grow by 0.0001 on
level-up. To keep encounters from stalling, foes regain health at one hundredth
the player rate. Base battles spawn one foe plus one more for every five
Pressure, capped at ten. Party size can add bonus foes using descending
probability rolls: parties of two have a 35% chance at one extra; parties of
three roll 35% for two extras and, if that fails, 75% for one. Larger parties
continue this sequence, and the total foe count never exceeds ten.
Each foe defeated during a battle temporarily raises the party's rare drop rate
by 55% for that room, increasing gold rewards and element-based item drops.

Luna's foe variant is weighted to appear more often than other characters,
including in boss encounters when she isn't already in the party.

Foes also expose a `rank` field to describe encounter tier. Supported ranks are
`normal`, `prime`, `glitched prime`, `boss`, and `glitched boss`. Battle and
boss room responses include this field for every foe so the frontend can render
appropriate tags or behaviors.
 
They are procedurally named by prefixing a randomly selected adjective plugin
from `plugins/themedadj` to a player name. Adjective plugins are
auto-discovered based on files in that directory, so adding a new adjective
requires only dropping a file into the folder. Each adjective class applies its own
stat changes derived from the legacy project—for example, **Atrocious** boosts
max HP by 90% and attack by 10%. These adjustments are applied as persistent
`StatModifier` buffs so base stats return to normal once the foe is defeated.

Example: **Atrocious Luna** applies the adjective's stat bonuses to the base
player stats and prefixes the foe's name, yielding a combatant whose title
reflects its enhanced abilities.

Development builds include a `Slime` foe plugin that reduces all baseline stats
by 90% for simple battle testing. Standard battles may also spawn random player
characters that are not currently in the party. These player foes are wrapped in
`FoeBase` at load time, granting them foe-specific behaviors such as periodic
HP regeneration via `maybe_regain`.
