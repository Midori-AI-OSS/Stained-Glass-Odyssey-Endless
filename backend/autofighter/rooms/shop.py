from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any

from services.run_configuration import RunModifierContext
from services.run_configuration import get_shop_modifier_summaries

from ..cards import card_choices
from ..party import Party
from ..passives import PassiveRegistry
from ..relics import _registry as relic_registry
from . import Room
from .utils import _serialize

PRICE_BY_STARS = {1: 20, 2: 50, 3: 100, 4: 200, 5: 500}
REROLL_COST = 10


def _configured_cost(
    base: int,
    *,
    pressure: int,
    context: RunModifierContext | None,
    rng: random.Random | None = None,
) -> int:
    random_source = rng or random
    if context is not None:
        multiplier = max(float(context.shop_multiplier), 0.0)
        variance = getattr(context, "shop_variance", (0.95, 1.05))
        try:
            low, high = float(variance[0]), float(variance[1])
        except Exception:
            low, high = 0.95, 1.05
    else:
        multiplier = 1.26 ** max(pressure, 0)
        low, high = 0.95, 1.05
    if high > low:
        multiplier *= random_source.uniform(low, high)
    return int(base * multiplier)


def _tax_amount(
    base_price: int,
    pressure: int,
    items_bought: int,
    context: RunModifierContext | None,
) -> int:
    if items_bought <= 0:
        return 0
    rate = 0.01 * (max(pressure, 0) + 1) * items_bought
    if context is not None:
        try:
            rate *= max(float(context.shop_tax_multiplier), 0.0)
        except Exception:
            pass
    return int(math.ceil(base_price * rate))


def _taxed_price(
    base_price: int,
    pressure: int,
    items_bought: int,
    context: RunModifierContext | None,
) -> int:
    tax = _tax_amount(base_price, pressure, items_bought, context)
    return base_price + tax


def _apply_tax_to_stock(
    stock: list[dict[str, Any]],
    pressure: int,
    items_bought: int,
    context: RunModifierContext | None,
) -> list[dict[str, Any]]:
    repriced: list[dict[str, Any]] = []
    for entry in stock:
        base_price = int(entry.get("base_price") or entry.get("price") or entry.get("cost") or 0)
        taxed = _taxed_price(base_price, pressure, items_bought, context)
        updated = {
            **entry,
            "base_price": base_price,
            "price": taxed,
            "cost": taxed,
            "tax": taxed - base_price,
        }
        repriced.append(updated)
    return repriced


