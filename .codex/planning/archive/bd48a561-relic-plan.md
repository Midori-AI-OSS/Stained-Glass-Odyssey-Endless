# Relic Design

Parent: [Web Game Plan](8a7d9c1e-web-game-plan.md)

## Guiding Principles
- Relics are permanent passives that trigger automatically once obtained.
- Multiple copies can be collected and their effects stack without cap.
- Strength follows star rank just like cards: low stars give tiny boosts; high stars can reshape entire runs.
- *Aftertaste* is a damage FX with a base pot of 25 and a random 0.1–1.5 modifier; several relics / cards reference this effect.
- *Critical Boost* grants +0.5% Crit Rate and +5% Crit Damage per stack but vanishes when the unit is hit.

## 1★ Relics
 - [ ] **Rusty Buckle** – At the start of each turn, all allies bleed for 5% of their Max HP per stack. After the party loses HP equal to its total Max HP (threshold rises by 50% per additional stack), unleash 5 hits of Aftertaste at random foes, plus 3 hits per extra stack. Each hit deals 0.5% of the cumulative HP lost.
 - [x] **Threadbare Cloak** – Allies start battle with a shield equal to 3% Max HP; each copy adds another 3%.
 - [x] **Lucky Button** – +3% Crit Rate; missed crits add +3% Crit Rate next turn.
 - [x] **Bent Dagger** – +3% ATK; whenever a foe dies, gain +1% ATK for the rest of combat per stack.
 - [x] **Old Coin** – +3% gold earned; first shop purchase costs 3% less plus 3% per stack.
 - [x] **Shiny Pebble** – +3% DEF; the first time an ally is hit, they gain +3% mitigation for 1 turn.
 - [x] **Herbal Charm** – Recover 0.5% HP per turn plus 0.5% per stack.
 - [x] **Tattered Flag** – +3% party Max HP; when an ally falls, all survivors gain +3% ATK.
 - [x] **Wooden Idol** – +3% Effect Res; resisting a debuff grants +1% Effect Res for the next turn per stack.
 - [x] **Pocket Manual** – +3% damage; every 10th hit deals an extra 3% damage as Aftertaste.
 - [x] **Featherweight Anklet** – +2% SPD per stack (multiplicative); first action each ally takes per battle grants +6% SPD per stack for 1 turn.
 - [x] **Field Rations** – After each battle, heal 2% Max HP per stack and grant +1 ultimate charge per stack to all allies.

## 2★ Relics
 - [x] **Vengeful Pendant** – Whenever an ally is hit, deal 15% of the damage taken back to the attacker, plus 15% per additional copy.
 - [x] **Arcane Flask** – After an ally uses their Ultimate, grant a shield equal to 20% Max HP plus 20% per stack.
 - [x] **Echo Bell** – The first action each ally takes every battle repeats at 15% power plus 15% per stack.
 - [x] **Frost Sigil** – Each hit on a foe applies a chill that deals 5% ATK as one hit of Aftertaste plus one additional hit per stack.
 - [x] **Ember Stone** – When an ally below 25% HP is hit, deal a burn equal to 50% ATK plus 50% per stack to the attacker.
 - [x] **Guardian Charm** – At the start of combat, the ally with the lowest HP gains +20% DEF plus 20% per stack.
 - [x] **Killer Instinct** – When an ally uses their Ultimate, they gain +75% ATK for that turn; if they kill a foe, they immediately take another turn.

## 3★ Relics
 - [ ] **Greed Engine** – All characters lose 1% HP per turn plus 0.5% per stack. Earn 50% more gold plus 25% per stack and increase rare drop rate by 0.5% plus 0.1% per additional stack.
 - [ ] **Stellar Compass** – Critical hits grant +1.5% ATK and +1.5% gold for the rest of combat, stacking without limit.
 - [ ] **Echoing Drum** – The first attack an ally uses each battle repeats at 25% power plus 25% per stack.

## 4★ Relics
  - [ ] **Null Lantern** – Shops no longer appear. All foes are buffed by 150% for each fight cleared while holding this relic. Every fight now drops 1 pull plus 1 per stack.
  - [x] **Traveler's Charm** – When an ally is hit, they gain +25% DEF and +10% mitigation for the next turn plus 25% DEF and +10% mitigation per stack.
  - [x] **Timekeeper's Hourglass** – At the start of each turn, there is a 10% chance plus 1% per stack for all allies to take an additional turn.

## 5★ Relics
- **Paradox Hourglass** – At the start of combat there is a 60% chance, reduced as allies are missing (0% if only one remains), to kill 1 random ally plus 1 per stack. Survivors gain 200% to all stats plus 100% per stack, and all foes lose 4× DEF plus 1× per stack down to a minimum of 100 total DEF.
- **Soul Prism** – After combat and at the start of a new round, revive fallen allies at 1% HP but reduce their Max HP by 75% for the rest of the run; buff their DEF and mitigation by 5%. Each additional copy reduces the penalty by 5% and adds 2% to the buffs.
- **Omega Core** – At the start of combat, all allies gain +500% to all stats; after 10 turns the party begins taking 1% HP damage each turn, increasing by 1% per extra turn. Each stack adds 2 turns before the damage begins.
