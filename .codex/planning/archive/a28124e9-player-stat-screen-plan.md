# Player Stat Screen

1. Overlay displays and groups data:
   - **Core stats:** HP, Max HP (MHP), EXP, Level, EXP buff multiplier, Actions per Turn.
   - **Offense:** Attack, Crit Rate, Crit Damage, Effect Hit Rate, base damage type.
   - **Defense:** Defense, Mitigation, Regain, Dodge Odds, Effect Resistance.
   - **Vitality:** boosts EXP gain and all other stats; lowers damage taken down to a minimum of 1 and buffs damage dealt, healing, and DoT damage; shown separately because it influences both offense and defense.
   - **Advanced:** Action Points, Actions per Turn, cumulative Damage Taken/Dealt, and Kills.
   - **Status:**
     - *Passives:* list all active entries from `plugins/passives`.
     - *DoTs:*
        - `Bleed` – physical wounds that bypass mitigation and deal 2% Max HP per turn.
        - `Celestial Atrophy` – light damage that also lowers the target's Attack each tick.
        - `Abyssal Corruption` – dark damage that spreads to nearby foes when the target falls.
        - `Abyssal Weakness` – dark damage that reduces Defense while active.
        - `Gale Erosion` – wind damage stripping 1% Mitigation per tick.
        - `Charged Decay` – lightning damage with a 10% stun chance on the final tick.
        - `Frozen Wound` – ice damage that slows action speed by 5% each turn.
        - `Blazing Torment` – fire damage that inflicts an extra tick whenever the target acts.
        - `Cold Wound` – mild ice damage that stacks up to five times.
        - `Twilight Decay` – light/dark damage draining 0.5% Vitality per turn.
        - `Impact Echo` – physical shockwaves repeating 50% of the last hit for three turns.
        - DoTs stack indefinitely unless a specific effect lists a cap (only `Cold Wound` has a five-stack limit).
        - All DoT-induced stat changes are cleared after each fight unless a card explicitly makes them permanent.
     - *HoTs:*
        - `Regeneration` – heals a flat amount (5 HP) each turn for three turns.
        - `PlayerName's Echo` – when a generic-type ally deals damage, party members heal for 20% of that damage over five turns.
        - `PlayerName's Heal` – certain themed allies give wounded teammates an instant heal plus 1% Max HP per turn for five turns.
        - HoTs have no stack cap and, like DoTs, expire when the battle ends unless a card states otherwise.
     - *Damage types:*
        - `Generic`
        - `Light`
        - `Dark`
        - `Wind`
        - `Lightning`
        - `Fire`
        - `Ice`
     - *Relics:* show collected stacks by name and star rank.
   - Track stats using Python's arbitrary-precision integers; chunk internally only if performance demands it and display formatted single values to players.
2. Bind fields to player data and refresh at a user-defined rate (default every 5 frames, adjustable from every frame to every 10 frames; values outside this range clamp to the nearest limit).
3. ESC or close returns to the previous scene and respects the Options pause setting.
4. Code structure:
   - Create `StatPanel` widgets for each category and populate from a shared `Stats` dataclass.
   - Expose hooks so plugins can append custom lines to the Status section.
