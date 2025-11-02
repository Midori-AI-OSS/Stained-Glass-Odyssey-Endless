# Card Design

Parent: [Web Game Plan](8a7d9c1e-web-game-plan.md)

## Guiding Principles
- Cards are unique rewards with a single copy each.
- Strength scales by star rank: 1★ offers tiny bonuses, while 5★ radically changes how battles play out.
- *Aftertaste* is a damage FX with a base pot of 25 and a random 0.1–1.5 modifier; several relics / cards reference this effect.
- *Critical Boost* grants +0.5% Crit Rate and +5% Crit Damage per stack but vanishes when the unit is hit.

## Star Rank Targets

### 1★ Cards
Entry-tier cards should provide gentle stat bumps or situational perks that teach core mechanics. They often grant small heal-over-time effects, low-stakes resource gains, or minor mitigation so early floors feel forgiving without removing risk.

### 2★ Cards
Mid-tier cards convert those fundamentals into short bursts of power. Expect larger stat swings, conditional ult triggers, or battle-long buffs that reward players who maintain uptime. 2★ rewards frequently interact with shared systems such as Critical Boost or elemental stances.

### 3★ Cards
Three-star rewards lean into party-wide pivots. They can rescue failing runs through revives, wide shields, or chain damage that rewards mastery over status setups. Think of them as the bridge between utility and transformational play.

### 4★ Cards
Four-star cards redefine pacing with dramatic tempo shifts—extra turns, stance swaps, or revival loops that change how players script an encounter. They should feel aspirational without eclipsing 5★ chase pieces.

### 5★ Cards
Top-rarity cards fundamentally reshape a build. They deliver overwhelming stat spikes, summon allies, or impose global rules (gravity wells, time freezes, etc.). Treat them as capstone rewards for long runs and narrative milestones.

## Canonical Source of Truth
Card specifics—names, stat spreads, and descriptive copy—live directly inside the plugins under `backend/plugins/cards/`. Update each plugin's `about` string and helper methods when behaviour changes. This planning note now tracks intent only, leaving the roster details to the code that powers the game and documentation tooling.