def serialize_shop_payload(
    party: Party,
    stock: list[dict[str, Any]] | None,
    pressure: int,
    items_bought: int,
    *,
    context: RunModifierContext | None,
    transactions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Serialize a shop state without mutating the underlying room."""

    repriced_stock = _apply_tax_to_stock(stock or [], pressure, items_bought, context)

    try:
        registry_map = relic_registry()
    except Exception:
        registry_map = {}

    enriched_stock: list[dict[str, Any]] = []
    for entry in repriced_stock:
        enriched = dict(entry)
        if enriched.get("type") == "relic":
            rid = enriched.get("id")
            stacks = party.relics.count(rid)
            enriched["stacks"] = stacks
            about = None
            try:
                cls = registry_map.get(rid)
                if cls is not None:
                    about = cls().describe(stacks + 1)
            except Exception:
                about = None
            if about:
                enriched["about"] = about
        enriched_stock.append(enriched)

    party_data = [_serialize(member) for member in party.members]
    payload = {
        "result": "shop",
        "party": party_data,
        "gold": party.gold,
        "relics": party.relics,
        "cards": party.cards,
        "rdr": party.rdr,
        "stock": enriched_stock,
        "items_bought": items_bought,
        "card": None,
        "foes": [],
        "transactions": transactions or [],
    }
    if context is not None:
        payload["modifier_context"] = {
            "metadata_hash": context.metadata_hash,
            "shop_multiplier": context.shop_multiplier,
            "shop_tax_multiplier": context.shop_tax_multiplier,
            "shop_variance": list(context.shop_variance),
            "encounter_slot_bonus": context.encounter_slot_bonus,
            "pressure": context.pressure,
            "elite_spawn_bonus_pct": context.elite_spawn_bonus_pct,
            "prime_spawn_bonus_pct": context.prime_spawn_bonus_pct,
            "glitched_spawn_bonus_pct": context.glitched_spawn_bonus_pct,
            "modifier_stacks": dict(context.modifier_stacks),
        }
    config_snapshot = getattr(party, "run_config", None)
    if isinstance(config_snapshot, dict):
        run_type = None
        run_type_info = config_snapshot.get("run_type")
        if isinstance(run_type_info, dict):
            run_type = run_type_info.get("id")
        modifiers = {}
        raw_modifiers = config_snapshot.get("modifiers")
        if isinstance(raw_modifiers, dict):
            for key, value in raw_modifiers.items():
                details = value.get("details") if isinstance(value, dict) else None
                stacks = details.get("stacks") if isinstance(details, dict) else None
                if stacks is not None:
                    modifiers[key] = stacks
        summary = {
            "run_type": run_type,
            "modifiers": modifiers,
        }
        if context is not None:
            summary["metadata_hash"] = context.metadata_hash
        payload["run_configuration"] = {k: v for k, v in summary.items() if v}
        shop_summaries = get_shop_modifier_summaries(config_snapshot)
        if shop_summaries:
            payload["shop_modifiers"] = shop_summaries

    return payload


def _apply_rdr_to_stars(stars: int, rdr: float) -> int:
    for threshold in (10.0, 10000.0):
        if stars >= 5 or rdr < threshold:
            break
        chance = min(rdr / (threshold * 10.0), 0.99)
        if random.random() < chance:
            stars += 1
        else:
            break
    return stars


def _pick_shop_stars() -> int:
    roll = random.random()
    if roll < 0.7:
        return 1
    if roll < 0.9:
        return 2
    return 3


def _generate_stock(
    party: Party,
    pressure: int,
    context: RunModifierContext | None,
) -> list[dict[str, Any]]:
    stock: list[dict[str, Any]] = []
    rng = random
    for _ in range(2):
        stars = _apply_rdr_to_stars(_pick_shop_stars(), party.rdr)
        choice = card_choices(party, stars, count=1)
        if choice:
            card = choice[0]
            base = PRICE_BY_STARS.get(card.stars, 0)
            base_price = _configured_cost(base, pressure=pressure, context=context, rng=rng)
            stock.append(
                {
                    "id": card.id,
                    "name": card.name,
                    "stars": card.stars,
                    "type": "card",
                    "base_price": base_price,
                    "price": base_price,
                    "cost": base_price,
                    "tax": 0,
                }
            )
    all_relics = [cls() for cls in relic_registry().values()]
    seen_relics: set[str] = set()
    relic_list = []
    for _ in range(6):
        stars = _apply_rdr_to_stars(_pick_shop_stars(), party.rdr)
        pool = [r for r in all_relics if r.stars == stars and r.id != "fallback_essence" and r.id not in seen_relics]
        if not pool:
            continue
        relic = rng.choice(pool)
        seen_relics.add(relic.id)
        relic_list.append(relic)
    for relic in relic_list:
        base = PRICE_BY_STARS.get(relic.stars, 0)
        base_price = _configured_cost(base, pressure=pressure, context=context, rng=rng)
        stock.append(
            {
                "id": relic.id,
                "name": relic.name,
                "stars": relic.stars,
                "type": "relic",
                "base_price": base_price,
                "price": base_price,
                "cost": base_price,
                "tax": 0,
            }
        )
    rng.shuffle(stock)
    return stock


@dataclass
class ShopRoom(Room):
    """Shop rooms allow relic purchases and heal the party slightly."""

    async def resolve(self, party: Party, data: dict[str, Any]) -> dict[str, Any]:
        action = data.get("action", "")
        registry = PassiveRegistry()
        if not getattr(self.node, "visited", False):
            heal = int(sum(m.max_hp for m in party.members) * 0.05)
            for member in party.members:
                await registry.trigger("room_enter", member)
                await member.apply_healing(heal)
            self.node.visited = True

        items_bought = int(getattr(self.node, "items_bought", 0))
        if items_bought < 0:
            items_bought = 0
        self.node.items_bought = items_bought

        context = getattr(self.node, "run_modifier_context", None)
        if isinstance(context, dict):
            try:
                context = RunModifierContext.from_dict(context)
                setattr(self.node, "run_modifier_context", context)
            except Exception:
                context = None
        if context is None:
            context = getattr(party, "run_modifier_context", None)
            if context is not None:
                setattr(self.node, "run_modifier_context", context)

        stock = getattr(self.node, "stock", [])
        if not stock:
            stock = _generate_stock(party, self.node.pressure, context)

        stock = _apply_tax_to_stock(stock, self.node.pressure, items_bought, context)
        self.node.stock = stock

        transactions: list[dict[str, Any]] = []

        if action == "reroll":
            if party.gold >= REROLL_COST:
                party.gold -= REROLL_COST
                stock = _generate_stock(party, self.node.pressure, context)
                stock = _apply_tax_to_stock(stock, self.node.pressure, items_bought, context)
                self.node.stock = stock
                transactions.append(
                    {
                        "item_type": "reroll",
                        "item_id": None,
                        "cost": REROLL_COST,
                        "action": "reroll",
                    }
                )
        else:
            purchases: list[dict[str, Any]] = []
            payload_items = data.get("items")
            if isinstance(payload_items, list) and payload_items:
                purchases = [p for p in payload_items if isinstance(p, dict)]
            elif isinstance(payload_items, dict) and payload_items:
                purchases = [payload_items]
            else:
                item_id = data.get("id") or data.get("item")
                cost_value = data.get("cost") or data.get("price")
                if item_id and cost_value is not None:
                    purchases = [
                        {"id": item_id, "cost": cost_value},
                    ]

            for purchase in purchases:
                item_id = purchase.get("id") or purchase.get("item")
                cost_value = purchase.get("cost") or purchase.get("price")
                if not item_id or cost_value is None:
                    continue

                try:
                    cost = int(cost_value)
                except (TypeError, ValueError):
                    continue

                entry = next((s for s in stock if s.get("id") == item_id), None)
                if entry is None:
                    continue

                base_price = int(entry.get("base_price") or 0)
                expected_cost = _taxed_price(
                    base_price,
                    self.node.pressure,
                    items_bought,
                    context,
                )
                if cost != expected_cost or party.gold < expected_cost:
                    continue

                party.gold -= expected_cost
                if entry.get("type") == "card":
                    party.cards.append(item_id)
                else:
                    party.relics.append(item_id)

                stock.remove(entry)

                items_bought += 1
                self.node.items_bought = items_bought
                stock = _apply_tax_to_stock(
                    stock,
                    self.node.pressure,
                    items_bought,
                    context,
                )
                self.node.stock = stock
                transactions.append(
                    {
                        "item_type": entry.get("type"),
                        "item_id": item_id,
                        "cost": expected_cost,
                        "action": "purchase",
                    }
                )

            self.node.stock = stock

        payload = serialize_shop_payload(
            party,
            stock,
            self.node.pressure,
            items_bought,
            context=context,
            transactions=transactions,
        )
        self.node.stock = payload["stock"]
        return payload
