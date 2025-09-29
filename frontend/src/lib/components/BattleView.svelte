<script>
  import { onMount, onDestroy, createEventDispatcher, tick } from 'svelte';
  import { get } from 'svelte/store';
  import { scale, fade } from 'svelte/transition';
  import { roomAction } from '$lib';
  import {
    getRandomBackground,
    getElementColor,
    getLightstreamSwordVisual,
    normalizeDamageTypeId
  } from '../systems/assetLoader.js';
  import BattleFighterCard from '../battle/BattleFighterCard.svelte';
  import EnrageIndicator from '../battle/EnrageIndicator.svelte';
  import BattleLog from '../battle/BattleLog.svelte';
  import BattleEffects from '../effects/BattleEffects.svelte';
  import StatusIcons from '../battle/StatusIcons.svelte';
  import ActionQueue from '../battle/ActionQueue.svelte';
  import BattleEventFloaters from './BattleEventFloaters.svelte';
  import BattleTargetingOverlay from './BattleTargetingOverlay.svelte';
  import { motionStore } from '../systems/settingsStorage.js';
  import { haltSync } from '../systems/overlayState.js';

  export let runId = '';
  export let framerate = 60;
  export let party = [];
  export let enrage = { active: false, stacks: 0, turns: 0 };
  export let reducedMotion = false; // Legacy prop for backward compatibility
  export let active = true;
  export let showHud = false;
  export let showFoes = true;
  export let showActionValues = false;
  // Hide status chips (DoTs/HoTs timeline) by default
  export let showStatusTimeline = false;
  export let showTurnCounter = true;
  export let flashEnrageCounter = true;

  // Use granular motion settings with fallback to legacy prop
  $: motionSettings = $motionStore || { 
    globalReducedMotion: false, 
    disablePortraitGlows: false, 
    simplifyOverlayTransitions: false 
  };
  $: effectiveReducedMotion = reducedMotion || motionSettings.globalReducedMotion;

  let foes = [];
  let queue = [];
  let serverShowActionValues = false;
  let combatants = [];
  let activeId = null;
  let activeTargetId = null;
  let snapshotActiveId = null;
  let snapshotActiveTargetId = null;
  let turnPhaseSeen = false;
  let rawTurnPhase = null;
  let turnPhaseState = '';
  let turnPhaseAttackerId = null;
  let turnPhaseTargetId = null;
  let storedTurnPhase = null;
  let normalizedTurnPhaseState = '';
  let turnPhaseIsActive = false;
  let phaseAllowsOverlays = true;
  let currentTurn = null;
  let statusPhase = null;
  let statusTimeline = [];
  let recentEvents = [];
  let statusChipLifetime = 1800;
  const statusEntryMap = new Map();
  const statusRemovalTimers = new Map();
  let combatantById = new Map();
  $: combatants = [
    ...(party || []),
    ...((party || []).flatMap(p => p?.summons || [])),
    ...(foes || []),
    ...((foes || []).flatMap(f => f?.summons || [])),
  ];
  $: combatantById = new Map(
    (combatants || [])
      .filter(entry => entry)
      .flatMap(entry => {
        const results = [];
        const baseId = entry?.id;
        if (baseId !== undefined && baseId !== null) {
          results.push([String(baseId), entry]);
        }
        const instanceKey = entry?.instance_id;
        if (
          instanceKey !== undefined &&
          instanceKey !== null &&
          instanceKey !== baseId
        ) {
          results.push([String(instanceKey), entry]);
        }
        return results;
      })
  );
  // If a combatant disappears, clear stale targeting ids
  $: if (activeId && !combatantById.has(String(activeId))) activeId = null;
  $: if (activeTargetId && !combatantById.has(String(activeTargetId))) activeTargetId = null;
  $: if (snapshotActiveId && !combatantById.has(String(snapshotActiveId))) {
    snapshotActiveId = null;
  }
  $: if (snapshotActiveTargetId && !combatantById.has(String(snapshotActiveTargetId))) {
    snapshotActiveTargetId = null;
  }
  $: if (turnPhaseSeen && turnPhaseAttackerId && !combatantById.has(String(turnPhaseAttackerId))) {
    turnPhaseAttackerId = null;
  }
  $: if (turnPhaseSeen && turnPhaseTargetId && !combatantById.has(String(turnPhaseTargetId))) {
    turnPhaseTargetId = null;
  }

  $: normalizedTurnPhaseState = normalizePhaseState(turnPhaseState);
  $: turnPhaseIsActive = turnPhaseSeen && (normalizedTurnPhaseState === 'start' || normalizedTurnPhaseState === 'resolve');
  $: storedTurnPhase = turnPhaseSeen
    ? {
      ...(rawTurnPhase || {}),
      state: normalizedTurnPhaseState,
      attacker_id: turnPhaseAttackerId ?? null,
      target_id: turnPhaseTargetId ?? null,
    }
    : null;
  $: phaseAllowsOverlays = turnPhaseSeen ? turnPhaseIsActive : true;
  $: {
    const nextActive = turnPhaseIsActive
      ? (turnPhaseAttackerId ?? snapshotActiveId ?? null)
      : turnPhaseSeen
        ? null
        : snapshotActiveId ?? null;
    if (activeId !== nextActive) activeId = nextActive;

    const nextTarget = turnPhaseIsActive
      ? (turnPhaseTargetId ?? snapshotActiveTargetId ?? null)
      : turnPhaseSeen
        ? null
        : snapshotActiveTargetId ?? null;
    if (activeTargetId !== nextTarget) activeTargetId = nextTarget;
  }
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
  function clearPollTimer() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }
  function isSyncHalted() {
    return get(haltSync);
  }
  let logs = [];
  let hoveredId = null;
  let floaterFeed = [];
  // Anchor positions for floating damage/heal numbers: id -> { x, y } in [0..1] relative to root field
  let anchors = {};
  // Track live DOM nodes for anchors to allow global recompute when layout shifts (e.g., removals)
  let anchorNodes = new Map(); // id -> node
  let rootEl;
  let recentEventCounts = new Map();
  let lastRecentEventTokens = [];
  let floaterDuration = 1200;
  const relevantRecentEventTypes = new Set([
    'damage_taken',
    'heal_received',
    'dot_tick',
    'hot_tick',
    'card_effect',
    'relic_effect',
  ]);
  let lastRunId = runId;

  // Slow down floater animation a bit for readability
  $: floaterDuration = Math.max(1400, pollDelay * 5);
  $: if (runId !== lastRunId) {
    recentEventCounts = new Map();
    lastRecentEventTokens = [];
    floaterFeed = [];
    recentEvents = [];
    activeId = null;
    activeTargetId = null;
    snapshotActiveId = null;
    snapshotActiveTargetId = null;
    resetTurnPhaseState();
    statusPhase = null;
    clearStatusTimeline();
    queuedHpDrains = [];
    waitingForResolve = false;
    lastPhaseToken = '';
    lastEffectSignature = '';
    phaseSequenceCounter = 0;
    pendingLayers = new Map();
    hpHistory = new Map();
    lastRunId = runId;
    currentTurn = null;
  }
  $: if (!active) {
    floaterFeed = [];
    recentEventCounts = new Map();
    lastRecentEventTokens = [];
    recentEvents = [];
    activeId = null;
    activeTargetId = null;
    snapshotActiveId = null;
    snapshotActiveTargetId = null;
    resetTurnPhaseState();
    statusPhase = null;
    clearStatusTimeline();
    queuedHpDrains = [];
    waitingForResolve = false;
    lastPhaseToken = '';
    lastEffectSignature = '';
    phaseSequenceCounter = 0;
    pendingLayers = new Map();
    hpHistory = new Map();
    currentTurn = null;
  }

  // Compute and update anchor for a given id/node
  function computeAnchorFor(id, node) {
    if (!id || !node || !rootEl) return;
    try {
      const root = rootEl.getBoundingClientRect();
      const rect = node.getBoundingClientRect();
      if (!root.width || !root.height) return;
      const cx = rect.left + rect.width / 2 - root.left;
      const cy = rect.top + rect.height * 0.5 - root.top;
      const x = Math.max(0, Math.min(1, cx / root.width));
      const y = Math.max(0, Math.min(1, cy / root.height));
      const prev = anchors[id];
      const dx = prev ? Math.abs(prev.x - x) : Infinity;
      const dy = prev ? Math.abs(prev.y - y) : Infinity;
      if (dx > 0.002 || dy > 0.002 || !prev) {
        anchors = { ...anchors, [id]: { x, y } };
      }
    } catch {}
  }

  function recomputeAllAnchors() {
    for (const [id, node] of anchorNodes.entries()) {
      computeAnchorFor(id, node);
    }
  }

  // Svelte action: register a DOM node as an anchor for a given id
  function registerAnchor(node, params) {
    const extractId = (p) => {
      if (p && typeof p === 'object' && 'id' in p) return String(p.id);
      if (p === 0 || p) return String(p);
      return '';
    };
    let id = extractId(params);
    if (!id || !node) return { update: () => {}, destroy: () => {} };
    const compute = () => computeAnchorFor(id, node);
    // Track this node for global recomputes
    if (id) anchorNodes.set(id, node);
    compute();
    const ro = new ResizeObserver(() => compute());
    ro.observe(node);
    const onWinResize = () => compute();
    window.addEventListener('resize', onWinResize);
    return {
      update(next) {
        const nextId = extractId(next);
        if (nextId !== id) {
          if (id && anchors[id]) {
            const copy = { ...anchors };
            delete copy[id];
            anchors = copy;
          }
          if (id) {
            anchorNodes.delete(id);
          }
          id = nextId;
          if (id) {
            anchorNodes.set(id, node);
          }
        }
        compute();
      },
      destroy() {
        try { ro.disconnect(); } catch {}
        window.removeEventListener('resize', onWinResize);
        if (id && anchors[id]) {
          const copy = { ...anchors };
          delete copy[id];
          anchors = copy;
        }
        if (id) {
          anchorNodes.delete(id);
        }
      }
    };
  }
  
  let effectCue = '';
  function queueEffect(name) {
    if (!name || effectiveReducedMotion) return;
    effectCue = name;
    tick().then(() => {
      effectCue = '';
    });
  }

  const ELEMENTAL_EFFECT_TABLE = {
    fire: ['FireOne1', 'FireOne2', 'Fire2', 'Fire3'],
    ice: ['IceOne1', 'IceOne2', 'Ice3', 'Ice4'],
    lightning: ['ThunderOne1', 'ThunderOne2', 'Thunder2', 'Thunder3'],
    wind: ['WindOne1', 'WindOne2', 'Wind2', 'Wind3'],
    light: ['LightOne1', 'LightOne2', 'Light2', 'Light3'],
    dark: ['Darkness1', 'Darkness2', 'Darkness3', 'Darkness4'],
    earth: ['EarthOne1', 'EarthOne2', 'Earth2', 'Earth3'],
    poison: ['Poison', 'PoisonAll', 'PoisonAll', 'PoisonAll'],
    heal: ['HealOne1', 'HealOne2', 'CureOne1', 'CureOne2'],
    generic: ['HitEffect', 'HitSP1', 'HitSP2', 'HitSpecial1'],
  };

  function effectIntensityFromAmount(amount) {
    const value = Math.abs(Number(amount) || 0);
    if (value >= 1200) return 3;
    if (value >= 700) return 2;
    if (value >= 300) return 1;
    return 0;
  }

  function resolveEffectNameForKey(typeId, amount, eventType) {
    let key = normalizeDamageTypeId(typeId);
    if (!key || key === 'none') key = 'generic';
    if (key === 'water') key = 'ice';
    if (key === 'holy') key = 'light';
    if (key === 'shadow') key = 'dark';
    const normalizedType = normalizePhaseState(eventType);
    if (normalizedType === 'heal_received' || normalizedType === 'hot_tick') {
      key = 'heal';
    } else if (normalizedType === 'dot_tick' && (!key || key === 'generic')) {
      key = 'poison';
    }
    const options = ELEMENTAL_EFFECT_TABLE[key] || ELEMENTAL_EFFECT_TABLE.generic;
    const index = Math.min(effectIntensityFromAmount(amount), options.length - 1);
    return options[index] || ELEMENTAL_EFFECT_TABLE.generic[0];
  }

  function findLast(array, predicate) {
    if (!Array.isArray(array)) return null;
    for (let i = array.length - 1; i >= 0; i -= 1) {
      const item = array[i];
      try {
        if (predicate(item)) return item;
      } catch {
        // Ignore predicate failures when matching events
      }
    }
    return null;
  }

  function selectCandidateEvent(events, attackerId, targetId) {
    if (!Array.isArray(events) || !events.length) {
      return { event: null, signature: '' };
    }
    const attackerKey = normalizeId(attackerId);
    const targetKey = normalizeId(targetId);
    const filtered = [];
    for (const evt of events) {
      if (!evt || typeof evt !== 'object') continue;
      const eventSource = normalizeId(evt.source_id ?? evt.sourceId);
      const eventTarget = normalizeId(evt.target_id ?? evt.targetId);
      if (attackerKey && eventSource && eventSource !== attackerKey) continue;
      if (targetKey && eventTarget && eventTarget !== targetKey) continue;
      filtered.push(evt);
    }
    const pool = filtered.length ? filtered : events;
    const priorities = ['damage_taken', 'dot_tick', 'heal_received', 'hot_tick', 'card_effect', 'relic_effect'];
    let selected = null;
    for (const type of priorities) {
      selected = findLast(pool, (evt) => normalizePhaseState(evt?.type) === type);
      if (selected) break;
    }
    if (!selected) {
      selected = pool[pool.length - 1];
    }
    return {
      event: selected || null,
      signature: selected ? eventToken(selected) : '',
    };
  }

  function queueElementalEffect({
    events,
    attackerId,
    targetId,
    phaseToken,
    fallbackElement,
    force = false,
  }) {
    const { event: candidate, signature } = selectCandidateEvent(events, attackerId, targetId);
    const normalizedPhaseToken = phaseToken ? String(phaseToken) : '';
    let amount = 0;
    let key = fallbackElement || 'generic';
    let eventType = '';
    if (candidate) {
      amount = Number(candidate.amount ?? candidate.value ?? 0);
      eventType = candidate.type ?? '';
      if (candidate.damageTypeId) {
        key = candidate.damageTypeId;
      } else if (candidate.metadata) {
        const meta = candidate.metadata;
        const candidateKey =
          meta.damage_type_id ??
          meta.element ??
          meta.damage_type ??
          meta.effect_type ??
          meta.effect ??
          meta.type;
        if (candidateKey) {
          key = candidateKey;
        }
      }
      const normalizedType = normalizePhaseState(candidate.type);
      if (normalizedType === 'heal_received' || normalizedType === 'hot_tick') {
        key = 'heal';
      } else if (normalizedType === 'dot_tick' && (!key || key === 'generic')) {
        key = 'poison';
      }
    }
    const effectName = resolveEffectNameForKey(key, amount, eventType);
    if (!effectName) return null;
    const compositeSignature = [
      normalizedPhaseToken,
      signature || '',
      effectName,
      normalizeId(attackerId),
      normalizeId(targetId),
    ].join('::');
    if (!force && compositeSignature === lastEffectSignature) {
      return effectName;
    }
    lastEffectSignature = compositeSignature;
    queueEffect(effectName);
    return effectName;
  }

  function enqueueHpDrains(entries) {
    if (!Array.isArray(entries) || !entries.length) return;
    queuedHpDrains = [...queuedHpDrains, ...entries];
  }

  async function releaseHpDrains({ force = false } = {}) {
    if (!force && waitingForResolve) return;
    if (!queuedHpDrains.length) return;
    const drains = queuedHpDrains;
    queuedHpDrains = [];
    if (!effectiveReducedMotion) {
      await tick();
    }
    let drained = false;
    for (const entry of drains) {
      const state = pendingLayers.get(entry.key);
      if (!state) continue;
      if (entry.kind === 'damage' && state.damageKey === entry.version && state.damage > 0) {
        pendingLayers.set(entry.key, { ...state, damage: 0 });
        drained = true;
      } else if (entry.kind === 'heal' && state.healKey === entry.version && state.heal > 0) {
        pendingLayers.set(entry.key, { ...state, heal: 0 });
        drained = true;
      }
    }
    if (drained) {
      pendingLayers = new Map(pendingLayers);
    }
  }

  let knownSummons = new Set();
  const pendingEaseCurve = 'cubic-bezier(0.25, 0.9, 0.3, 1)';
  let hpHistory = new Map();
  let pendingLayers = new Map();
  let queuedHpDrains = [];
  let waitingForResolve = false;
  let lastPhaseToken = '';
  let lastEffectSignature = '';
  let phaseSequenceCounter = 0;
  $: pendingEaseMs = Math.max(240, pollDelay * 1.5);
  const dispatch = createEventDispatcher();
  // Poll battle snapshots at (framerate / 10) times per second.
  // Example: 30fps -> 3/s, 60fps -> 6/s, 120fps -> 12/s
  let pollDelay = 10000 / framerate;
  $: pollDelay = 10000 / framerate;
  $: statusChipLifetime = effectiveReducedMotion ? Math.max(900, pollDelay * 6) : Math.max(1600, pollDelay * 10);
  let bg = getRandomBackground();

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

  function extractEffectLabel(metadata) {
    if (!metadata || typeof metadata !== 'object') return '';
    const list = Array.isArray(metadata.effects) ? metadata.effects : [];
    for (const entry of list) {
      if (!entry || typeof entry !== 'object') continue;
      if (entry.name) return String(entry.name);
      if (entry.id) return String(entry.id);
    }
    const fallbackKeys = [
      'effect_name',
      'effect',
      'effect_type',
      'effectType',
      'action_name',
      'actionName',
      'source_name',
      'sourceName',
      'source_type',
      'sourceType',
      'card_name',
      'cardName',
      'relic_name',
      'relicName',
    ];
    for (const key of fallbackKeys) {
      const value = metadata[key];
      if (value !== undefined && value !== null && String(value).trim() !== '') {
        return String(value);
      }
    }
    const details = metadata.details;
    if (details && typeof details === 'object') {
      const detailKeys = [
        'label',
        'name',
        'effect_name',
        'effect',
        'effect_type',
        'effectType',
        'action_name',
        'actionName',
        'source_name',
        'sourceName',
      ];
      for (const key of detailKeys) {
        const value = details[key];
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          return String(value);
        }
      }
    }
    return '';
  }

  function normalizeRecentEvent(evt) {
    if (!evt || typeof evt !== 'object') return null;
    const metadata = (evt.metadata && typeof evt.metadata === 'object') ? { ...evt.metadata } : {};
    let damageTypeId = metadata.damage_type_id;
    if (!damageTypeId) {
      const effects = Array.isArray(metadata.effects) ? metadata.effects : [];
      for (const effect of effects) {
        if (!effect || typeof effect !== 'object') continue;
        damageTypeId =
          effect.damage_type_id ||
          effect.element ||
          effect.damage_type ||
          effect.type;
        if (damageTypeId) break;
      }
    }
    if (!damageTypeId) {
      const fallbacks = [
        metadata.effect,
        metadata.effect_type,
        metadata.effectType,
        metadata.element,
      ];
      for (const candidate of fallbacks) {
        if (candidate !== undefined && candidate !== null && String(candidate).trim() !== '') {
          damageTypeId = candidate;
          break;
        }
      }
    }
    const amount = Number(evt.amount ?? 0);
    const isCritical = Boolean(
      metadata?.is_critical ?? metadata?.isCritical ?? metadata?.critical ?? evt.isCritical
    );
    let effectLabel = extractEffectLabel(metadata);
    if (!effectLabel) {
      const fallbackCandidates = [
        metadata.card_name,
        metadata.cardName,
        metadata.relic_name,
        metadata.relicName,
        metadata.effect,
        metadata.effect_type,
        metadata.effectType,
      ];
      for (const candidate of fallbackCandidates) {
        if (candidate !== undefined && candidate !== null && String(candidate).trim() !== '') {
          effectLabel = String(candidate);
          break;
        }
      }
    }
    return {
      ...evt,
      amount,
      damageTypeId,
      metadata,
      isCritical,
      effectLabel,
    };
  }

  function eventToken(evt) {
    if (!evt) return '';
    const metadata = evt.metadata || {};
    const effectIds = Array.isArray(metadata.effect_ids) ? metadata.effect_ids.join('|') : '';
    const cardIdentifiers = [
      metadata.card_id,
      metadata.cardId,
      metadata.card_name,
      metadata.cardName,
    ]
      .map(value => (value === undefined || value === null ? '' : String(value)))
      .join('~');
    const relicIdentifiers = [
      metadata.relic_id,
      metadata.relicId,
      metadata.relic_name,
      metadata.relicName,
    ]
      .map(value => (value === undefined || value === null ? '' : String(value)))
      .join('~');
    const label = evt.effectLabel === undefined || evt.effectLabel === null ? '' : String(evt.effectLabel);
    const effectDetails = Array.isArray(metadata.effects)
      ? metadata.effects
          .map(e =>
            [e?.type, e?.id, e?.name, e?.remaining_turns, e?.original_amount, e?.original_healing]
              .map(v => (v === undefined || v === null ? '' : String(v)))
              .join('~'),
          )
          .join('|')
      : '';
    return [
      evt.type || '',
      evt.target_id || '',
      evt.source_id || '',
      evt.amount ?? '',
      metadata.damage_type_id || '',
      metadata.is_critical ? 'crit' : '',
      effectIds,
      label,
      cardIdentifiers,
      relicIdentifiers,
      effectDetails,
    ].join('::');
  }

  // Group/dedupe recent events: show only newly increased instances per unique token
  function processRecentEvents(events) {
    if (!Array.isArray(events)) {
      recentEventCounts = new Map();
      lastRecentEventTokens = [];
      return [];
    }
    const filtered = [];
    for (const raw of events) {
      if (!raw || typeof raw !== 'object') continue;
      if (!relevantRecentEventTypes.has(raw.type)) continue;
      const normalized = normalizeRecentEvent(raw);
      if (normalized) filtered.push(normalized);
    }
    const tokens = filtered.map(eventToken);
    const nextCounts = new Map();
    const newOnes = [];
    for (let i = 0; i < filtered.length; i += 1) {
      const entry = filtered[i];
      const token = tokens[i];
      const prevCount = recentEventCounts.get(token) || 0;
      const nextCount = (nextCounts.get(token) || 0) + 1;
      nextCounts.set(token, nextCount);
      if (prevCount < nextCount) {
        newOnes.push(entry);
      }
    }
    // If a single identical event repeats (token unchanged), still surface it
    if (!newOnes.length && filtered.length === 1) {
      const [token] = tokens;
      const isIdenticalToLast = lastRecentEventTokens.length === 1 && lastRecentEventTokens[0] === token;
      if (isIdenticalToLast) newOnes.push(filtered[0]);
    }
    recentEventCounts = nextCounts;
    lastRecentEventTokens = tokens;
    return newOnes;
  }

  function differs(a, b) {
    return JSON.stringify(a) !== JSON.stringify(b);
  }

  function getSummonIdentifier(summon) {
    if (!summon || typeof summon !== 'object') return '';
    const value = summon?.instance_id ?? summon?.id;
    if (value === undefined || value === null) return '';
    try {
      return String(value);
    } catch {
      return '';
    }
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
        const ident = getSummonIdentifier(s);
        if (ident && !all.has(ident)) {
          queueEffect('SummonEffect');
          all.add(ident);
          break;
        }
      }
    }
    for (const [, summons] of foeSummons) {
      for (const s of summons) {
        const ident = getSummonIdentifier(s);
        if (ident && !all.has(ident)) {
          queueEffect('SummonEffect');
          all.add(ident);
          break;
        }
      }
    }
    knownSummons = all;
  }

  function resolveDamageTypeFromEntity(entity, fallback = '') {
    if (!entity || typeof entity !== 'object') {
      return normalizeDamageTypeId(fallback);
    }
    const primary = Array.isArray(entity.damage_types)
      ? entity.damage_types.find(Boolean)
      : null;
    const candidate =
      primary ||
      entity.damage_type ||
      entity.element ||
      entity.luna_sword_label ||
      fallback;
    return normalizeDamageTypeId(candidate);
  }

  function applyLunaSwordVisuals(entry, ownerId, baseElement = 'generic') {
    if (!entry || typeof entry !== 'object') return entry;
    const summonType = String(entry.summon_type || '').toLowerCase();
    const source = String(entry.summon_source || '').toLowerCase();
    const isSword =
      Boolean(entry.luna_sword) ||
      source === 'luna_sword' ||
      summonType.startsWith('luna_sword');
    if (!isSword) {
      return entry;
    }

    const label = entry.luna_sword_label || entry.damage_type || entry.element || baseElement;
    const visual = getLightstreamSwordVisual(label, {
      seed:
        entry.instance_id ||
        entry.id ||
        `${ownerId || ''}:${summonType || ''}:${label || ''}`
    });
    const element = visual.element || normalizeDamageTypeId(label || baseElement);

    return {
      ...entry,
      lunaSword: true,
      lunaSwordType: element,
      lunaSwordArt: visual.art,
      lunaSwordColor: getElementColor(element),
      lunaSwordPalette: visual.palette,
      element
    };
  }

  function combatantKey(kind, id, ownerId = '') {
    const parts = [kind];
    if (ownerId !== undefined && ownerId !== null && ownerId !== '') {
      parts.push(ownerId);
    }
    if (id === undefined || id === null || id === '') {
      return '';
    }
    parts.push(id);
    return parts.map(String).join(':');
  }

  function safeFraction(value, max) {
    const maxValue = Number(max) || 0;
    if (maxValue <= 0) return 0;
    const current = Number(value) || 0;
    return Math.max(0, Math.min(1, current / maxValue));
  }

  function percentFromFraction(fraction) {
    return Math.max(0, Math.min(100, Number(fraction || 0) * 100));
  }

  function normalizeId(value) {
    if (value === undefined || value === null) return '';
    try {
      return String(value);
    } catch {
      return '';
    }
  }

  function normalizePhaseState(value) {
    if (value === undefined || value === null) return '';
    try {
      return String(value).trim().toLowerCase();
    } catch {
      return '';
    }
  }

  function normalizePhasePayload(value) {
    if (value === undefined || value === null) return null;
    if (typeof value === 'string') return { state: value };
    if (typeof value === 'object') return { ...value };
    try {
      return { state: String(value) };
    } catch {
      return null;
    }
  }

  function extractPhaseId(phase, keys) {
    if (!phase || typeof phase !== 'object') return undefined;
    for (const key of keys) {
      if (Object.prototype.hasOwnProperty.call(phase, key)) {
        return phase[key];
      }
    }
    return undefined;
  }

  function resolvePhaseToken(phase) {
    if (!phase || typeof phase !== 'object') return '';
    const keys = [
      'phase_token',
      'phaseToken',
      'token',
      'id',
      'turn_id',
      'turnId',
      'action_id',
      'actionId',
      'sequence',
      'queue_index',
      'queueIndex',
      'step',
      'order',
      'turn',
      'turn_number',
      'turnNumber',
    ];
    for (const key of keys) {
      if (!Object.prototype.hasOwnProperty.call(phase, key)) continue;
      const value = phase[key];
      if (value === undefined || value === null) continue;
      try {
        const str = String(value).trim();
        if (str) return str;
      } catch {
        // ignore invalid token shapes
      }
    }
    return '';
  }

  function resetTurnPhaseState() {
    turnPhaseSeen = false;
    rawTurnPhase = null;
    turnPhaseState = '';
    turnPhaseAttackerId = null;
    turnPhaseTargetId = null;
    storedTurnPhase = null;
    normalizedTurnPhaseState = '';
    turnPhaseIsActive = false;
    phaseAllowsOverlays = true;
  }

  function applyTurnPhaseSnapshot(phase) {
    turnPhaseSeen = true;
    if (!phase || typeof phase !== 'object') {
      rawTurnPhase = null;
      turnPhaseState = '';
      turnPhaseAttackerId = null;
      turnPhaseTargetId = null;
      return {
        state: '',
        attackerId: null,
        targetId: null,
        token: null,
      };
    }
    rawTurnPhase = { ...phase };
    turnPhaseState = normalizePhaseState(
      phase.state ?? phase.phase_state ?? phase.phase ?? phase.status,
    );
    const attacker = extractPhaseId(phase, [
      'attacker_id',
      'attackerId',
      'source_id',
      'actor_id',
      'active_id',
    ]);
    if (attacker !== undefined) {
      turnPhaseAttackerId = attacker ?? null;
    }
    const target = extractPhaseId(phase, [
      'target_id',
      'targetId',
      'defender_id',
      'target',
    ]);
    if (target !== undefined) {
      turnPhaseTargetId = target ?? null;
    }
    if (turnPhaseState === 'end') {
      turnPhaseAttackerId = null;
      turnPhaseTargetId = null;
    }
    const token = resolvePhaseToken(phase) || null;
    return {
      state: turnPhaseState,
      attackerId: turnPhaseAttackerId ?? null,
      targetId: turnPhaseTargetId ?? null,
      token,
    };
  }

  function handlePhaseTransition(info, events) {
    const normalizedEvents = Array.isArray(events) ? events : [];
    if (!info || !info.state) {
      if (normalizedEvents.length) {
        const fallbackAttacker = normalizeId(
          turnPhaseAttackerId ?? snapshotActiveId ?? activeId ?? null,
        );
        const fallbackTarget = normalizeId(
          turnPhaseTargetId ?? snapshotActiveTargetId ?? activeTargetId ?? null,
        );
        const attackerEntity = combatantById.get(fallbackAttacker);
        const fallbackElement = resolveDamageTypeFromEntity(attackerEntity, 'generic');
        const { signature } = selectCandidateEvent(normalizedEvents, fallbackAttacker, fallbackTarget);
        phaseSequenceCounter += 1;
        queueElementalEffect({
          events: normalizedEvents,
          attackerId: fallbackAttacker,
          targetId: fallbackTarget,
          phaseToken: `fallback::${signature || phaseSequenceCounter}`,
          fallbackElement,
          force: false,
        });
      }
      waitingForResolve = false;
      lastPhaseToken = '';
      return true;
    }

    const state = normalizePhaseState(info.state);
    const attackerId = normalizeId(info.attackerId ?? turnPhaseAttackerId ?? snapshotActiveId ?? activeId ?? null);
    const targetId = normalizeId(info.targetId ?? turnPhaseTargetId ?? snapshotActiveTargetId ?? activeTargetId ?? null);
    const attackerEntity = combatantById.get(attackerId);
    const fallbackElement = resolveDamageTypeFromEntity(attackerEntity, 'generic');

    let tokenBase = info.token ? String(info.token) : '';
    if (!tokenBase) {
      phaseSequenceCounter += 1;
      tokenBase = `${attackerId || 'unknown'}::${targetId || 'unknown'}::${phaseSequenceCounter}`;
    }

    if (state === 'start') {
      waitingForResolve = true;
      const phaseSignature = `${state}:${tokenBase}`;
      if (phaseSignature !== lastPhaseToken) {
        queueElementalEffect({
          events: normalizedEvents,
          attackerId,
          targetId,
          phaseToken: phaseSignature,
          fallbackElement,
          force: true,
        });
        lastPhaseToken = phaseSignature;
      }
      return false;
    }

    waitingForResolve = false;
    lastPhaseToken = '';
    if (!state || state === 'resolve' || state === 'end') {
      return true;
    }
    return true;
  }

  function resolveCombatantNameById(id) {
    const key = normalizeId(id);
    if (!key) return '';
    const fighter = combatantById.get(key);
    if (!fighter) return '';
    const raw = fighter.name || fighter.id || '';
    return typeof raw === 'string' ? raw.replace(/[_-]+/g, ' ') : String(raw);
  }

  function resolveStatusLabel(phase) {
    const key = String(phase || '').toLowerCase();
    if (!key) return '';
    if (key === 'hot') return 'HoTs';
    if (key === 'dot') return 'DoTs';
    return key.charAt(0).toUpperCase() + key.slice(1);
  }

  function resolveStatusColor(phase) {
    const key = String(phase || '').toLowerCase();
    if (key === 'hot') return 'rgba(66, 214, 163, 0.95)';
    if (key === 'dot') return 'rgba(255, 107, 107, 0.95)';
    return 'rgba(180, 180, 196, 0.9)';
  }

  function clearStatusTimeline() {
    for (const timer of statusRemovalTimers.values()) {
      clearTimeout(timer);
    }
    statusRemovalTimers.clear();
    statusEntryMap.clear();
    statusTimeline = [];
  }

  function scheduleStatusRemoval(key) {
    if (!key) return;
    if (statusRemovalTimers.has(key)) {
      clearTimeout(statusRemovalTimers.get(key));
      statusRemovalTimers.delete(key);
    }
    const delay = Math.max(0, Number(statusChipLifetime) || 0);
    if (!delay) {
      statusEntryMap.delete(key);
      statusTimeline = Array.from(statusEntryMap.values()).sort((a, b) => a.createdAt - b.createdAt);
      return;
    }
    const handle = setTimeout(() => {
      statusRemovalTimers.delete(key);
      statusEntryMap.delete(key);
      statusTimeline = Array.from(statusEntryMap.values()).sort((a, b) => a.createdAt - b.createdAt);
    }, delay);
    statusRemovalTimers.set(key, handle);
  }

  function updateStatusTimeline(phase) {
    if (!phase || typeof phase !== 'object') return;
    const normalizedPhase = String(phase.phase || '').toLowerCase();
    const label = resolveStatusLabel(normalizedPhase);
    const orderValue = Number.isFinite(Number(phase.order)) ? Number(phase.order) : 0;
    const targetKey = normalizeId(phase.target_id);
    const entryKey = `${targetKey}::${normalizedPhase}::${orderValue}`;
    if (!entryKey.trim()) return;

    const state = String(phase.state || 'start').toLowerCase();

    if (statusRemovalTimers.has(entryKey) && state !== 'end') {
      clearTimeout(statusRemovalTimers.get(entryKey));
      statusRemovalTimers.delete(entryKey);
    }

    const existing = statusEntryMap.get(entryKey);
    const entry = existing || { key: entryKey, createdAt: Date.now() };

    const rawIds = Array.isArray(phase.effect_ids) ? phase.effect_ids : [];
    const rawNames = Array.isArray(phase.effect_names) ? phase.effect_names : [];
    const effectIds = rawIds
      .map((value) => String(value ?? '').trim())
      .filter((value) => value.length > 0);
    const effectNames = rawNames
      .map((value) => String(value ?? '').trim())
      .filter((value) => value.length > 0);

    entry.phase = normalizedPhase;
    entry.label = label || (normalizedPhase ? normalizedPhase.toUpperCase() : '');
    entry.state = state;
    entry.effectCount = Number.isFinite(Number(phase.effect_count)) ? Number(phase.effect_count) : 0;
    entry.expiredCount = Number.isFinite(Number(phase.expired_count)) ? Number(phase.expired_count) : 0;
    entry.hasEffects = Boolean(phase.has_effects);
    entry.targetId = targetKey || null;
    entry.targetName = resolveCombatantNameById(targetKey);
    entry.order = orderValue;
    entry.color = resolveStatusColor(normalizedPhase);
    entry.updatedAt = Date.now();
    entry.effectIds = effectIds;
    entry.effectNames = effectNames;
    entry.effectSummary = effectNames.length
      ? effectNames.join(', ')
      : effectIds.join(', ');

    statusEntryMap.set(entryKey, entry);

    let entries = Array.from(statusEntryMap.values()).sort((a, b) => {
      if (a.createdAt === b.createdAt) return a.order - b.order;
      return a.createdAt - b.createdAt;
    });

    const maxEntries = 4;
    if (entries.length > maxEntries) {
      const trimmed = entries.slice(0, entries.length - maxEntries);
      for (const item of trimmed) {
        statusEntryMap.delete(item.key);
        if (statusRemovalTimers.has(item.key)) {
          clearTimeout(statusRemovalTimers.get(item.key));
          statusRemovalTimers.delete(item.key);
        }
      }
      entries = Array.from(statusEntryMap.values()).sort((a, b) => {
        if (a.createdAt === b.createdAt) return a.order - b.order;
        return a.createdAt - b.createdAt;
      });
    }

    statusTimeline = entries;

    if (entry.state === 'end') {
      scheduleStatusRemoval(entryKey);
    }
  }

  function describeStatusChip(entry) {
    if (!entry) return '';
    if (entry.state === 'start') {
      if (entry.effectCount > 0) return `${entry.effectCount} active`;
      return entry.hasEffects ? 'Processing' : 'No effects';
    }
    if (entry.expiredCount > 0) {
      return `${entry.expiredCount} expired`;
    }
    if (entry.effectCount > 0) {
      return `${entry.effectCount} remain`;
    }
    return 'Complete';
  }

  function recordHpSnapshot(key, hpValue, maxValue) {
    if (!key) return { drains: [], state: null };
    const max = Math.max(1, Number(maxValue || 0));
    const current = Math.max(0, Math.min(max, Number(hpValue || 0)));
    const prev = hpHistory.has(key) ? hpHistory.get(key) : current;
    const prevClamped = Math.max(0, Math.min(max, Number(prev || 0)));
    const currentFraction = current / max;
    const prevFraction = prevClamped / max;
    let pendingDamage = 0;
    let pendingHeal = 0;
    if (current < prevClamped) {
      pendingDamage = prevFraction - currentFraction;
    } else if (current > prevClamped) {
      pendingHeal = currentFraction - prevFraction;
    }

    const existing = pendingLayers.get(key) || {
      damageKey: 0,
      healKey: 0,
      damage: 0,
      heal: 0,
      prevFraction,
      currentFraction,
    };

    let damage = existing.damage || 0;
    let heal = existing.heal || 0;
    let damageKey = existing.damageKey || 0;
    let healKey = existing.healKey || 0;

    const drains = [];
    if (pendingDamage > 0) {
      damageKey += 1;
      damage = pendingDamage;
      heal = 0;
      drains.push({ key, kind: 'damage', version: damageKey });
    } else if (pendingHeal > 0) {
      healKey += 1;
      heal = pendingHeal;
      damage = 0;
      drains.push({ key, kind: 'heal', version: healKey });
    }

    const next = {
      prevFraction: pendingDamage > 0 || pendingHeal > 0 ? prevFraction : existing.prevFraction ?? prevFraction,
      currentFraction,
      damage,
      heal,
      damageKey,
      healKey,
    };

    pendingLayers.set(key, next);
    hpHistory.set(key, current);

    return { drains, state: next };
  }

  function getHpState(key) {
    if (!key) return null;
    return pendingLayers.get(key) || null;
  }

  async function fetchSnapshot() {
    if (!active || !runId) return;
    if (isSyncHalted()) {
      clearPollTimer();
      return;
    }
    const start = performance.now();
    dispatch('snapshot-start');
    let haltedDuringFetch = false;
    try {
      const snap = await roomAction(runId, 'battle', 'snapshot');
      if (isSyncHalted()) {
        haltedDuringFetch = true;
        return;
      }
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

      const seenHpKeys = new Set();
      const pendingDrains = [];
      const summonCounters = new Map();

      function trackHp(key, hpValue, maxValue) {
        if (!key) return;
        seenHpKeys.add(key);
        const { drains } = recordHpSnapshot(key, hpValue, maxValue);
        if (drains?.length) {
          pendingDrains.push(...drains);
        }
      }

      function prepareSummon(summon, ownerId, side) {
        if (!summon) return null;
        let baseId = getSummonIdentifier(summon);
        if (!baseId) {
          const typeLabel = summon?.summon_type || summon?.type || 'summon';
          const ownerLabel = summon?.summoner_id || ownerId || 'owner';
          const counterKey = `${side}:${ownerLabel}:${typeLabel}`;
          const count = summonCounters.get(counterKey) || 0;
          summonCounters.set(counterKey, count + 1);
          baseId = `${typeLabel}_${ownerLabel}_${count}`;
        }
        const key = combatantKey(`${side}-summon`, baseId, ownerId);
        if (key) {
          trackHp(key, summon.hp, summon.max_hp);
        }
        const baseElement = resolveDamageTypeFromEntity(summon);
        let result = { ...summon, hpKey: key };
        if (baseElement && baseElement !== 'generic') {
          result = { ...result, element: baseElement };
        }
        result = applyLunaSwordVisuals(result, ownerId, baseElement);
        return result;
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
          const processed = prepareSummon(s, owner, 'party');
          if (!partySummons.has(owner)) partySummons.set(owner, []);
          if (processed) partySummons.get(owner).push(processed);
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
          const processed = prepareSummon(s, owner, 'foe');
          if (!foeSummons.has(owner)) foeSummons.set(owner, []);
          if (processed) foeSummons.get(owner).push(processed);
        }
      }

      detectSummons(partySummons, foeSummons);

      if (snap.enrage && differs(snap.enrage, enrage)) enrage = snap.enrage;
      
      if (snap.party) {
        // Build a set of summon IDs owned by party members to avoid duplicating them
        const partySummonIds = (() => {
          const set = new Set();
          try {
            for (const list of partySummons.values()) {
              for (const s of list) {
                const ident = getSummonIdentifier(s);
                if (ident) set.add(ident);
              }
            }
          } catch {}
          return set;
        })();

        const prevById = new Map((party || []).map(p => [p.id, p]));
        const base = (snap.party || []).filter(m => {
          const id = (typeof m === 'object' ? m?.id : m) || '';
          const isSummon = typeof m === 'object' && (m?.summon_type || m?.type === 'summon' || m?.is_summon);
          return id && !isSummon && !partySummonIds.has(id);
        });
        const enriched = base.map(m => {
          const hpKey = combatantKey('party', m?.id);
          trackHp(hpKey, m?.hp, m?.max_hp);
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
          const summons = (partySummons.get(m.id) || []).map(s => ({ ...s }));
          return { ...m, element: resolved, summons, hpKey };
        });
        if (differs(enriched, party)) party = enriched;
      }

      if (snap.foes) {
        const prevById = new Map((foes || []).map(f => [f.id, f]));
        const enrichedFoes = (snap.foes || []).map(f => {
          const hpKey = combatantKey('foe', f?.id);
          trackHp(hpKey, f?.hp, f?.max_hp);
          let elem =
            (Array.isArray(f.damage_types) && f.damage_types[0]) ||
            f.damage_type ||
            f.element;
          let resolved = typeof elem === 'string' ? elem : (elem?.id || elem?.name);
          if (!resolved) {
            const prev = prevById.get(f.id);
            resolved = prev?.element || prev?.damage_type || '';
          }
          const summons = (foeSummons.get(f.id) || []).map(s => ({ ...s }));
          return { ...f, element: resolved, summons, hpKey };
        });
        if (differs(enrichedFoes, foes)) foes = enrichedFoes;
      }

      let removedKeys = false;
      for (const key of Array.from(pendingLayers.keys())) {
        if (!seenHpKeys.has(key)) {
          pendingLayers.delete(key);
          removedKeys = true;
        }
      }
      for (const key of Array.from(hpHistory.keys())) {
        if (!seenHpKeys.has(key)) {
          hpHistory.delete(key);
        }
      }

      if (removedKeys || seenHpKeys.size || pendingDrains.length) {
        pendingLayers = new Map(pendingLayers);
      }

      enqueueHpDrains(pendingDrains);

      if (Array.isArray(snap.queue || snap.action_queue)) {
        queue = snap.queue || snap.action_queue;
      }
      if ("show_action_values" in snap) {
        serverShowActionValues = Boolean(snap.show_action_values);
      }

      if ('active_id' in snap) {
        snapshotActiveId = snap.active_id ?? null;
      }
      if ('active_target_id' in snap) {
        snapshotActiveTargetId = snap.active_target_id ?? null;
      }
      let phaseInfo = null;
      if ('turn_phase' in snap) {
        const normalizedPhase = normalizePhasePayload(snap.turn_phase);
        if (!normalizedPhase) {
          resetTurnPhaseState();
          phaseInfo = { state: '', attackerId: null, targetId: null, token: null };
        } else {
          phaseInfo = applyTurnPhaseSnapshot(normalizedPhase);
        }
      } else if (!turnPhaseSeen) {
        resetTurnPhaseState();
        phaseInfo = { state: '', attackerId: null, targetId: null, token: null };
      } else {
        phaseInfo = {
          state: '',
          attackerId: turnPhaseAttackerId ?? null,
          targetId: turnPhaseTargetId ?? null,
          token: null,
        };
      }
      if ('status_phase' in snap) {
        const nextPhase = snap.status_phase && typeof snap.status_phase === 'object' ? { ...snap.status_phase } : null;
        statusPhase = nextPhase;
        if (nextPhase) updateStatusTimeline(nextPhase);
      }

      let normalizedEvents = [];
      if (Array.isArray(snap.recent_events)) {
        normalizedEvents = snap.recent_events
          .map(event => normalizeRecentEvent(event))
          .filter(Boolean);
      }

      const shouldForceRelease = handlePhaseTransition(phaseInfo, normalizedEvents);

      if (Array.isArray(snap.recent_events)) {
        recentEvents = normalizedEvents;
        floaterFeed = processRecentEvents(snap.recent_events);
      } else {
        recentEvents = [];
        floaterFeed = [];
        recentEventCounts = new Map();
        lastRecentEventTokens = [];
      }

      await releaseHpDrains({ force: shouldForceRelease || !waitingForResolve });

      const determineTurn = () => {
        if (!snap || typeof snap !== 'object') return null;
        if ('turn' in snap) return snap.turn;
        if ('turn_count' in snap) return snap.turn_count;
        if ('current_turn' in snap) return snap.current_turn;
        if ('turnNumber' in snap) return snap.turnNumber;
        if ('turn_index' in snap) return snap.turn_index;
        return null;
      };
      const nextTurn = determineTurn();
      if (nextTurn !== null && nextTurn !== undefined) {
        const numericTurn = Number(nextTurn);
        currentTurn = Number.isFinite(numericTurn) ? numericTurn : nextTurn;
      }

      if (Array.isArray(snap.log)) logs = snap.log;
      else if (Array.isArray(snap.logs)) logs = snap.logs;

      // After applying snapshot updates, re-measure anchors because layout may have shifted
      // (e.g., foes/party removed) which doesn’t trigger node ResizeObserver.
      await tick();
      recomputeAllAnchors();
    } catch (e) {
      // Silently ignore errors to avoid spam during rapid polling
    } finally {
      dispatch('snapshot-end');
      if (isSyncHalted() || haltedDuringFetch) {
        clearPollTimer();
        return;
      }
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
    clearPollTimer();
    clearStatusTimeline();
  });

  // Watch active state changes
  $: if (active && runId && !timer) {
    fetchSnapshot();
  } else if (!active && timer) {
    clearPollTimer();
  }
