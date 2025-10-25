# Battle Endpoint Payload

`POST /rooms/<run_id>/battle` resolves the next battle node. Fights are fully automated, looping until one side falls, and the backend echoes any provided `action` string. Each round triggers passives and processes damage or healing over time effects before exchanging attacks, pausing for 0.002 s between turns to keep the loop async-friendly.

## Request
- `action` (string, optional)

## Response
- `result` (string): always `"battle"` for this endpoint.
- `run_id` (string): identifier for the active run.
- `action` (string): echoes the request `action` or defaults to an empty string.
- `party` (array): updated stats for each party member.
- `gold` (integer): current shared gold pool.
- `relics` (array): list of acquired relic IDs.
- `cards` (array): list of owned card IDs.
- `card_choices` (array): up to three card options with `id`, `name`, and `stars`.
- `relic_choices` (array): up to three relic options with `id`, `name`, and `stars`.
- `loot` (object): summary of rewards with `gold`, `card_choices`, `relic_choices`, and `items` arrays.
- `reward_staging` (object): active staged rewards split into `cards`, `relics`, and `items`. Each staged entry now exposes a
  `preview` block produced by `autofighter.reward_preview.merge_preview_payload`, which resolves author-provided payloads and
  fills gaps from default `effects` metadata.【F:backend/services/reward_service.py†L42-L126】【F:backend/autofighter/reward_preview.py†L55-L189】
  Frontend consumers should expect the following shape:

  | Field | Type | Notes |
  | --- | --- | --- |
  | `summary` | string | Optional rich-text summary; defaults to the staged `about` copy once trimmed. |
  | `stats` | array | Zero or more stat deltas. Each entry carries `stat`, `mode` (`percent`, `flat`, or `multiplier`),
  `amount` (friendly value already scaled for display), `target` (`party`, `allies`, `foe`, etc.), and stack metadata
  (`stacks`, `total_amount`, `previous_total`). Percentages are represented as whole percents so 0.12 becomes `12.0`. |
  | `triggers` | array | Normalised event hooks with an `event` identifier and optional `description` explaining the
  activation condition. |

  Card and relic plugins can override `build_preview` to emit additional data; any missing fields fall back to the
  canonical calculations in `build_preview_from_effects` so reconnects remain deterministic.【F:backend/plugins/cards/_base.py†L130-L169】【F:backend/plugins/relics/_base.py†L70-L105】
- `reward_activation_log` (array): chronological snapshots of the last 20 reward confirmations. Each entry includes a `bucket`
  value (`cards`, `relics`, or `items`), the `activation_id` issued during confirmation, an ISO8601 `activated_at` timestamp,
  and a copy of the staged payload that was committed. Clients should surface this history when recovering from reconnects so
  duplicate confirmations remain transparent.
- `foes` (array): stats for spawned foes. Each foe entry includes a `rank` string such as `"normal"` or `"boss"` indicating encounter difficulty.

Generic damage types are reserved for the Luna player character; other combatants use elemental types such as Fire, Ice, Lightning, Light, Dark, or Wind.

Example:
```json
{
  "result": "battle",
  "run_id": "abc123",
  "action": "",
  "party": [
    {
      "id": "player",
      "name": "Player",
      "char_type": "C",
      "hp": 990,
      "max_hp": 1000,
      "exp": 1,
      "level": 1,
      "exp_multiplier": 1.0,
      "actions_per_turn": 1,
      "atk": 100,
      "crit_rate": 0.05,
      "crit_damage": 2,
      "effect_hit_rate": 0.01,
      "damage_type": "Fire",
      "defense": 50,
      "mitigation": 100,
      "regain": 1,
      "dodge_odds": 0,
      "effect_resistance": 1.0,
      "vitality": 1.0,
      "action_points": 1,
      "damage_taken": 11,
      "damage_dealt": 1,
      "kills": 1,
      "last_damage_taken": 10,
      "passives": [],
      "dots": [],
      "hots": []
    }
  ],
  "gold": 0,
  "relics": [],
  "cards": [],
  "card_choices": [
    {"id": "balanced_diet", "name": "Balanced Diet", "stars": 1},
    {"id": "mindful_tassel", "name": "Mindful Tassel", "stars": 1},
    {"id": "micro_blade", "name": "Micro Blade", "stars": 1}
  ],
  "relic_choices": [],
  "loot": {
    "gold": 0,
    "card_choices": [
      {"id": "balanced_diet", "name": "Balanced Diet", "stars": 1},
      {"id": "mindful_tassel", "name": "Mindful Tassel", "stars": 1},
      {"id": "micro_blade", "name": "Micro Blade", "stars": 1}
    ],
    "relic_choices": [],
    "items": []
  },
  "reward_staging": {
    "cards": [
      {
        "id": "arc_lightning",
        "name": "Arc Lightning",
        "stars": 3,
        "about": "+255% ATK; every attack chains 50% of dealt damage to a random foe.",
        "preview": {
          "summary": "+255% ATK; every attack chains 50% of dealt damage to a random foe.",
          "stats": [
            {
              "stat": "atk",
              "mode": "percent",
              "amount": 255.0,
              "target": "party",
              "stacks": 1,
              "total_amount": 255.0
            }
          ],
          "triggers": []
        }
      }
    ],
    "relics": [],
    "items": []
  },
  "foes": [
    {
      "id": "slime",
      "name": "Slime",
      "char_type": "C",
      "hp": 0,
      "max_hp": 100,
      "exp": 0,
      "level": 0,
      "exp_multiplier": 0.1,
      "actions_per_turn": 0,
      "atk": 10,
      "crit_rate": 0.005,
      "crit_damage": 0,
      "effect_hit_rate": 0.001,
      "damage_type": "Ice",
      "defense": 5,
      "mitigation": 10,
      "regain": 0,
      "dodge_odds": 0,
      "effect_resistance": 0.1,
      "vitality": 0.1,
      "action_points": 0,
      "damage_taken": 0,
      "damage_dealt": 0,
      "kills": 0,
      "last_damage_taken": 0,
      "passives": [],
      "dots": [],
      "hots": [],
      "gold": 0,
      "rank": "normal"
    }
  ]
}
```

