# Gacha Character Recruitment

1. Between runs, players spend collected upgrade items on gacha pulls for recruitable characters and chatable allies.
   - Pulls share the same pity counters and currency as main-menu pulls.
   - Players may pull as much as they want and immediately add new characters before leaving.
   - Each character is classified as Type A (Masculine), Type B (Feminine), or Type C (Androgynous).
   - Seed the pool with existing player plugins such as Ally, Becca, Bubbles, Carly, Ixia, Graygray, Hilander, Kboshi, Lady Darkness, Lady Echo, Lady Fire and Ice, Lady Light, Luna, Mezzy, and Mimic.
2. Pull options: spend for exactly 1, 5, or 10 pulls; players cannot choose other batch sizes.
   - Play a pre-made video keyed to the highest rarity obtained (1★–6★); videos are skippable or fast-forwardable.
   - Base odds heavily favor ≥2★ rewards (~99%), with 5★ and 6★ odds rising as pity grows.
   - After the video, display a menu listing all items/characters from the pull batch.
3. Pity system: odds start at 0.001%, rise slowly, ~5% at pull 159, guaranteed featured character at pull 180; counter resets on success. After owning all 5★ characters, soft pity for 6★ increases by 1000 pulls per 6★ owned with a hard cap at 2000.
4. Duplicate logic:
   - Before completing the 5★ roster: 25% chance to pull a duplicate, 75% new 5★.
   - After collecting all 5★ characters: 25% chance to get a duplicate of a heavily stacked 5★, 75% chance for a 5★ with few stacks; 6★ rolls remain extremely rare.
5. Vitality bonus: first duplicate adds 0.01%; each additional stack adds 5% more than the previous increment (0.01%, 0.0105%, 0.011025%, ...). Vitality increases EXP gain and all other stats.
6. Failed pulls give upgrade items (1★–4★) for each damage type—Generic, Light, Dark, Wind, Lightning, Fire, and Ice; dual-type characters require both types.
   - Player stat upgrades require collecting 4★ items from all non-Generic damage types to eventually choose a base damage type.
   - Costs: 1000×1★, 500×2★, 100×3★, or 20×4★ items per upgrade level.
   - 125 lower-star items combine into one higher star.
   - Trading 10×4★ items grants one additional pull.
   - Infusing a character outside runs lets players pick which stat to boost: 45×4★ items per tier for normal stats, 180×4★ for Vitality or similar power stats.
7. 6★ characters are dual damage types (e.g., Lady Fire and Ice, Persona Light and Dark) and are far rarer than 5★; even at full pity they appear only ~0.01% of the time.
8. Star colors are shared across all systems: 1★ gray, 2★ blue, 3★ green, 4★ purple, 5★ red, 6★ gold.
9. Provide crafting menus for converting items to higher stars or extra pulls.
10. Code structure:
    - Implement a `GachaManager` handling pity counts, roll tables, and reward serialization.
    - Define `UpgradeItem` and `Character` dataclasses to represent inventory pieces and recruitable units.
    - Store upgrade items and character stacks in the encrypted save database for cross-run persistence.
11. Party picker lets players choose four owned characters plus the player before starting a run, and gacha recruits can join the party immediately after they are pulled.
