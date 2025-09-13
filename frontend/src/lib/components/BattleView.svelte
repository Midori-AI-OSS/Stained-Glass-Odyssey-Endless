<script>
  import { onMount, onDestroy, createEventDispatcher, tick } from 'svelte';
  import { scale } from 'svelte/transition';
  import { roomAction } from '$lib';
  import { getRandomBackground, getElementColor } from '../systems/assetLoader.js';
  import FighterUIItem from '../battle/FighterUIItem.svelte';
  import EnrageIndicator from '../battle/EnrageIndicator.svelte';
  import BattleLog from '../battle/BattleLog.svelte';
  import BattleEffects from '../effects/BattleEffects.svelte';
  import StatusIcons from '../battle/StatusIcons.svelte';
  import ActionQueue from '../battle/ActionQueue.svelte';

  export let runId = '';
  export let framerate = 60;
  export let party = [];
  export let enrage = { active: false, stacks: 0, turns: 0 };
  export let reducedMotion = false;
  export let active = true;
  export let showHud = true;
  export let showFoes = true;
  export let showActionValues = false;

  let foes = [];
  let queue = [];
  let serverShowActionValues = false;
  let combatants = [];
  $: combatants = [
    ...(party || []),
    ...((party || []).flatMap(p => p?.summons || [])),
    ...(foes || []),
    ...((foes || []).flatMap(f => f?.summons || [])),
  ];
  $: foeCount = (foes || []).length;
  $: displayActionValues = Boolean(showActionValues || serverShowActionValues);
  function getFoeSizePx(count) {
    const c = Math.max(1, Number(count || 0));
    if (c <= 1) return 384;
    if (c === 2) return 320;
    if (c === 3) return 288;
    if (c === 4) return 272;
    if (c === 5) return 256; // match player size
    if (c === 6) return 224;
    if (c === 7) return 208;
    return 192; // 8 or more
  }
  let timer;
  let logs = [];
  
  const logAnimations = {
    damage: 'HitEffect',
    burn: 'Fire1',
    poison: 'Poison',
    heal: 'HealOne1'
  };

  let effectCue = '';
  function queueEffect(name) {
    if (!name || reducedMotion) return;
    effectCue = name;
    tick().then(() => {
      effectCue = '';
    });
  }

  let knownSummons = new Set();
  const dispatch = createEventDispatcher();
  let pollDelay = 1000 / framerate;
  $: pollDelay = 1000 / framerate;
  let bg = getRandomBackground();

  function logToEvent(line) {
    if (typeof line !== 'string') return null;
    const l = line.toLowerCase();
    if (l.includes('burn')) return 'burn';
    if (l.includes('poison')) return 'poison';
    if (l.includes('heal')) return 'heal';
    if (l.includes('damage')) return 'damage';
    return null;
  }

  // Combine passives, dots, and hots into a single list (cap will be applied in template)
  function combineStatuses(unit) {
    if (!unit) return [];
    const out = [];
    for (const p of unit.passives || []) {
      out.push({ kind: 'passive', label: p.id, count: Number(p.stacks || 1), title: p.id });
    }
    for (const d of unit.dots || []) {
      const title = `${d.id} - ${d.damage} dmg for ${d.turns} turns`;
      out.push({ kind: 'dot', label: d.id, count: Number(d.turns || 1), title });
    }
    for (const h of unit.hots || []) {
      const title = `${h.id} - ${h.healing} heal for ${h.turns} turns`;
      out.push({ kind: 'hot', label: h.id, count: Number(h.turns || 1), title });
    }
    return out;
  }

  $: if (logs.length) {
    const evt = logToEvent(logs[logs.length - 1]);
    if (evt && logAnimations[evt]) {
      queueEffect(logAnimations[evt]);
    }
  }

  function differs(a, b) {
    return JSON.stringify(a) !== JSON.stringify(b);
  }

  function guessElementFromId(id) {
    if (!id) return 'Generic';
    const s = String(id).toLowerCase();
    if (s.includes('fire') || s.includes('flame') || s.includes('burn')) return 'Fire';
    if (s.includes('water') || s.includes('aqua') || s.includes('ice') || s.includes('frost')) return 'Water';
    if (s.includes('earth') || s.includes('stone') || s.includes('rock') || s.includes('ground')) return 'Earth';
    if (s.includes('air') || s.includes('wind') || s.includes('storm') || s.includes('lightning')) return 'Air';
    if (s.includes('light') || s.includes('holy') || s.includes('divine')) return 'Light';
    if (s.includes('dark') || s.includes('shadow') || s.includes('void')) return 'Dark';
    return 'Generic';
  }

  function detectSummons(partySummons, foeSummons) {
    const all = new Set(knownSummons);
    for (const [, summons] of partySummons) {
      for (const s of summons) {
        if (!all.has(s.id)) {
          queueEffect('SummonEffect');
          all.add(s.id);
          break;
        }
      }
    }
    for (const [, summons] of foeSummons) {
      for (const s of summons) {
        if (!all.has(s.id)) {
          queueEffect('SummonEffect');
          all.add(s.id);
          break;
        }
      }
    }
    knownSummons = all;
  }

  async function fetchSnapshot() {
    if (!active || !runId) return;
    const start = performance.now();
    dispatch('snapshot-start');
    try {
      const snap = await roomAction(runId, 'battle', 'snapshot');
      // Normalize alternate shapes for compatibility
      if (snap && !Array.isArray(snap.party) && snap.party && typeof snap.party === 'object') {
        snap.party = Object.values(snap.party);
      }
      if (snap && !Array.isArray(snap.foes)) {
        if (snap.foes && typeof snap.foes === 'object') {
          snap.foes = Object.values(snap.foes);
        } else if (Array.isArray(snap.enemies)) {
          snap.foes = snap.enemies;
        } else if (snap.enemies && typeof snap.enemies === 'object') {
          snap.foes = Object.values(snap.enemies);
        }
      }

      // Map summons to their owners
      const partySummons = new Map();
      if (snap && snap.party_summons) {
        const arr = Array.isArray(snap.party_summons)
          ? snap.party_summons
          : Object.entries(snap.party_summons).flatMap(([owner, list]) =>
              (Array.isArray(list) ? list : [list]).map(s => ({ owner_id: owner, ...s })),
            );
        for (const s of arr) {
          const owner = s?.owner_id;
          if (!owner) continue;
          if (!partySummons.has(owner)) partySummons.set(owner, []);
          partySummons.get(owner).push(s);
        }
      }

      const foeSummons = new Map();
      if (snap && snap.foe_summons) {
        const arr = Array.isArray(snap.foe_summons)
          ? snap.foe_summons
          : Object.entries(snap.foe_summons).flatMap(([owner, list]) =>
              (Array.isArray(list) ? list : [list]).map(s => ({ owner_id: owner, ...s })),
            );
        for (const s of arr) {
          const owner = s?.owner_id;
          if (!owner) continue;
          if (!foeSummons.has(owner)) foeSummons.set(owner, []);
          foeSummons.get(owner).push(s);
        }
      }

      detectSummons(partySummons, foeSummons);

      if (snap.enrage && differs(snap.enrage, enrage)) enrage = snap.enrage;
      
      if (snap.party) {
        const prevById = new Map((party || []).map(p => [p.id, p]));
        const enriched = (snap.party || []).map(m => {
          let elem =
            (Array.isArray(m.damage_types) && m.damage_types[0]) ||
            m.damage_type ||
            m.element ||
            '';
          if (!elem || /generic/i.test(String(elem))) {
            const prev = prevById.get(m.id);
            if (prev && (prev.element || prev.damage_type)) {
              elem = prev.element || prev.damage_type;
            } else {
              elem = guessElementFromId(m.id);
            }
          }
          const resolved = typeof elem === 'string' ? elem : (elem?.id || elem?.name || 'Generic');
          return { ...m, element: resolved, summons: partySummons.get(m.id) || [] };
        });
        if (differs(enriched, party)) party = enriched;
      }

      if (snap.foes) {
        const prevById = new Map((foes || []).map(f => [f.id, f]));
        const enrichedFoes = (snap.foes || []).map(f => {
          let elem =
            (Array.isArray(f.damage_types) && f.damage_types[0]) ||
            f.damage_type ||
            f.element;
          let resolved = typeof elem === 'string' ? elem : (elem?.id || elem?.name);
          if (!resolved) {
            const prev = prevById.get(f.id);
            resolved = prev?.element || prev?.damage_type || '';
          }
          return { ...f, element: resolved, summons: foeSummons.get(f.id) || [] };
        });
        if (differs(enrichedFoes, foes)) foes = enrichedFoes;
      }

      if (Array.isArray(snap.queue || snap.action_queue)) {
        queue = snap.queue || snap.action_queue;
      }
      if ("show_action_values" in snap) {
        serverShowActionValues = Boolean(snap.show_action_values);
      }

      if (Array.isArray(snap.log)) logs = snap.log;
      else if (Array.isArray(snap.logs)) logs = snap.logs;
    } catch (e) {
      // Silently ignore errors to avoid spam during rapid polling
    } finally {
      dispatch('snapshot-end');
      const elapsed = performance.now() - start;
      const remaining = Math.max(0, pollDelay - elapsed);
      if (active && runId) {
        timer = setTimeout(fetchSnapshot, remaining);
      }
    }
  }

  onMount(() => {
    if (active && runId) {
      fetchSnapshot();
    }
  });

  onDestroy(() => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  });

  // Watch active state changes
  $: if (active && runId && !timer) {
    fetchSnapshot();
  } else if (!active && timer) {
    clearTimeout(timer);
    timer = null;
  }