The preview block reports the percentage bonus the party will receive (`amount`) and the cumulative modifier once the staged
reward is confirmed (`total_amount`). When a relic adds an additional stack, a `previous_total` field is included so clients can
display the incremental change alongside the existing bonus.

### Preview authoring examples

> These examples assume the backend preview schema task (`b30ad6a1-reward-preview-schema.md`) and frontend overlay task
> (`f2622706-reward-preview-frontend.md`) have landed; coordinate with the Task Master board so doc updates ship alongside
> those deliverables.

**Flat stat buff (card)**

Cards that only alter base stats can rely on `CardBase.build_preview`, which pipes the card's `effects` dict into
`build_preview_from_effects` and emits a single `percent` stat entry per attribute.【F:backend/plugins/cards/_base.py†L130-L169】
No manual override is required—set `effects = {"atk": 0.25, "crit_rate": 0.1}` and the preview will report +25% ATK and +10%
crit rate for the party. Use `preview_summary` (defaults to the trimmed `about` string) to control the summary line.

**Conditional trigger (card)**

When a reward hinges on an event hook—e.g., "On battle start, gain 2 Balance tokens"—supply a `preview_triggers` iterable on
the plugin. `CardBase.build_preview` merges that iterable with the stat entries so the frontend lists each trigger with a
normalized `event` label and optional `description`. Example:

```python
class EquilibriumPrism(CardBase):
    preview_triggers = (
        {"event": "battle_start", "description": "Gain 2 Balance tokens."},
    )
```

**Passive subscription (relic)**

Relics that subscribe to the event bus or accumulate stacks should override `build_preview` to surface stack-sensitive values.
Call `merge_preview_payload` with a custom payload so you can describe subscriptions and per-stack math while still falling
back to `effects` for core stats.【F:backend/services/reward_service.py†L113-L169】 For example:

```python
class CataclysmEngine(RelicBase):
    def build_preview(self, *, stacks: int, previous_stacks: int = 0):
        payload = super().build_preview(stacks=stacks, previous_stacks=previous_stacks)
        payload["triggers"].append({
            "event": "turn_start",
            "description": f"Queue Cataclysm pulse ({stacks} stacks).",
        })
        return payload
```

Preview totals automatically reflect the requested stack count, so passing `stacks=party.relics.count(self.id) + 1` from
`RewardService.select_relic` keeps overlays accurate for duplicate copies.【F:backend/services/reward_service.py†L113-L160】

### Duplicate-confirmation telemetry

Every `/rewards/<bucket>/<run_id>/confirm` request now emits a `confirm_<bucket>_blocked` telemetry record through
`log_game_action` when staging is empty (for example, a duplicate submission or manual retry after the reward already locked in).
The payload captures the run, current room identifier, the attempted `bucket`, and a snapshot of the `awaiting_*` flags. Live
ops can monitor this signal for suspicious automation or reconnect storms; the associated API response remains a `400` with
`"no staged reward to confirm"` so clients can retry safely.

## Testing
- `uv run pytest tests/test_card_rewards.py::test_battle_offers_choices_and_applies_effect`
