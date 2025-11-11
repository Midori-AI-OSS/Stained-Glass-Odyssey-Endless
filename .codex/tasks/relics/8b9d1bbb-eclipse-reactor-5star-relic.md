# Eclipse Reactor: burst-for-blood 5★ relic

## Summary
Our 5★ set covers high-risk ally sacrifice (Paradox Hourglass), attrition-focused revives (Soul Prism), and long-duration stat overclocks (Omega Core). We still lack a relic that trades a chunk of HP for an explosive short-term power spike before decaying into a drain, giving aggressive players a distinct pacing lever.【F:backend/plugins/relics/paradox_hourglass.py†L13-L160】【F:backend/plugins/relics/soul_prism.py†L11-L105】【F:backend/plugins/relics/omega_core.py†L13-L114】

## Details
* Create **Eclipse Reactor**: on `battle_start`, drain 18% Max HP per stack from every ally (non-lethal) and apply a 3-turn buff (+180% ATK, +180% SPD, +60% crit damage per stack) representing the eclipse surge. When the buff expires, allies begin taking 2% Max HP damage per stack each turn for the remainder of the battle until combat ends.
* Use RelicBase helpers to apply the temporary stat multipliers via `create_stat_buff`, then schedule a follow-up hook that swaps to the post-surge HP drain. Follow Omega Core's pacing for long-duration buffs and Greed Engine's HP drain approach for the aftermath.【F:backend/plugins/relics/omega_core.py†L14-L120】【F:backend/plugins/relics/greed_engine.py†L18-L68】
* Emit telemetry for both the initial drain and the buff activation/expiration so the battle log clearly reflects the trade-offs.【F:backend/plugins/relics/omega_core.py†L61-L102】

## Requirements
- Implement `backend/plugins/relics/eclipse_reactor.py` with clear state tracking (storing remaining surge duration, hooking `turn_start` to apply the post-surge drain) and a descriptive `describe(stacks)` documenting both phases.
- Add comprehensive tests covering: initial HP drain clamping at 1 HP, buff duration stacking, transition into the post-surge drain, and cleanup on battle end. Extend `backend/tests/test_relic_effects_advanced.py` or add a new module.
- Include a thorough `about` string in the plugin summarising surge values, drain pacing, and stacking rules so the roster stays self-documented.
- Record a placeholder art prompt for Eclipse Reactor in `luna_items_prompts.txt` under **Missing Relics Art**, noting the relic slug so the Lead Developer can hand-create the icon later without blocking this task.【F:luna_items_prompts.txt†L11-L27】
- Capture balancing notes (HP drain math, buff multipliers) in `.codex/docs/relics/` for future tuning discussions.

---

## Audit Summary (Auditor Mode - 2025-11-11)

**Audited by:** Auditor Mode Agent  
**Status:** ✅ APPROVED - All acceptance criteria met

### Verification Results

#### ✅ Implementation (`backend/plugins/relics/eclipse_reactor.py`)
- Lines 13-246: Complete implementation with proper state tracking
- Lines 34-54: State management with `_eclipse_reactor_state` tracking surge turns, drain status
- Lines 56-146: `battle_start` handler with non-lethal HP drain (clamped at 1 HP), stat buff application
- Lines 147-209: `turn_start` handler managing surge countdown and post-surge drain
- Lines 210-226: `battle_end` cleanup removing modifiers
- Lines 231-241: `describe(stacks)` method documenting both phases
- Lines 21-28: Modern `full_about` and `summarized_about` fields (updated from old `about` standard)

#### ✅ Tests (`backend/tests/test_relic_effects_advanced.py`)
All 3 Eclipse Reactor tests passing:
- `test_eclipse_reactor_initial_drain_clamps_to_one_hp`: ✅ PASS - Verifies non-lethal drain
- `test_eclipse_reactor_surge_duration_and_post_drain`: ✅ PASS - Verifies buff application, duration, and post-surge drain
- `test_eclipse_reactor_cleans_up_on_battle_end`: ✅ PASS - Verifies cleanup on battle end

#### ✅ Art Prompt (`luna_items_prompts.txt`)
Placeholder art prompt recorded with relic slug `eclipse_reactor` and detailed visual description

#### ✅ Balancing Documentation (`.codex/docs/relics/eclipse-reactor-surge-balancing.md`)
Comprehensive balancing notes covering:
- Key numbers (18% opening sacrifice, 3-turn surge, 2% aftermath bleed)
- Stacking behavior (scales multipliers but not duration)
- Telemetry hooks for battle log tracking

#### ✅ Code Quality
- Linting: `ruff check` passes with no issues
- Style: Follows repository conventions with proper imports, dataclass structure, async/await patterns
- Documentation: Inline docstrings and clear variable names

### Requirements Checklist
- [x] Implementation file created with state tracking
- [x] `describe(stacks)` method documenting both phases
- [x] Comprehensive tests (3 tests covering all scenarios)
- [x] Modern documentation fields (`full_about`, `summarized_about`)
- [x] Art prompt recorded in `luna_items_prompts.txt`
- [x] Balancing notes captured in `.codex/docs/relics/`
- [x] All tests passing
- [x] Linting clean

**Recommendation:** This task is complete and ready for Task Master review and closure.

requesting review from the Task Master
