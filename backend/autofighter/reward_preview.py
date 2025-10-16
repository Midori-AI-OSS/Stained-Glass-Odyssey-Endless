from __future__ import annotations
from typing import Literal
from typing import Mapping
from typing import Iterable
from typing import Sequence
from typing import TypedDict


PreviewTarget = Literal["party", "foe", "run", "self", "allies"]
PreviewMode = Literal["percent", "flat", "multiplier"]


class RewardPreviewStat(TypedDict, total=False):
    """Structured description of a stat change applied by a reward."""

    stat: str
    mode: PreviewMode
    amount: float
    target: PreviewTarget
    stacks: int
    total_amount: float
    previous_total: float


class RewardPreviewTrigger(TypedDict, total=False):
    """Description of an event hook activated by a reward."""

    event: str
    description: str | None


class RewardPreviewPayload(TypedDict, total=False):
    """Serializable preview payload for staged rewards."""

    summary: str | None
    stats: list[RewardPreviewStat]
    triggers: list[RewardPreviewTrigger]


def _normalise_summary(summary: str | None) -> str | None:
    if summary is None:
        return None
    text = str(summary).strip()
    return text or None


def _normalise_triggers(
    triggers: Iterable[Mapping[str, object]] | None,
) -> list[RewardPreviewTrigger]:
    normalised: list[RewardPreviewTrigger] = []
    if not triggers:
        return normalised

    for trigger in triggers:
        if not isinstance(trigger, Mapping):
            continue
        event = str(trigger.get("event", "")).strip()
        if not event:
            continue
        entry: RewardPreviewTrigger = {"event": event}
        description = trigger.get("description")
        if isinstance(description, str):
            cleaned = description.strip()
            if cleaned:
                entry["description"] = cleaned
        normalised.append(entry)
    return normalised


def _stat_entries_from_effects(
    effects: Mapping[str, float] | None,
    *,
    stacks: int,
    previous_stacks: int = 0,
    target: PreviewTarget = "party",
) -> list[RewardPreviewStat]:
    if not isinstance(effects, Mapping):
        return []

    stats: list[RewardPreviewStat] = []
    for attr, raw_value in effects.items():
        try:
            pct = float(raw_value)
        except (TypeError, ValueError):
            continue
        entry: RewardPreviewStat = {
            "stat": str(attr),
            "mode": "percent",
            "amount": pct * 100,
            "target": target,
            "stacks": max(stacks, 1),
            "total_amount": ((1 + pct) ** max(stacks, 1) - 1) * 100,
        }
        if previous_stacks > 0:
            entry["previous_total"] = ((1 + pct) ** previous_stacks - 1) * 100
        stats.append(entry)
    return stats


def build_preview_from_effects(
    *,
    effects: Mapping[str, float] | None,
    summary: str | None = None,
    triggers: Iterable[Mapping[str, object]] | None = None,
    stacks: int = 1,
    previous_stacks: int = 0,
    target: PreviewTarget = "party",
) -> RewardPreviewPayload:
    """Construct a preview payload from standard reward metadata."""

    payload: RewardPreviewPayload = {
        "stats": _stat_entries_from_effects(
            effects,
            stacks=max(stacks, 1),
            previous_stacks=max(previous_stacks, 0),
            target=target,
        ),
        "triggers": _normalise_triggers(triggers),
    }

    summary_text = _normalise_summary(summary)
    if summary_text:
        payload["summary"] = summary_text

    return payload


def merge_preview_payload(
    base: Mapping[str, object] | None,
    *,
    fallback_effects: Mapping[str, float] | None,
    summary: str | None,
    stacks: int,
    previous_stacks: int = 0,
    target: PreviewTarget = "party",
) -> RewardPreviewPayload:
    """Normalise an arbitrary preview mapping, filling gaps from defaults."""

    default = build_preview_from_effects(
        effects=fallback_effects,
        summary=summary,
        triggers=None,
        stacks=stacks,
        previous_stacks=previous_stacks,
        target=target,
    )

    if not isinstance(base, Mapping):
        return default

    payload: RewardPreviewPayload = {
        "stats": default.get("stats", []),
        "triggers": default.get("triggers", []),
    }

    base_summary = _normalise_summary(base.get("summary"))
    payload_summary = base_summary or default.get("summary")
    if payload_summary:
        payload["summary"] = payload_summary

    raw_stats = base.get("stats")
    if isinstance(raw_stats, Sequence):
        stats: list[RewardPreviewStat] = []
        for entry in raw_stats:
            if not isinstance(entry, Mapping):
                continue
            stat_name = str(entry.get("stat", "")).strip()
            mode = entry.get("mode")
            if not stat_name:
                continue
            if mode not in {"percent", "flat", "multiplier"}:
                mode = "percent"
            stat_preview: RewardPreviewStat = {
                "stat": stat_name,
                "mode": mode,  # type: ignore[assignment]
                "target": str(entry.get("target", target)),
            }
            amount = entry.get("amount")
            if isinstance(amount, (int, float)):
                stat_preview["amount"] = float(amount)
            elif isinstance(fallback_effects, Mapping):
                try:
                    fallback_pct = float(fallback_effects.get(stat_name, 0.0))
                except (TypeError, ValueError):
                    fallback_pct = 0.0
                stat_preview["amount"] = fallback_pct * 100
            else:
                stat_preview["amount"] = 0.0
            stacks_value = entry.get("stacks")
            if isinstance(stacks_value, (int, float)):
                stat_preview["stacks"] = int(stacks_value)
            else:
                stat_preview["stacks"] = max(stacks, 1)
            total_amount = entry.get("total_amount")
            if isinstance(total_amount, (int, float)):
                stat_preview["total_amount"] = float(total_amount)
            elif isinstance(fallback_effects, Mapping):
                try:
                    fallback_pct = float(fallback_effects.get(stat_name, 0.0))
                except (TypeError, ValueError):
                    fallback_pct = 0.0
                stat_preview["total_amount"] = ((1 + fallback_pct) ** stat_preview["stacks"] - 1) * 100
            else:
                stat_preview["total_amount"] = 0.0
            previous_total = entry.get("previous_total")
            if isinstance(previous_total, (int, float)) and previous_total != stat_preview["total_amount"]:
                stat_preview["previous_total"] = float(previous_total)
            stats.append(stat_preview)
        payload["stats"] = stats

    raw_triggers = base.get("triggers")
    payload["triggers"] = _normalise_triggers(
        raw_triggers if isinstance(raw_triggers, Iterable) else None
    )

    return payload
