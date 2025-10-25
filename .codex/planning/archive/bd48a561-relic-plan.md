# Relic Design

Parent: [Web Game Plan](8a7d9c1e-web-game-plan.md)

## Guiding Principles
- Relics are permanent passives that trigger automatically once obtained.
- Multiple copies can be collected and their effects stack without cap.
- Strength follows star rank just like cards: low stars give tiny boosts; high stars can reshape entire runs.
- *Aftertaste* is a damage FX with a base pot of 25 and a random 0.1–1.5 modifier; several relics / cards reference this effect.
- *Critical Boost* grants +0.5% Crit Rate and +5% Crit Damage per stack but vanishes when the unit is hit.

## Star Rank Identity

### 1★ Relics
Baseline boosts that introduce mechanical hooks (bleed payoffs, small shields, gold tweaks) without defining a build. Use them to gently nudge strategies rather than overhaul parties.

### 2★ Relics
Push into specialised builds—reflect damage, echo actions, or provide conditional shielding. They should encourage players to experiment with synergy while keeping maintenance overhead low.

### 3★ Relics
Act as the first major inflection point. These relics may tax the party (HP drain, speed sacrifices) in exchange for snowballing bonuses or encounter-wide debuffs.

### 4★ Relics
Deliver dramatic tempo manipulation or encounter scripting. Think battlefield control, polarising buffs, or run-altering map changes. These should feel risky but rewarding to pilot.

### 5★ Relics
Legendary effects that redefine a run. They often trade survivability for overwhelming power, add unique win conditions, or rewrite drop tables entirely.

## Canonical Source of Truth
Implementation details, numerical tuning, and descriptive copy live in the plugins under `backend/plugins/relics/`. Update each relic's `about` string and behaviour methods directly in the plugin—this planning archive now captures design intent only.