</script>

<div
  class="modern-battle-field"
  style={`background-image: url("${bg}")`}
  data-testid="modern-battle-view"
  bind:this={rootEl}
>
  <EnrageIndicator active={Boolean(enrage?.active)} reducedMotion={effectiveReducedMotion} enrageData={enrage} />
  <BattleEffects cue={effectCue} />
  <BattleEventFloaters
    class="overlay-layer"
    events={floaterFeed}
    reducedMotion={effectiveReducedMotion}
    paceMs={floaterDuration}
    anchors={anchors}
    baseOffsetX={16}
    baseOffsetY={8}
    staggerMs={220}
  />
  <BattleTargetingOverlay
    class="overlay-layer"
    {activeId}
    {activeTargetId}
    anchors={anchors}
    {combatants}
    events={recentEvents}
    reducedMotion={effectiveReducedMotion}
    turnPhase={storedTurnPhase}
  />
  {#if showStatusTimeline && statusTimeline.length && phaseAllowsOverlays}
    <div class:reduced={effectiveReducedMotion} class="status-timeline overlay-layer" aria-live="polite">
      {#each statusTimeline as chip (chip.key)}
        <div class="timeline-chip" data-state={chip.state} style={`--chip-color:${chip.color};`}>
          <span class="chip-phase">{chip.label}</span>
          {#if chip.targetName}
            <span class="chip-target">→ {chip.targetName}</span>
          {/if}
          {#if chip.effectIds?.length}
            <span
              class="chip-effects"
              title={chip.effectSummary || chip.effectIds.join(', ')}
            >
              IDs: {chip.effectIds.join(', ')}
            </span>
          {/if}
          <span class="chip-meta">{describeStatusChip(chip)}</span>
        </div>
      {/each}
    </div>
  {/if}
  <ActionQueue
    {queue}
    {combatants}
    reducedMotion={effectiveReducedMotion}
    effectiveReducedMotion={effectiveReducedMotion}
    {activeId}
    {currentTurn}
    {enrage}
    {showTurnCounter}
    {flashEnrageCounter}
    showActionValues={displayActionValues}
    on:hover={(e) => hoveredId = e.detail?.id || null}
  />

  <!-- Foes at the top -->
  {#if showFoes}
    <div class="foe-row">
      {#each foes as foe (foe.id)}
        {@const hpState = getHpState(foe.hpKey)}
        {@const hpFraction = hpState ? hpState.currentFraction : safeFraction(foe.hp, foe.max_hp)}
        {@const prevFraction = hpState ? hpState.prevFraction : hpFraction}
        {@const hpPercent = percentFromFraction(hpFraction)}
        {@const damageWidth = percentFromFraction(hpState?.damage)}
        {@const healWidth = percentFromFraction(hpState?.heal)}
        {@const damageLeft = percentFromFraction(hpFraction)}
        {@const healLeft = percentFromFraction(prevFraction)}
        {@const damageOpacity = damageWidth > 0 ? 0.9 : 0}
        {@const healOpacity = healWidth > 0 ? 0.9 : 0}
        <div
          class="foe-container"
          in:fade={{ duration: effectiveReducedMotion ? 0 : 300 }}
          out:fade={{ duration: effectiveReducedMotion ? 0 : 600 }}
        >
          <!-- Buffs at the very top -->
          <div class="foe-buffs">
            {#if foe.passives?.length || foe.dots?.length || foe.hots?.length}
              <!-- Buff bar shows HoTs, DoTs, and Passives -->
              <StatusIcons layout="bar" hots={(foe.hots || []).slice(0, 6)} dots={(foe.dots || []).slice(0, 6)} active_effects={(foe.passives || []).slice(0, 6)} />
            {/if}
          </div>
          
          <!-- HP bar on top -->
          <div class="foe-hp-bar" style={`width: ${getFoeSizePx(foeCount)}px`}>
            <div class="hp-bar-wrapper">
              {#if Number(foe?.shields || 0) > 0 && Number(foe?.max_hp || 0) > 0}
                <div
                  class="overheal-fill"
                  style={`width: calc(${Math.max(0, Math.min(100, (Number(foe.shields || 0) / Math.max(1, Number(foe.max_hp || 0))) * 100))}% + 5px); left: -5px;`}
                ></div>
              {/if}
              <div class="hp-bar-container" class:reduced={effectiveReducedMotion}>
                <div
                  class="hp-bar-fill"
                  style="width: {hpPercent}%;
                         background: {hpFraction <= 0.3 ? 'linear-gradient(90deg, #ff4444, #ff6666)' : 'linear-gradient(90deg, #44ffff, #66dddd)'}"
                ></div>
                <div
                  class="hp-bar-overlay damage"
                  style={`left: ${damageLeft}%; width: ${damageWidth}%; opacity: ${damageOpacity}; --pending-duration: ${effectiveReducedMotion ? 0 : pendingEaseMs}ms; --pending-ease: ${pendingEaseCurve};`}
                ></div>
                <div
                  class="hp-bar-overlay heal"
                  style={`left: ${healLeft}%; width: ${healWidth}%; opacity: ${healOpacity}; --pending-duration: ${effectiveReducedMotion ? 0 : pendingEaseMs}ms; --pending-ease: ${pendingEaseCurve};`}
                ></div>
                {#if foe.hp < foe.max_hp}
                  <div class="hp-text" data-position="outline">{foe.hp}</div>
                {/if}
              </div>
            </div>
          </div>
          
          <!-- Character photo/portrait -->
          <div class="fighter-anchor" use:registerAnchor={foe.id}>
            <BattleFighterCard fighter={foe} position="top" {effectiveReducedMotion} sizePx={getFoeSizePx(foeCount)} highlight={hoveredId === foe.id} />
          </div>
          
          <!-- Summons -->
          {#if foe.summons?.length}
            <div class="summon-list">
              {#each foe.summons as summon (summon.instance_id || summon.id)}
                <div
                  class="summon-entry"
                  in:fade={{ duration: effectiveReducedMotion ? 0 : 200 }}
                  out:fade={{ duration: effectiveReducedMotion ? 0 : 450 }}
                >
                  <div in:scale={{ duration: effectiveReducedMotion ? 0 : 200 }} class="summon-inner">
                    <!-- Summon HP bar -->
                    {#if true}
                      {@const hpState = getHpState(summon.hpKey)}
                      {@const hpFraction = hpState ? hpState.currentFraction : safeFraction(summon.hp, summon.max_hp)}
                      {@const prevFraction = hpState ? hpState.prevFraction : hpFraction}
                      {@const hpPercent = percentFromFraction(hpFraction)}
                      {@const damageWidth = percentFromFraction(hpState?.damage)}
                      {@const healWidth = percentFromFraction(hpState?.heal)}
                      {@const damageLeft = percentFromFraction(hpFraction)}
                      {@const healLeft = percentFromFraction(prevFraction)}
                      {@const damageOpacity = damageWidth > 0 ? 0.9 : 0}
                      {@const healOpacity = healWidth > 0 ? 0.9 : 0}
                      <div class="summon-hp-bar">
                        <div class="hp-bar-wrapper">
                          {#if Number(summon?.shields || 0) > 0 && Number(summon?.max_hp || 0) > 0}
                            <div
                              class="overheal-fill"
                              style={`width: calc(${Math.max(0, Math.min(100, (Number(summon.shields || 0) / Math.max(1, Number(summon.max_hp || 0))) * 100))}% + 5px); left: -5px;`}
                            ></div>
                          {/if}
                          <div class="hp-bar-container" class:reduced={effectiveReducedMotion}>
                            <div
                              class="hp-bar-fill"
                              style="width: {hpPercent}%;
                                     background: {hpFraction <= 0.3 ? 'linear-gradient(90deg, #ff4444, #ff6666)' : 'linear-gradient(90deg, #44ffff, #66dddd)'}"
                            ></div>
                            <div
                              class="hp-bar-overlay damage"
                              style={`left: ${damageLeft}%; width: ${damageWidth}%; opacity: ${damageOpacity}; --pending-duration: ${effectiveReducedMotion ? 0 : pendingEaseMs}ms; --pending-ease: ${pendingEaseCurve};`}
                            ></div>
                            <div
                              class="hp-bar-overlay heal"
                              style={`left: ${healLeft}%; width: ${healWidth}%; opacity: ${healOpacity}; --pending-duration: ${effectiveReducedMotion ? 0 : pendingEaseMs}ms; --pending-ease: ${pendingEaseCurve};`}
                            ></div>
                            {#if summon.hp < summon.max_hp}
                              <div class="hp-text" data-position="outline">{summon.hp}</div>
                            {/if}
                          </div>
                        </div>
                      </div>
                    {/if}
                    
                    <div class="fighter-anchor" use:registerAnchor={summon.instance_id || summon.id}>
                      <BattleFighterCard 
                        fighter={summon} 
                        position="top" 
                        {effectiveReducedMotion} 
                        size="medium" 
                        highlight={hoveredId === (summon.instance_id || summon.id) || (hoveredId && summon?.summoner_id && summon?.summon_type && hoveredId === `${summon.summoner_id}_${summon.summon_type}_summon`)}
                      />
                    </div>
                  </div>
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
      <div
        class="party-container"
        in:fade={{ duration: effectiveReducedMotion ? 0 : 300 }}
        out:fade={{ duration: effectiveReducedMotion ? 0 : 600 }}
      >
        <!-- Summons (show above player portrait for party) -->
        {#if member.summons?.length}
          <div class="summon-list">
            {#each member.summons as summon (summon.instance_id || summon.id)}
              <div
                class="summon-entry"
                in:fade={{ duration: effectiveReducedMotion ? 0 : 200 }}
                out:fade={{ duration: effectiveReducedMotion ? 0 : 450 }}
              >
                <div in:scale={{ duration: effectiveReducedMotion ? 0 : 200 }} class="summon-inner">
                  <!-- Summon portrait -->
                  <div class="fighter-anchor" use:registerAnchor={summon.instance_id || summon.id}>
                    <BattleFighterCard
                      fighter={summon}
                      position="bottom"
                      {effectiveReducedMotion}
                      size="medium" 
                      highlight={hoveredId === (summon.instance_id || summon.id) || (hoveredId && summon?.summoner_id && summon?.summon_type && hoveredId === `${summon.summoner_id}_${summon.summon_type}_summon`)}
                    />
                  </div>

                  <!-- Summon HP bar under portrait -->
                  {#if true}
                    {@const hpState = getHpState(summon.hpKey)}
                    {@const hpFraction = hpState ? hpState.currentFraction : safeFraction(summon.hp, summon.max_hp)}
                    {@const prevFraction = hpState ? hpState.prevFraction : hpFraction}
                    {@const hpPercent = percentFromFraction(hpFraction)}
                    {@const damageWidth = percentFromFraction(hpState?.damage)}
                    {@const healWidth = percentFromFraction(hpState?.heal)}
                    {@const damageLeft = percentFromFraction(hpFraction)}
                    {@const healLeft = percentFromFraction(prevFraction)}
                    {@const damageOpacity = damageWidth > 0 ? 0.9 : 0}
                    {@const healOpacity = healWidth > 0 ? 0.9 : 0}
                    <div class="summon-hp-bar">
                      <div class="hp-bar-wrapper">
                        {#if Number(summon?.shields || 0) > 0 && Number(summon?.max_hp || 0) > 0}
                          <div
                            class="overheal-fill"
                            style={`width: calc(${Math.max(0, Math.min(100, (Number(summon.shields || 0) / Math.max(1, Number(summon.max_hp || 0))) * 100))}% + 5px); left: -5px;`}
                          ></div>
                        {/if}
                        <div class="hp-bar-container" class:reduced={effectiveReducedMotion}>
                          <div
                            class="hp-bar-fill"
                            style="width: {hpPercent}%;
                                   background: {hpFraction <= 0.3 ? 'linear-gradient(90deg, #ff4444, #ff6666)' : 'linear-gradient(90deg, #44ffff, #66dddd)'}"
                          ></div>
                          <div
                            class="hp-bar-overlay damage"
                            style={`left: ${damageLeft}%; width: ${damageWidth}%; opacity: ${damageOpacity}; --pending-duration: ${effectiveReducedMotion ? 0 : pendingEaseMs}ms; --pending-ease: ${pendingEaseCurve};`}
                          ></div>
                          <div
                            class="hp-bar-overlay heal"
                            style={`left: ${healLeft}%; width: ${healWidth}%; opacity: ${healOpacity}; --pending-duration: ${effectiveReducedMotion ? 0 : pendingEaseMs}ms; --pending-ease: ${pendingEaseCurve};`}
                          ></div>
                          {#if summon.hp < summon.max_hp}
                            <div class="hp-text" data-position="outline">{summon.hp}</div>
                          {/if}
                        </div>
                      </div>
                    </div>
                  {/if}

                  <!-- Summon buffs under HP bar -->
                  <div class="summon-buffs">
                    {#if summon.passives?.length || summon.dots?.length || summon.hots?.length}
                      <StatusIcons layout="bar" hots={(summon.hots || []).slice(0, 6)} dots={(summon.dots || []).slice(0, 6)} active_effects={(summon.passives || []).slice(0, 6)} />
                    {/if}
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}

        <div class="party-main fighter-anchor" use:registerAnchor={member.id}>
          <!-- Character photo as base (ult & pips overlay handled inside) -->
          <BattleFighterCard fighter={member} position="bottom" {effectiveReducedMotion} highlight={hoveredId === member.id} />
        </div>
        
        <!-- HP bar under the photo -->
        {#if true}
          {@const hpState = getHpState(member.hpKey)}
          {@const hpFraction = hpState ? hpState.currentFraction : safeFraction(member.hp, member.max_hp)}
          {@const prevFraction = hpState ? hpState.prevFraction : hpFraction}
          {@const hpPercent = percentFromFraction(hpFraction)}
          {@const damageWidth = percentFromFraction(hpState?.damage)}
          {@const healWidth = percentFromFraction(hpState?.heal)}
          {@const damageLeft = percentFromFraction(hpFraction)}
          {@const healLeft = percentFromFraction(prevFraction)}
          {@const damageOpacity = damageWidth > 0 ? 0.9 : 0}
          {@const healOpacity = healWidth > 0 ? 0.9 : 0}
          <div class="party-hp-bar">
            <div class="hp-bar-wrapper">
              {#if Number(member?.shields || 0) > 0 && Number(member?.max_hp || 0) > 0}
                <div
                  class="overheal-fill"
                  style={`width: calc(${Math.max(0, Math.min(100, (Number(member.shields || 0) / Math.max(1, Number(member.max_hp || 0))) * 100))}% + 5px); left: -5px;`}
                ></div>
              {/if}
              <div class="hp-bar-container" class:reduced={effectiveReducedMotion}>
                <div
                  class="hp-bar-fill"
                  style="width: {hpPercent}%;
                         background: {hpFraction <= 0.3 ? 'linear-gradient(90deg, #ff4444, #ff6666)' : 'linear-gradient(90deg, #44ffff, #66dddd)'}"
                ></div>
                <div
                  class="hp-bar-overlay damage"
                  style={`left: ${damageLeft}%; width: ${damageWidth}%; opacity: ${damageOpacity}; --pending-duration: ${effectiveReducedMotion ? 0 : pendingEaseMs}ms; --pending-ease: ${pendingEaseCurve};`}
                ></div>
                <div
                  class="hp-bar-overlay heal"
                  style={`left: ${healLeft}%; width: ${healWidth}%; opacity: ${healOpacity}; --pending-duration: ${effectiveReducedMotion ? 0 : pendingEaseMs}ms; --pending-ease: ${pendingEaseCurve};`}
                ></div>
                {#if member.hp < member.max_hp}
                  <div class="hp-text" data-position="outline">{member.hp}</div>
                {/if}
              </div>
            </div>
          </div>
        {/if}
        
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

  .modern-battle-field > *:not(.action-queue):not(.overlay-layer) {
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
  .hp-bar-wrapper {
    position: relative;
    width: 100%;
    height: 10px; /* match container height for proper anchoring */
  }

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
    position: absolute;
    left: 0;
    top: 0;
    z-index: 1; /* draw above overheal/shields */
  }

  /* Overheal/shields visual overlay (similar to LegacyFighterPortrait) */
  .overheal-fill {
    position: absolute;
    left: 0;
    top: -1px; /* nudged up by 1px for alignment */
    height: calc(100% + 4px);
    background: rgba(255, 255, 255, 0.92);
    transition: width 0.3s linear;
    pointer-events: none;
    z-index: 0; /* below main HP fill */
  }

  .hp-bar-overlay {
    position: absolute;
    top: 0;
    height: 100%;
    pointer-events: none;
    z-index: 2;
    transition-property: width, opacity;
    transition-duration: var(--pending-duration, 360ms);
    transition-timing-function: var(--pending-ease, cubic-bezier(0.25, 0.9, 0.3, 1));
    opacity: 0;
  }

  .hp-bar-overlay.damage {
    background: linear-gradient(90deg, rgba(255, 72, 72, 0.85), rgba(255, 24, 24, 0.65));
  }

  .hp-bar-overlay.heal {
    background: linear-gradient(90deg, rgba(80, 255, 180, 0.85), rgba(32, 192, 120, 0.65));
  }

  .hp-bar-container.reduced .hp-bar-fill {
    transition: none;
  }

  .hp-bar-container.reduced .overheal-fill {
    transition: none;
  }

  .hp-bar-container.reduced .hp-bar-overlay {
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
    z-index: 3;
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

  .status-timeline {
    position: absolute;
    top: clamp(0.75rem, 4vh, 2.5rem);
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 0.65rem;
    align-items: center;
    pointer-events: none;
    z-index: 4;
  }

  .status-timeline .timeline-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.85rem;
    border-radius: 999px;
    background: rgba(18, 18, 26, 0.78);
    border: 1px solid var(--chip-color, rgba(255, 255, 255, 0.35));
    color: #f4f4f6;
    font-weight: 600;
    font-size: 0.85rem;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35);
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .status-timeline .timeline-chip .chip-phase {
    color: var(--chip-color, #9fc5ff);
    letter-spacing: 0.08em;
  }

  .status-timeline .timeline-chip .chip-target {
    font-size: 0.78rem;
    opacity: 0.85;
    text-transform: none;
  }

  .status-timeline .timeline-chip .chip-effects {
    font-size: 0.72rem;
    opacity: 0.85;
    text-transform: none;
    font-family: 'JetBrains Mono', 'Fira Mono', monospace;
    letter-spacing: 0.02em;
    white-space: nowrap;
  }

  .status-timeline .timeline-chip .chip-meta {
    font-size: 0.75rem;
    opacity: 0.8;
    text-transform: none;
  }

  .status-timeline:not(.reduced) .timeline-chip {
    animation: timeline-enter 0.28s ease-out;
  }

  .status-timeline.reduced .timeline-chip {
    animation: none;
  }

  .status-timeline .timeline-chip[data-state='end'] {
    background: rgba(18, 18, 26, 0.64);
    border-color: var(--chip-color, #9fc5ff);
    border-color: color-mix(in srgb, var(--chip-color, #9fc5ff) 65%, #ffffff 35%);
  }

  @keyframes timeline-enter {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @media (max-width: 900px) {
    .status-timeline {
      top: clamp(0.5rem, 3vh, 1.4rem);
      flex-wrap: wrap;
      justify-content: center;
      gap: 0.5rem;
    }

    .status-timeline .timeline-chip {
      font-size: 0.78rem;
      padding: 0.35rem 0.75rem;
    }
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
