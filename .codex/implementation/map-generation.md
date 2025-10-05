# Map Generation and Pressure Scaling

The map generator builds deterministic floor layouts using a seeded
`MapGenerator`. Pressure Level influences both room structure and
combat difficulty, and modifier metadata enriches the generated nodes
with additional context for encounter assembly.

## Seed Tracking
Base seeds are persisted to `used_seeds.json`. Creating a `MapGenerator`
checks this list and raises a `ValueError` if a seed was used before.
This prevents regenerating identical maps across runs. The storage path
can be overridden with the `seed_store_path` argument for testing or
custom setups.

## Room Adjustments
- Base floors contain 10 primary nodes (start, shop/rest slots,
  battles, boss). Modifier stacks may flag individual battle rooms as
  `battle-prime` or `battle-glitched` when spawn odds increase.
- Per-room `encounter_bonus` values persist additional foe slots earned
  from pressure stacks and modifier bonuses so the foe factory can
  spawn the guaranteed extras deterministically.
- The run modifier context caches elite, prime, and glitched spawn
  percentages on every node so downstream systems do not need to
  recalculate the metadata hash or modifier maths.

## Enemy Scaling
Enemy stats scale with floor, room, and loop counts. Additional
Pressure Level modifiers are applied via
`autofighter.balance.pressure.apply_pressure` during battle setup, and
per-room bonuses feed into `_desired_count` to honour `encounter_bonus`
without re-running the configuration helper.
