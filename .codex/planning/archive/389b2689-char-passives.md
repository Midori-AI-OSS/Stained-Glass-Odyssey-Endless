# Character Passive Planning

Planned passive abilities for each player character. Use this list to track which characters have defined passives and which still need design work.

## Ally
Overload – Ally fights with twin daggers, granting two attacks per action.
Each pair of strikes builds 10 Overload charge and unused charge decays by
5 per turn when the stance is inactive. At 100 charge she may trigger an
Overload stance that doubles her attack count and makes each hit deal 30%
more damage but also causes her to take 40% more damage from all sources.
While Overload is active, Ally cannot receive HoT ticks and her maximum
recoverable HP is capped at 20% of normal, making excess health impossible
to heal. Overload drains 20 charge per turn and ends immediately if she is
defeated or charge is depleted.

## Becca
Menagerie Bond – Becca rescues jellyfish from the coastal Menagerie and
can call one to battle by spending 10% of her current HP; this action has a
one-turn cooldown. Only one summon can be active at a time. Each time she
rotates to a different jellyfish, the previous companion disperses into a
lingering spirit that grants Becca and her current pet +5% attack and
defense for the rest of the encounter via a stacking `StatModifier`. If a
pet is defeated, it still leaves a spirit that provides a stack.

## Bubbles
Bubble Burst – Bubbles' damage type shifts randomly each turn. Hitting an
enemy applies a Bubble stack; at three stacks the bubbles pop, dealing
area damage of the last element used to all combatants and leaving a
two-turn DoT of that element on enemies. Each burst also grants Bubbles a
permanent +10% attack buff, then resets his damage type for the next turn.

## Carly
Guardian's Aegis – Carly protects the party by healing the most injured
ally each turn for a small amount based on her defense. When she takes a
hit, the mitigation step is applied twice before damage is dealt,
effectively squaring her mitigation for that attack. Each time she is hit
she gains two mitigation stacks for the rest of the fight and taunts foes,
forcing them to target her. When she uses her ultimate, she grants all
allies mitigation equal to half of her own and reduces her mitigation by
the same amount.

## Ixia
Tiny Titan – Ixia gains four times the normal HP from Vitality and
converts 500% of current Vitality into attack. Each time Ixia is hit,
Vitality increases by 0.01 for the rest of the battle, encouraging a
bruiser playstyle. This Vitality bonus also reduces incoming damage
slightly and grants a minor HoT each turn while active.

## Graygray
Counter Maestro – Graygray retaliates after every hit taken, dealing 50%
of the damage received back at the attacker with his current element.
Damage from DoT ticks also triggers his counter. Each successful counter
grants him +5% attack and a one-turn mitigation buff.

## Hilander
Critical Ferment – Hilander builds 5% crit rate and 10% crit damage each
time he lands a hit, stacking up to 20 times. On a critical strike he
unleashes an Aftertaste hit dealing 25% of the original damage with a
random element, then consumes one stack of his built-up crit bonuses.

## Kboshi
Flux Cycle – At the start of each turn Kboshi has a high chance to switch
to a random damage type. If his element fails to change, he gains a 20%
damage bonus and a small HoT for that turn, stacking until a change
occurs. Changing element removes the stacks but applies a brief mitigation
debuff to all foes.

## Lady Darkness
Eclipsing Veil – DoTs Lady Darkness inflicts last one extra turn. Whenever
any DoT ticks on the battlefield, she siphons 1% of the damage as a HoT on
herself. Resisting a debuff grants her +5% attack for the remainder of the
fight.

## Lady Echo
Resonant Static – Each DoT on her target increases Lady Echo's chain
lightning ping damage by 10%. Landing consecutive hits on the same target
grants the party +2% crit rate, stacking up to ten times and resetting
when she changes targets.

## Lady Fire and Ice
Duality Engine – Alternating between fire and ice attacks grants an
Elemental Flux stack that raises burn DoT and chill debuff potency by 5%.
Using the same element twice consumes all stacks to apply a small HoT to
allies and a mitigation debuff to foes.

## Lady Light
Radiant Aegis – HoTs applied by Lady Light also grant a one-turn shield
and +5% effect resistance. Cleansing a DoT heals allies for an additional
5% of their max HP and gives Lady Light +2% attack, stacking with no cap.

## Lady of Fire
Infernal Momentum – Fire's missing HP damage bonus is doubled for Lady of
Fire. Each time she takes damage she applies a short burn DoT to the
attacker, and any self-damage from Fire drain grants her a HoT equal to
half the amount for two turns.

## Luna
Lunar Reservoir – charge-based system supporting up to 200 charge points.
Every action Luna takes grants 1 charge point, and any external effect on her
grants 1 point. At 200 points she enters a boosted mode while charge remains
above 200, spending 50 points per turn.
Her attack count scales with her current charge level:
- below 35 charge: 2 hits
- 35–49 charge: 4 hits
- 50–69 charge: 8 hits
- 70–84 charge: 16 hits
- 85+ charge: 32 hits
Charge points accrue only from actions, not individual attack instances; each
attack still rolls DoTs, buffs, relics, and other modifiers.

## Mezzy
Gluttonous Bulwark – Mezzy's immense bulk grants 20% damage reduction and a
focus on Max HP growth. Each turn she siphons 1% of attack, defense, and
max HP from allies whose HP exceeds 20% of her max, applying the stolen
values as permanent `StatModifier` buffs. If an ally falls below that
threshold, she returns half of the stolen stats. Her damage reduction is
applied before mitigation and she is immune to allied debuffs but still
takes DoT damage normally.

## Mimic
Copies the player then applies a permanent 25% debuff to all copied stats
on spawn. Mimic also duplicates the player's passive at half strength but
cannot gain additional buffs during the battle.

## Player
Gains 1.35× more stats on level up (planned).

---

### Q&A

**Q:** What damage type do summons use?

**A:** Summons roll a random damage type each action with high odds of matching their summoner's element.

**Q:** How strong should summons be relative to their summoners?

**A:** Summons start with 50% of their summoner's base stats, scaling proportionally.

**Q:** What other mechanics could enhance Carly's tank passive?

**A:** Ideas include counterattacks on blocked hits or temporary shields for allies she heals.

**Q:** How do DoTs and HoTs behave in combat?

**A:** Each tick uses the `EffectManager` to apply damage or healing and
emits an event before resolving, allowing passives to react to the tick.

**Q:** How are buffs and debuffs implemented?

**A:** Temporary stat changes use `StatModifier` effects created via
`create_stat_buff`, which stack and expire based on turn counters.
