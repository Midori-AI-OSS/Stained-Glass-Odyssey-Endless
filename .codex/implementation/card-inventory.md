# Card Inventory

`CardInventory.svelte` lists collected cards inside a shared `MenuPanel`. The
menu shows each card's name in a wrapped grid and displays a placeholder message
when no cards are owned. The inventory can be accessed during combat to review
collected cards and their effects. The broader `InventoryPanel.svelte` now also
shows upgrade materials in a Star‑Rail‑style grid with quantity badges and a
detail pane.

## Testing
- `bun test`
## 1★ Cards
- Micro Blade – +3% ATK; Attacks have a 6% chance to deal +8% bonus physical damage on hit
- Polished Shield – +3% DEF; When an ally resists a DoT/debuff, grant them +3 DEF for 1 turn
- Sturdy Vest – +3% HP; When below 35% HP, gain a small 3% HoT for 2 turns
- Lucky Coin – +3% Crit Rate; On critical hit, 20% chance to refund a tiny energy (or small resource) to the attacker
- Sharpening Stone – +3% Crit Damage; After scoring a crit, gain +2% crit damage for 2 turns
- Mindful Tassel – +3% Effect Hit Rate; First debuff applied each battle has +5% potency
- Calm Beads – +3% Effect Res; On resisting a debuff, gain +1 small energy for next action
- Energizing Tea – +3% Regain; At battle start, gain +1 energy on the first turn
- Thick Skin – +3% Bleed Resist; When afflicted by Bleed, 50% chance to reduce its duration by 1
- Balanced Diet – +3% HP & +3% DEF; When healed, grant the healed unit +2% DEF for 1 turn
- Lightweight Boots – +3% Dodge Odds; On successful dodge, heal 2% HP to the dodging unit
- Sturdy Boots – +3% Dodge Odds & +3% DEF; Provides flat defensive bonuses with no secondary effect
- Expert Manual – +3% EXP Gain; 5% chance to give a small extra XP on a kill once per battle
- Steel Bangles – +3% Mitigation; On attack hit, 5% chance to reduce the target's next attack damage by 3%
- Enduring Charm – +3% Vitality; When below 30% HP, gain +3% Vitality for 2 turns
- Keen Goggles – +3% Crit Rate & +3% Effect Hit Rate; Landing a debuff grants +1% crit rate for next action (stack up to 3)
- Honed Point – +4% ATK; First attack vs an unmarked enemy gains +10% armor penetration for that hit
- Fortified Plating – +4% DEF; Reduce damage from the first hit each turn by 6%
- Rejuvenating Tonic – +4% Regain; When using a heal, heal an additional +1% HP
- Adamantine Band – +4% HP; If lethal damage would reduce you below 1 HP, reduce that damage by 10%
- Precision Sights – +4% Crit Damage; After scoring a crit, gain +2% crit damage for 2 turns (small stacking)
- Steady Grip – +5% ATK; Critical hits can overcharge into 4× super crits based on crit rate (≈5% chance per 25% crit)
- Inspiring Banner – +2% ATK & +2% DEF; At battle start, grant a random ally +2% ATK for 2 turns
- Tactical Kit – +2% ATK & +2% HP; Once per battle, convert 1% HP to +2% ATK for one action
- Bulwark Totem – +2% DEF & +2% HP; When lethal damage would drop an ally to 0 HP, siphon 5% of that hit from a healthy teammate to restore the victim (tiny soak)
- Farsight Scope – +3% Crit Rate; Attacks against enemies under 50% HP gain +6% crit rate
- Coated Armor – +3% Mitigation & +3% DEF; When mitigation reduces incoming damage, heal 1% HP
- Guiding Compass – +3% EXP Gain & +3% Effect Hit Rate; First battle of a run grants a small extra XP bonus
- Swift Bandanna – +3% Crit Rate & +3% Dodge Odds; On dodge, gain +1% crit rate for next action
- Reinforced Cloak – +3% DEF & +3% Effect Res; 30% chance to reduce the starting duration of long debuffs by 1
- Vital Core – +3% Vitality & +3% HP; When below 30% HP, gain +3% Vitality for 2 turns
- Enduring Will – +3% Mitigation & +3% Vitality; If no allies die during combat, grant +1 mitigation next battle
- Battle Meditation – +3% EXP Gain & +3% Vitality; If all allies start at full HP, grant +2% energy for the first turn
- Guardian Shard – +2% DEF & +2% Mitigation; At battle end, if no allies died, grant +1 small mitigation for the next battle
- Spiked Shield – +3% ATK & +3% DEF; When mitigation triggers (block threshold), deal small retaliatory damage (3% of attack)
- 
## 2★ Cards
- Critical Focus – +55% ATK; start of turn grants Critical Boost stack
- Critical Transfer – Ultimates absorb Critical Boost stacks; +4% ATK per stack for that turn
- Iron Guard – +55% DEF; taking damage gives all allies +10% DEF for 1 turn
- Swift Footwork – +1 action per turn; first action each combat is free
- Mystic Aegis – +55% Effect Res; resisting a debuff heals 5% Max HP
- Vital Surge – +55% Max HP; while below 50% HP, +55% ATK
- Elemental Spark – +55% ATK & +55% Effect Hit Rate; one ally's debuffs gain +5% potency
- 
## 3★ Cards
- Critical Overdrive – +255% ATK; while an ally has Critical Boost, they gain +10% Crit Rate and convert excess Crit Rate to +2% Crit Damage.
- Iron Resurgence – +200% DEF & +200% HP; the first ally death revives at 10% HP and refreshes every 4 turns.
- Arc Lightning – +255% ATK; every attack chains 50% damage to a random foe.

## 4★ Cards
- Overclock – +240% ATK & +240% Effect Hit Rate; at the start of each battle, all allies immediately take two actions back to back.
- Iron Resolve – +240% DEF & +240% HP; the first time an ally dies, revive them at 30% HP. This effect refreshes every 3 turns.
- Arcane Repeater – +240% ATK; each attack has a 30% chance to immediately repeat at 50% power.
