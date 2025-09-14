# Map and Room Types

1. Room categories: chat, battle-weak, battle-normal, battle-boss, **battle-boss-floor**, shop.
   - Each floor has at least one shop.
   - Chats occur after fights without consuming room count.
   - Chat rooms let players RP with an LLM copy of a character that offers one-message tips or comments about the run.
   - Players may send only one message per chat room, capped at six chats per floor.
2. Map generator: 45-room floors for ~100 floors; endless looping after final floor.
   - Optional **Pressure Level** boosts foe stats by +5%–10% per tier and is selectable up to the highest level cleared.
   - Display Pressure Level next to foe names in combat, e.g., `Luna (5)`.
   - Every 5 Pressure levels add an extra foe per battle room up to 10; once capped, loot drops decrease.
   - Every 10 Pressure levels add one more room per floor before the boss.
   - Every 20 Pressure levels insert additional back-to-back boss rooms.
   - Enemy stats scale as base stats × floor level × room level × loop count.
   - Each loop multiplies enemy stats by 1.2× ±5% and, after the second loop, grants +1 Pressure level for future runs.
   - Battle rooms scale foes by 1.05× ±5% per fight.
3. Final room each floor is **battle-boss-floor** with a single foe at 100× floor level × room level × loop count.
4. Display: color-coded nodes, readable icons, highlight current location, show valid paths.
5. Transitions load correct room scenes using shared templates with floor-specific themes.
6. Starting around room 20, gradually shift floor visuals toward the upcoming boss room (e.g., Luna’s floor gains more night and star motifs) so players can sense the next encounter.
7. Combat accuracy driven solely by stats; reusable, recolorable effects for attack types and team buffs.
8. Fights that exceed 100 turns (500 for floor bosses) trigger a slow red/blue flash on the room to warn of drawn-out battles.
   - Each turn after the flash begins grants foes a +40% Attack `Enraged` buff.
9. Rewards:
   - **Rare drop rate (`rdr`)** multiplies gold payouts, relic drop odds, upgrade item counts, and pull ticket chances. At extreme values it also boosts relic and card star ranks (3★→4★ at 1000% `rdr`, 4★→5★ at 1,000,000%).
   - Normal fights: 10% × `rdr` chance to drop a relic (70% 1★, 20% 2★, 10% 3★), grant gold = 5 × loop × rand(1.01–1.25) × `rdr`, drop 1–2★ upgrade items based on floor/room/Pressure (capped at 4★) with quantity scaled by `rdr`, and award a 1–2★ card.
   - Bosses: 50% × `rdr` chance to drop a relic (60% 3★, 30% 4★, 10% 5★), grant gold = 20 × loop × rand(1.53–2.25) × `rdr`, drop 1–3★ upgrade items scaled by difficulty (max 4★) with quantity scaled by `rdr`, and award a 1–5★ card.
   - Floor bosses: guaranteed relic drop (60% 3★, 30% 4★, 10% 5★), largest gold bonus = 200 × loop × rand(2.05–4.25) × `rdr`, drop 3–4★ upgrade items scaled by difficulty (max 4★) with quantity scaled by `rdr`, award 3–5★ cards, and roll a 10% × `rdr` chance for one pull ticket.
   - Relics come in 1–5★ ranks using the shared star-color scheme; stacks have no cap and drop tables favor relics the player lacks.
   - Cards are unique collectibles with one copy each; design ~100 cards per combat theme (DoT, melee, etc.), with 1★ effects providing minor perks (e.g., heal 1% when dealing DoT) and 5★ effects offering major boons (e.g., temporary ally joins the party).
10. Code structure:
    - Create a `MapNode` dataclass storing room type, links, and reward data.
    - Implement `Room` subclasses (`BattleRoom`, `ChatRoom`, etc.) with shared interfaces for entry, reward, and exit hooks.
    - Build a `chat/` module that routes one-shot messages to local or remote LLMs stored under `llms/`.
    - Seed each floor from a run-specific base seed, mutate it several times, and forbid seed reuse so players cannot reproduce identical maps.
    - Expand event plugins with branching outcomes and tests to cover failure paths.
