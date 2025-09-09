from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any

from ..cards import card_choices
from ..party import Party
from ..passives import PassiveRegistry
from ..relics import _registry as relic_registry
from . import Room
from .utils import _serialize

PRICE_BY_STARS = {1: 20, 2: 50, 3: 100, 4: 200, 5: 500}
REROLL_COST = 10


def _pressure_cost(base: int, pressure: int) -> int:
    scale = 1.26**pressure
    if pressure:
        scale *= random.uniform(0.95, 1.05)
    return int(base * scale)


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


def _generate_stock(party: Party, pressure: int) -> list[dict[str, Any]]:
    stock: list[dict[str, Any]] = []
    for _ in range(2):
        stars = _apply_rdr_to_stars(_pick_shop_stars(), party.rdr)
        choice = card_choices(party, stars, count=1)
        if choice:
            card = choice[0]
            base = PRICE_BY_STARS.get(card.stars, 0)
            cost = _pressure_cost(base, pressure)
            stock.append(
                {
                    "id": card.id,
                    "name": card.name,
                    "stars": card.stars,
                    "type": "card",
                    "cost": cost,
                    "price": cost,
                }
            )
    # Offer up to 6 relics at the selected star tier; entries are unique
    # Shop relics: roll star rank per slot; allow owned, ensure uniqueness within this stock
    all_relics = [cls() for cls in relic_registry().values()]
    seen_relics: set[str] = set()
    relic_list = []
    for _ in range(6):
        stars = _apply_rdr_to_stars(_pick_shop_stars(), party.rdr)
        pool = [
            r
            for r in all_relics
            if r.stars == stars
            and r.id != "fallback_essence"
            and r.id not in seen_relics
        ]
        if not pool:
            continue
        relic = random.choice(pool)
        seen_relics.add(relic.id)
        relic_list.append(relic)
    for relic in relic_list:
        base = PRICE_BY_STARS.get(relic.stars, 0)
        cost = _pressure_cost(base, pressure)
        stock.append(
            {
                "id": relic.id,
                "name": relic.name,
                "stars": relic.stars,
                "type": "relic",
                "cost": cost,
                "price": cost,
            }
        )
    random.shuffle(stock)
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

        stock = getattr(self.node, "stock", [])
        if not stock:
            stock = _generate_stock(party, self.node.pressure)
            self.node.stock = stock

        if action == "reroll":
            if party.gold >= REROLL_COST:
                party.gold -= REROLL_COST
                stock = _generate_stock(party, self.node.pressure)
                self.node.stock = stock
        else:
            item_id = data.get("id") or data.get("item")
            cost = int(data.get("cost") or data.get("price") or 0)
            if item_id and cost:
                entry = next(
                    (s for s in stock if s["id"] == item_id and s["cost"] == cost),
                    None,
                )
                if entry and party.gold >= cost:
                    party.gold -= cost
                    if entry["type"] == "card":
                        party.cards.append(item_id)
                    else:
                        party.relics.append(item_id)
                    stock.remove(entry)
                    self.node.stock = stock

        # Enrich stock entries with stacking-aware descriptions for relics
        enriched_stock: list[dict[str, Any]] = []
        try:
            registry_map = relic_registry()
        except Exception:
            registry_map = {}
        for s in stock:
            if s.get("type") == "relic":
                rid = s.get("id")
                stacks = party.relics.count(rid)
                about = None
                try:
                    cls = registry_map.get(rid)
                    if cls is not None:
                        about = cls().describe(stacks + 1)
                except Exception:
                    about = None
                enriched = {**s, "stacks": stacks}
                if about:
                    enriched["about"] = about
                enriched_stock.append(enriched)
            else:
                enriched_stock.append(dict(s))

        party_data = [_serialize(p) for p in party.members]
        return {
            "result": "shop",
            "party": party_data,
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "rdr": party.rdr,
            "stock": enriched_stock,
            "card": None,
            "foes": [],
        }
