# Shop Room

Offers upgrade items and cards for gold with a reroll option.

- **Stock** – three random items roll from a small pool and display name, star rating, and price. Buttons disable after buying.
- **Reroll** – spending 10 gold refreshes the entire stock.
- **Persistence** – exiting saves remaining gold and acquired items through `save_player`.
- **Spawn rules** – `ShopRoom.should_spawn` ensures at least one shop appears per floor by tracking spawns in `spawns_per_floor`.

## Pricing

Cards and relics share a star-based pricing table:

| Stars | Price (gold) |
| ----- | ------------ |
| 1★    | 20           |
| 2★    | 50           |
| 3★    | 100          |
| 4★    | 200          |
| 5★    | 500          |

These are base prices. Each pressure level multiplies the cost by **1.26**, and when
pressure is above zero a final \u00b15\% variation is applied. Run modifiers can also
stack shop multipliers, tax overrides, or custom variance bands. The backend caches
these derived values inside the `RunModifierContext` so shop rooms can reuse the
math without recomputing the wizard metadata:

```
multiplier = context.shop_multiplier  # includes pressure and modifier effects
variance_low, variance_high = context.shop_variance
final_price = floor(base_price * multiplier * rand(variance_low, variance_high))
```

The reroll action always costs **10 gold** and is unaffected by pressure.

### Star Modifiers

Base star rolls are weighted toward low ranks (70% 1★, 20% 2★, 10% 3★). High party rare-drop rate (`rdr`) can promote an item to a higher star rank:

- `rdr` ≥ 10 may raise the star level by one with a chance of `min(rdr / 100, 99%)`.
- `rdr` ≥ 10,000 may raise it again with a chance of `min(rdr / 100000, 99%)`.

These promotions are checked sequentially and cap at 5★.

## Testing

Run the backend test suite to verify pricing logic and stock updates:

```bash
uv run pytest backend/tests/test_shop_room.py
```

The frontend shop menu will gain automated coverage once implemented:

```bash
cd frontend
bun test
```

The Svelte frontend exposes a stub `ShopMenu` built with `MenuPanel` that lists stock and provides **Buy**, **Reroll**, and **Leave** actions.

Serialized payloads now include the modifier context metadata hash, the applied
shop multipliers, per-node encounter bonuses, and the normalised modifier stack
mapping so the frontend can confirm the active effects.
