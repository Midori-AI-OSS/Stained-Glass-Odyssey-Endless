# Gacha endpoints

Exposes gacha pulls and state through Quart.

## Routes
- `GET /gacha` returns the current pity counter, element-based upgrade item
-  totals, owned characters with duplicate stacks, and whether auto-crafting is
-  enabled.
- `POST /gacha/pull` accepts a JSON body with `count` (1, 5, or 10) and returns
  pull results plus the updated state. Each pull consumes one ticket; the server
  responds with **403** when tickets are insufficient. Results include `rarity`
  for character (5★ or 6★) and item pulls (1★–4★) keyed by element. Higher pity
  improves item rarity on failed pulls.
- `POST /gacha/auto-craft` toggles automatic crafting of upgrade items within an
  element. It accepts `{ "enabled": true | false }` and returns the updated
  flag.

## Banner rotation
- Two rotating `custom` banners operate on a three-day cadence. Each cycle
  selects one featured character from the owned pool and one from the unowned
  pool when both buckets contain options, avoiding duplicate assignments unless
  no other choices remain.

## Testing
- `uv run pytest tests/test_gacha.py`