</script>

<div
  class="modern-battle-field"
  style={`background-image: url(${bg})`}
  data-testid="modern-battle-view"
>
  <EnrageIndicator active={Boolean(enrage?.active)} {reducedMotion} enrageData={enrage} />
  <BattleEffects cue={effectCue} />
  <ActionQueue
    {queue}
    {combatants}
    {reducedMotion}
    showActionValues={displayActionValues}
  />

  <!-- Foes at the top -->
  {#if showFoes}
    <div class="foe-row">
      {#each foes as foe (foe.id)}
        <div class="foe-container">
          <!-- Buffs at the very top -->
          <div class="foe-buffs">
            {#if foe.passives?.length || foe.dots?.length || foe.hots?.length}
              <!-- Buff bar shows HoTs, DoTs, and Passives -->
              <StatusIcons layout="bar" hots={(foe.hots || []).slice(0, 6)} dots={(foe.dots || []).slice(0, 6)} active_effects={(foe.passives || []).slice(0, 6)} />
            {/if}
          </div>
          
          <!-- HP bar on top -->
          <div class="foe-hp-bar" style={`width: ${getFoeSizePx(foeCount)}px`}>
            <div class="hp-bar-container" class:reduced={reducedMotion}>
              {#if Number(foe?.shields || 0) > 0 && Number(foe?.max_hp || 0) > 0}
                <div
                  class="overheal-fill"
                  style={`width: calc(${Math.max(0, Math.min(100, (Number(foe.shields || 0) / Math.max(1, Number(foe.max_hp || 0))) * 100))}% + 5px); left: -5px;`}
                ></div>
              {/if}
              <div 
                class="hp-bar-fill"
                style="width: {Math.max(0, Math.min(100, (foe.hp / foe.max_hp) * 100))}%; 
                       background: {(foe.hp / foe.max_hp) <= 0.3 ? 'linear-gradient(90deg, #ff4444, #ff6666)' : 'linear-gradient(90deg, #44ffff, #66dddd)'}"
              ></div>
              {#if foe.hp < foe.max_hp}
                <div class="hp-text" data-position="outline">{foe.hp}</div>
              {/if}
            </div>
          </div>
          
          <!-- Character photo/portrait -->
          <FighterUIItem fighter={foe} position="top" {reducedMotion} sizePx={getFoeSizePx(foeCount)} />
          
          <!-- Summons -->
          {#if foe.summons?.length}
            <div class="summon-list">
              {#each foe.summons as summon (summon.id)}
                <div
                  in:scale={{ duration: reducedMotion ? 0 : 200 }}
                  class="summon-entry"
                >
                  <!-- Summon HP bar -->
                  <div class="summon-hp-bar">
                    <div class="hp-bar-container" class:reduced={reducedMotion}>
                      {#if Number(summon?.shields || 0) > 0 && Number(summon?.max_hp || 0) > 0}
                        <div
                          class="overheal-fill"
                          style={`width: calc(${Math.max(0, Math.min(100, (Number(summon.shields || 0) / Math.max(1, Number(summon.max_hp || 0))) * 100))}% + 5px); left: -5px;`}
                        ></div>
                      {/if}
                      <div 
                        class="hp-bar-fill"
                        style="width: {Math.max(0, Math.min(100, (summon.hp / summon.max_hp) * 100))}%; 
                               background: {(summon.hp / summon.max_hp) <= 0.3 ? 'linear-gradient(90deg, #ff4444, #ff6666)' : 'linear-gradient(90deg, #44ffff, #66dddd)'}"
                      ></div>
                      {#if summon.hp < summon.max_hp}
                        <div class="hp-text" data-position="outline">{summon.hp}</div>
                      {/if}
                    </div>
                  </div>
                  
                  <FighterUIItem fighter={summon} position="top" {reducedMotion} size="medium" />
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}

  <!-- Party at the bottom -->
  <div class="party-row">
    {#each party as member (member.id)}
      <div class="party-container">
        <!-- Summons (show above player portrait for party) -->
        {#if member.summons?.length}
          <div class="summon-list">
            {#each member.summons as summon (summon.id)}
              <div
                in:scale={{ duration: reducedMotion ? 0 : 200 }}
                class="summon-entry"
              >
                <!-- Summon portrait -->
                <FighterUIItem fighter={summon} position="bottom" {reducedMotion} size="medium" />

                <!-- Summon HP bar under portrait -->
                <div class="summon-hp-bar">
                  <div class="hp-bar-container" class:reduced={reducedMotion}>
                    {#if Number(summon?.shields || 0) > 0 && Number(summon?.max_hp || 0) > 0}
                      <div
                        class="overheal-fill"
                        style={`width: calc(${Math.max(0, Math.min(100, (Number(summon.shields || 0) / Math.max(1, Number(summon.max_hp || 0))) * 100))}% + 5px); left: -5px;`}
                      ></div>
                    {/if}
                    <div 
                      class="hp-bar-fill"
                      style="width: {Math.max(0, Math.min(100, (summon.hp / summon.max_hp) * 100))}%; 
                             background: {(summon.hp / summon.max_hp) <= 0.3 ? 'linear-gradient(90deg, #ff4444, #ff6666)' : 'linear-gradient(90deg, #44ffff, #66dddd)'}"
                    ></div>
                    {#if summon.hp < summon.max_hp}
                      <div class="hp-text" data-position="outline">{summon.hp}</div>
                    {/if}
                  </div>
                </div>

                <!-- Summon buffs under HP bar -->
                <div class="summon-buffs">
                  {#if summon.passives?.length || summon.dots?.length || summon.hots?.length}
                    <StatusIcons layout="bar" hots={(summon.hots || []).slice(0, 6)} dots={(summon.dots || []).slice(0, 6)} active_effects={(summon.passives || []).slice(0, 6)} />
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}

        <div class="party-main">
          <!-- Character photo as base (ult & pips overlay handled inside) -->
          <FighterUIItem fighter={member} position="bottom" {reducedMotion} />
        </div>
        
        <!-- HP bar under the photo -->
        <div class="party-hp-bar">
          <div class="hp-bar-container" class:reduced={reducedMotion}>
            {#if Number(member?.shields || 0) > 0 && Number(member?.max_hp || 0) > 0}
              <div
                class="overheal-fill"
                style={`width: calc(${Math.max(0, Math.min(100, (Number(member.shields || 0) / Math.max(1, Number(member.max_hp || 0))) * 100))}% + 5px); left: -5px;`}
              ></div>
            {/if}
            <div 
              class="hp-bar-fill"
              style="width: {Math.max(0, Math.min(100, (member.hp / member.max_hp) * 100))}%; 
                     background: {(member.hp / member.max_hp) <= 0.3 ? 'linear-gradient(90deg, #ff4444, #ff6666)' : 'linear-gradient(90deg, #44ffff, #66dddd)'}"
            ></div>
            {#if member.hp < member.max_hp}
              <div class="hp-text" data-position="outline">{member.hp}</div>
            {/if}
          </div>
        </div>
        
        <!-- Buffs under HP bar -->
        <div class="party-buffs">
          {#if member.passives?.length || member.dots?.length || member.hots?.length}
            <!-- Buff bar shows HoTs, DoTs, and Passives -->
            <StatusIcons layout="bar" hots={(member.hots || []).slice(0, 6)} dots={(member.dots || []).slice(0, 6)} active_effects={(member.passives || []).slice(0, 6)} />
          {/if}
        </div>

      </div>
    {/each}
  </div>

  {#if showHud}
    <BattleLog entries={logs} />
  {/if}
</div>

<style>
  .modern-battle-field {
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 1rem;
    overflow: hidden;
    gap: 1rem;
  }

  .modern-battle-field > *:not(.action-queue) {
    position: relative;
    z-index: 1;
  }

  /* Foe row at top */
  .foe-row {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
    align-items: flex-start;
    margin-top: 10vh;
  }

  .foe-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }

  .foe-buffs {
    min-height: 24px;
    display: flex;
    justify-content: center;
  }

  .foe-hp-bar {
    width: 96px; /* match enlarged foe portrait width */
    margin-bottom: 0.25rem;
  }

  /* Party row at bottom */
  .party-row {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
    align-items: flex-end;
  }

  .party-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }

  .party-main {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  /* Ult gauge moved into portrait overlay; remove layout container rules */

  .ult-ready-glow {
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    background: radial-gradient(circle, var(--element-color, #4CAF50) 0%, transparent 70%);
    opacity: 0.3;
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.3; }
    50% { transform: scale(1.1); opacity: 0.6; }
  }

  /* HP bars */
  .hp-bar-container {
    position: relative;
    width: 100%;
    height: 10px;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.3);
    overflow: visible; /* allow HP text to sit on the outline */
  }

  .hp-bar-fill {
    height: 100%;
    transition: width 0.3s ease, background 0.3s ease;
    position: relative; /* ensure z-index applies */
    z-index: 1; /* draw above overheal/shields */
  }

  /* Overheal/shields visual overlay (similar to legacy FighterPortrait) */
  .overheal-fill {
    position: absolute;
    left: 0;
    top: -1px; /* slight upward offset */
    height: calc(100% + 2px);
    background: rgba(255, 255, 255, 0.92);
    transition: width 0.3s linear;
    pointer-events: none;
    z-index: 0; /* below main HP fill */
  }

  .hp-bar-container.reduced .hp-bar-fill {
    transition: none;
  }

  .hp-bar-container.reduced .overheal-fill {
    transition: none;
  }

  .hp-text {
    position: absolute;
    right: 4px;
    top: -1.2em; /* sit on the bar outline, not inside the fill */
    transform: none;
    font-size: 1rem; /* larger for readability */
    font-weight: bold;
    color: #fff;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.9);
    padding: 0 6px;
    line-height: 1.1;
    border-radius: 6px; /* shape for backdrop */
    pointer-events: none;
    z-index: 2;
  }

  /* Soft faded-edge backdrop behind the HP number */
  .hp-text::before {
    content: '';
    position: absolute;
    inset: -12px; /* extend beyond text for softer falloff */
    border-radius: 16px;
    background: radial-gradient(
      ellipse at center,
      rgba(0, 0, 0, 0.55) 0%,
      rgba(0, 0, 0, 0.50) 40%,
      rgba(0, 0, 0, 0.30) 70%,
      rgba(0, 0, 0, 0.00) 100%
    );
    filter: blur(4px);
    box-shadow: 0 0 16px rgba(0,0,0,0.3);
    z-index: -1;
    pointer-events: none;
  }

  .party-hp-bar {
    width: 256px; /* match enlarged party portrait width */
  }

  /* Status effects */
  .status-bar {
    display: flex;
    gap: 0.2rem;
    flex-wrap: wrap;
    justify-content: center;
    max-width: 120px;
  }

  .status-icon {
    position: relative;
    min-width: 16px;
    height: 16px;
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.6rem;
    font-weight: bold;
    color: #fff;
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.8);
    cursor: help;
  }

  .status-icon.passive {
    background: linear-gradient(135deg, #3498DB, #2980B9);
  }

  .status-icon.dot {
    background: linear-gradient(135deg, #E74C3C, #C0392B);
  }

  .status-icon.hot {
    background: linear-gradient(135deg, #2ECC71, #27AE60);
  }

  .status-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 14px;
  }

  .status-count {
    position: absolute;
    top: -4px;
    right: -4px;
    background: rgba(0, 0, 0, 0.8);
    color: #fff;
    font-size: 0.5rem;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
  }

  /* Summons */
  .summon-list {
    display: flex;
    gap: 0.25rem;
    margin-top: 0.25rem;
  }

  /* Summons appear above party portrait: remove top margin for clean spacing */
  .party-container > .summon-list {
    margin-top: 0;
  }

  .summon-entry {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.125rem;
  }

  .summon-hp-bar {
    width: 96px; /* match medium portrait width */
    margin-bottom: 0.125rem;
  }

  .summon-buffs {
    min-height: 20px;
    display: flex;
    justify-content: center;
  }

  /* Responsive design */
  @media (max-width: 768px) {
    .modern-battle-field {
      padding: 0.5rem;
      gap: 0.5rem;
    }

    .foe-row, .party-row {
      gap: 0.5rem;
    }

    .ult-gauge {
      width: 30px;
      height: 30px;
    }

    .status-bar {
      max-width: 100px;
    }

    .status-icon {
      min-width: 14px;
      height: 14px;
      font-size: 0.55rem;
    }
  }

  @media (max-width: 600px) {
    .party-row, .foe-row {
      flex-direction: column;
      align-items: center;
    }

    .party-main {
      gap: 0.25rem;
    }

    .summon-list {
      gap: 0.2rem;
    }
  }
</style>
