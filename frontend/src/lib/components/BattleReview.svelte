<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import FighterPortrait from '../battle/FighterPortrait.svelte';
  import ReviewOverlay from './battle-review/ReviewOverlay.svelte';
  import RewardCard from './RewardCard.svelte';
  import CurioChoice from './CurioChoice.svelte';
  import { getElementColor, getDotImage, getDotElement } from '../systems/assetLoader.js';
  import { getBattleSummary, getBattleEvents } from '../systems/uiApi.js';
  import { Sparkles, Shield, CreditCard, Zap, Flame, Heart, Coins, TrendingUp, User, Swords, Skull, XOctagon, HeartOff } from 'lucide-svelte';

  export let runId = '';
  export let battleIndex = 0;
  export let cards = [];
  export let relics = [];
  export let party = [];
  export let foes = [];
  export let partyData = [];
  export let foeData = [];
  export let reducedMotion = false;
  // Optional: summary may be prefetched by OverlayHost to avoid flashing/loading
  export let prefetchedSummary = null;

  const dispatch = createEventDispatcher();
  let summary = { damage_by_type: {} };
  let events = [];
  let showEvents = false;
  let loadingEvents = false;
  
  // Tab system for entity-specific breakdowns
  let activeTab = 'overview';
  let availableTabs = [];
  // Track which battle summary we've loaded to refresh reactively
  let lastLoadedKey = '';
  // Derived state holders with safe defaults so template can render immediately
  let overviewTotals = {};
  let overviewGrand = 0;
  let currentTab = null;
  let entityData = null;

  const elements = ['Generic', 'Light', 'Dark', 'Wind', 'Lightning', 'Fire', 'Ice'];
  
  // Tooltip definitions for effects
  const effectTooltips = {
    'aftertaste': 'Deals a hit with random damage type (10% to 150% damage)',
    'critical_boost': '+0.5% crit rate and +5% crit damage per stack. Removed when taking damage.',
    'critboost': '+0.5% crit rate and +5% crit damage per stack. Removed when taking damage.',
    'iron_guard': '+55% DEF; damage grants all allies +10% DEF for 1 turn.',
    'phantom_ally': 'Summons a phantom copy of a random party member for one battle.',
    'arc_lightning': 'Lightning attacks have a 50% chance to chain to another random foe for 50% damage.',
    'critical_focus': 'Low HP allies gain +25% critical hit rate.',
    'elemental_spark': 'One random ally gains +5% effect hit rate until they take damage.'
  };

  // Generate element colors for bar graphs (case-insensitive; falls back to shared palette)
  function getElementBarColor(element) {
    const key = String(element || '').toLowerCase();
    const colorMap = {
      fire: '#ff6b35',
      ice: '#4fb3ff', 
      lightning: '#ffd93d',
      wind: '#7dd3c0',
      light: '#fff2b3',
      dark: '#9b59b6',
      generic: '#8e44ad'
    };
    return colorMap[key] || getElementColor(element) || '#8e44ad';
  }

  // Generate colors for different action types
  function getActionBarColor(action) {
    // Handle element-specific Aftertaste actions (e.g., "Aftertaste (Fire)")
    if (action.startsWith('Aftertaste (') && action.endsWith(')')) {
      const elementMatch = action.match(/Aftertaste \((\w+)\)/);
      if (elementMatch) {
        const element = elementMatch[1];
        // Use element-specific colors for mixed Aftertaste display
        return getElementColor(element);
      }
    }
    
    const colorMap = {
      'Normal Attack': '#ff6b35',
      'Dark Ultimate': '#9b59b6',
      'Ice Ultimate': '#4fb3ff',
      'Fire Ultimate': '#ff6b35',
      'Lightning Ultimate': '#ffd93d',
      'Wind Ultimate': '#7dd3c0',
      'Light Ultimate': '#fff2b3',
      'Aftertaste': '#e74c3c', // Fallback for legacy data
      'Wind Spread': '#7dd3c0',
      // Fallback colors for any other actions
      'Ultimate': '#8e44ad',
      'Relic Effect': '#f39c12',
      'Card Effect': '#27ae60'
    };
    return colorMap[action] || '#8e44ad';
  }

  // Prefer room-provided ids; if no bar data is available for them, fall back
  // to the ids present in the fetched summary to ensure graphs are shown.
  let partyDisplay = [];
  let foesDisplay = [];
  // Prefer full objects from room snapshot so DoTs/HoTs/buffs render in FighterPortrait
  $: partyDisplay = (partyData && partyData.length
    ? partyData
    : (party && party.length
        ? party.map(id => ({ id }))
        : (summary.party_members || []).map(id => ({ id }))
      )
  );
  $: foesDisplay = (foeData && foeData.length
    ? foeData
    : (foes && foes.length
        ? foes.map(f => (typeof f === 'object' ? { ...f } : { id: f }))
        : (summary.foes || []).map(id => ({ id }))
      )
  );

  // Shared loader with retry (used on mount and on prop changes)
  async function loadSummaryWithRetry(curBattleIndex, signal) {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    for (let attempt = 0; attempt < 10 && !(signal?.cancelled); attempt++) {
      try {
        const res = await getBattleSummary(curBattleIndex);
        if (signal?.cancelled) return;
        summary = res || { damage_by_type: {} };
        return;
      } catch (err) {
        // 404 is expected briefly while the backend writes logs
        if (err?.status !== 404) {
          console.warn('Battle summary fetch failed', err?.message || err);
          return;
        }
      }
      await sleep(attempt < 5 ? 400 : 800);
    }
  }

  onMount(async () => {
    // Require a positive battleIndex; avoid hammering 404s for index 0 or undefined
    if (!runId || battleIndex == null || battleIndex <= 0) return;
    const currentKey = `${runId}|${battleIndex}`;
    // If parent provided a prefetched summary for this battle, use it and skip fetch
    if (prefetchedSummary) {
      summary = prefetchedSummary || { damage_by_type: {} };
      lastLoadedKey = currentKey;
      return;
    }
    lastLoadedKey = currentKey;
    const signal = { cancelled: false };
    await loadSummaryWithRetry(battleIndex, signal);
    return () => { signal.cancelled = true; };
  });

  // Reactively refresh when runId or battleIndex changes (component stays mounted between battles)
  $: if (runId && battleIndex != null && battleIndex > 0) {
    const currentKey = `${runId}|${battleIndex}`;
    if (currentKey !== lastLoadedKey) {
      lastLoadedKey = currentKey;
      const signal = { cancelled: false };
      // Clear previous summary to avoid showing stale totals while loading
      summary = { damage_by_type: {} };
      // Keep the user on their current tab; data will update in-place
      // Fire and forget (errors are logged in loader)
      loadSummaryWithRetry(battleIndex, signal);
    }
  }

  // Build mapping of outgoing effects by source id so effects are grouped
  // with the character/foe that created them (not just who currently has them).
  function buildOutgoingMap() {
    const map = new Map();
    const push = (sid, bucket, eff) => {
      if (!sid) return;
      const entry = map.get(sid) || { dots: [], hots: [], buffs: [] };
      entry[bucket].push(eff);
      map.set(sid, entry);
    };
    const all = [...(partyDisplay || []), ...(foesDisplay || [])];
    for (const ent of all) {
      const dots = Array.isArray(ent.dots) ? ent.dots : [];
      const hots = Array.isArray(ent.hots) ? ent.hots : [];
      const buffs = Array.isArray(ent.active_effects) ? ent.active_effects : [];
      for (const d of dots) push(d.source, 'dots', d);
      for (const h of hots) push(h.source, 'hots', h);
      for (const b of buffs) push(b.source, 'buffs', b);
    }
    return map;
  }
  $: outgoingBySource = buildOutgoingMap();

  // Build available tabs based on available entities
  $: {
    const tabs = [{ id: 'overview', label: 'Overview', icon: Swords, type: 'overview' }];
    
    // Add party member tabs
    for (const member of partyDisplay || []) {
      if (member.id) {
        tabs.push({
          id: member.id,
          label: member.name || member.id,
          type: 'party',
          entity: member
        });
      }
    }
    
    // Add foe tabs
    for (const foe of foesDisplay || []) {
      if (foe.id) {
        const name = foe.name || foe.id;
        const label = foe.rank ? `${name} — ${foe.rank}` : name;
        tabs.push({
          id: foe.id,
          label,
          type: 'foe',
          entity: foe
        });
      }
    }
    
    availableTabs = tabs;
  }

  // Process actions - now preserves individual action types for detailed breakdown
  function processActionData(actions) {
    if (!actions) return {};
    
    // Return actions as-is to preserve detailed breakdown
    // Previously this function was combining ultimates and DoTs into "Normal Attack"
    // which was hiding the very data users want to see in "Damage by Action"
    return { ...actions };
  }

  // Get entity-specific data for a tab
  function getEntityData(entityId) {
    if (!summary) return null;

    if (entityId === 'overview') {
      const resourcesSpent = Object.values(summary.resources_spent || {}).reduce((acc, cur) => {
        for (const [type, amt] of Object.entries(cur || {})) {
          acc[type] = (acc[type] || 0) + amt;
        }
        return acc;
      }, {});
      const resourcesGained = Object.values(summary.resources_gained || {}).reduce((acc, cur) => {
        for (const [type, amt] of Object.entries(cur || {})) {
          acc[type] = (acc[type] || 0) + amt;
        }
        return acc;
      }, {});
      return {
        damage: totalDamageByType(),
        actions: processActionData(Object.values(summary.damage_by_action || {}).reduce((acc, cur) => {
          for (const [action, amt] of Object.entries(cur || {})) {
            acc[action] = (acc[action] || 0) + amt;
          }
          return acc;
        }, {})),
        criticals: Object.values(summary.critical_hits || {}).reduce((a, b) => a + b, 0),
        criticalDamage: Object.values(summary.critical_damage || {}).reduce((a, b) => a + b, 0),
        shieldAbsorbed: Object.values(summary.shield_absorbed || {}).reduce((a, b) => a + b, 0),
        dotDamage: Object.values(summary.dot_damage || {}).reduce((a, b) => a + b, 0),
        hotHealing: Object.values(summary.hot_healing || {}).reduce((a, b) => a + b, 0),
        resourcesSpent,
        resourcesGained,
        tempHpGranted: Object.values(summary.temporary_hp_granted || {}).reduce((a, b) => a + b, 0),
        kills: Object.values(summary.kills || {}).reduce((a, b) => a + b, 0),
        dotKills: Object.values(summary.dot_kills || {}).reduce((a, b) => a + b, 0),
        ultimatesUsed: Object.values(summary.ultimates_used || {}).reduce((a, b) => a + b, 0),
        ultimateFailures: Object.values(summary.ultimate_failures || {}).reduce((a, b) => a + b, 0),
        healingPrevented: Object.values(summary.healing_prevented || {}).reduce((a, b) => a + b, 0)
      };
    }

    return {
      damage: summary.damage_by_type?.[entityId] || {},
      actions: processActionData(summary.damage_by_action?.[entityId] || {}),
      criticals: summary.critical_hits?.[entityId] || 0,
      criticalDamage: summary.critical_damage?.[entityId] || 0,
      shieldAbsorbed: summary.shield_absorbed?.[entityId] || 0,
      dotDamage: summary.dot_damage?.[entityId] || 0,
      hotHealing: summary.hot_healing?.[entityId] || 0,
      resourcesSpent: summary.resources_spent?.[entityId] || {},
      resourcesGained: summary.resources_gained?.[entityId] || {},
      tempHpGranted: summary.temporary_hp_granted?.[entityId] || 0,
      kills: summary.kills?.[entityId] || 0,
      dotKills: summary.dot_kills?.[entityId] || 0,
      ultimatesUsed: summary.ultimates_used?.[entityId] || 0,
      ultimateFailures: summary.ultimate_failures?.[entityId] || 0,
      healingPrevented: summary.healing_prevented?.[entityId] || 0
    };
  }

  // Aggregate helpers for overview
  function totalDamageByType() {
    const out = {};
    const by = summary?.damage_by_type || {};
    for (const types of Object.values(by)) {
      for (const [elem, amt] of Object.entries(types || {})) {
        out[elem] = (out[elem] || 0) + (amt || 0);
      }
    }
    return out;
  }

  // Derived overview totals to avoid recomputation and ensure immediate reactivity
  // Explicitly depend on `summary` so Svelte recomputes when it changes
  $: { const _dep = summary; overviewTotals = totalDamageByType(); }
  $: overviewGrand = Object.values(overviewTotals).reduce((a, b) => a + b, 0);

  function primaryElement(id) {
    const totals = summary.damage_by_type?.[id] || {};
    const entries = Object.entries(totals);
    if (entries.length === 0) return 'Generic';
    return entries.sort((a, b) => b[1] - a[1])[0][0];
  }

  function handleSelect(e) {
    dispatch('select', e.detail);
  }

  // Derived helpers for labels and totals
  function fmt(n) {
    try { return Number(n).toLocaleString(); } catch { return String(n ?? 0); }
  }
  // Old bargraph helpers removed.

  async function toggleEvents() {
    showEvents = !showEvents;
    // Allow battleIndex 0
    if (showEvents && events.length === 0 && runId && battleIndex != null) {
      loadingEvents = true;
      try {
        const data = await getBattleEvents(battleIndex);
        events = Array.isArray(data) ? data : [];
      } catch (e) {
        // swallow; optional view
      } finally {
        loadingEvents = false;
      }
    }
  }

  // If no data for provided ids but summary has data for others, switch display ids
  $: {
    const hasAnySummary = (list) => Array.isArray(list) && list.some((e) => {
      const id = (e && typeof e === 'object') ? (e.id || '') : e;
      const totals = summary?.damage_by_type?.[id] || {};
      return Object.keys(totals).length > 0;
    });
    const summaryParty = (summary?.party_members || []).map(id => ({ id, element: 'Generic' }));
    const summaryFoes = (summary?.foes || []).map(id => ({ id, element: 'Generic' }));
    if (!hasAnySummary(partyDisplay) && hasAnySummary(summaryParty)) partyDisplay = summaryParty;
    if (!hasAnySummary(foesDisplay) && hasAnySummary(summaryFoes)) foesDisplay = summaryFoes;
  }

  // Calculate tab and entity data reactively
  $: currentTab = availableTabs.find(t => t.id === activeTab);
  // Explicit dependency on `summary` so the right-side stats panel updates on load
  $: { const _dep2 = summary; entityData = getEntityData(activeTab); }

  // Build a safe fighter object for portraits in tabs (ensures id/element/hp exist)
  function toDisplayFighter(entity) {
    const eid = (entity && typeof entity === 'object') ? (entity.id || '') : (entity || '');
    const id = eid || '';
    const element = (entity && typeof entity === 'object' && (entity.element)) || primaryElement(id);
    const hp = (entity && typeof entity === 'object' && Number.isFinite(entity.hp)) ? entity.hp : 1;
    const max_hp = (entity && typeof entity === 'object' && Number.isFinite(entity.max_hp) && entity.max_hp > 0) ? entity.max_hp : 1;
    const dots = (entity && typeof entity === 'object' && Array.isArray(entity.dots)) ? entity.dots : [];
    const hots = (entity && typeof entity === 'object' && Array.isArray(entity.hots)) ? entity.hots : [];
    const active_effects = (entity && typeof entity === 'object' && Array.isArray(entity.active_effects)) ? entity.active_effects : [];
    const shields = (entity && typeof entity === 'object' && Number.isFinite(entity.shields)) ? entity.shields : 0;
    return { ...(typeof entity === 'object' ? entity : {}), id, element, hp, max_hp, dots, hots, active_effects, shields };
  }
</script>

<style>
  .layout {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
    /* Default portrait size within review */
    --portrait-size: 6rem;
  }
  .layout.review {
    width: 100%;
    max-width: 100%;
    overflow-x: hidden;
    /* Use a single-column flow for the review so content spans full width */
    grid-template-columns: 1fr;
  }
  .side {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }
  .combatant {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    width: 100%;
  }
  .row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    justify-content: center;
  }
  .row.player { flex-direction: row; }
  .row.foe { flex-direction: row-reverse; }
  .portrait-col { display: flex; flex-direction: column; align-items: center; }
  .name-chip {
    width: var(--portrait-size);
    margin: 0 0 0.25rem 0;
    font-size: 0.78rem;
    color: #eee;
    text-align: center;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    background: rgba(0,0,0,0.35);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 2px 4px;
  }
  .effects-block { display: flex; flex-direction: column; align-items: stretch; min-width: 8rem; }
  .rewards {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }
  .effects-out { margin-top: 0.35rem; max-width: 320px; }
  .effects-section { margin-top: 0.25rem; }
  .effects-title { font-size: 0.72rem; color: #aaa; margin-bottom: 0.1rem; text-align: center; }
  .effect-cap { display: grid; grid-template-columns: 30px 1fr; gap: 0.4rem; align-items: center; margin: 0.15rem 0; padding: 0.25rem 0; }
  .effect-cap .dot-mini { width: 26px; height: 26px; border-radius: 4px; border: 2px solid #555; }
  .cap-lines { font-size: 0.7rem; line-height: 1.2; color: #ddd; }
  .cap-name { font-weight: 600; color: #eee; }
  .cap-stats { opacity: 0.9; }
  /* Hide in-portrait HP and Buff bars only inside the review UI */
  .review :global(.portrait-wrap .hp-bar) { display: none; }
  .review :global(.portrait-wrap .buff-bar) { display: none; }
  .subtle { opacity: 0.85; }
  .events {
    margin-top: 0.75rem;
    max-height: 240px;
    overflow-y: auto;
    overflow-x: auto;
    max-width: 100%;
    box-sizing: border-box;
    border: var(--glass-border);
    background: rgba(0,0,0,0.4);
    padding: 0.5rem;
  }
  .event-row { font-size: 0.72rem; color: #ddd; margin: 0.15rem 0; white-space: normal; overflow-wrap: anywhere; word-break: break-word; }
  .header { font-size: 0.85rem; color: #fff; margin-bottom: 0.25rem; display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; width: 100%; box-sizing: border-box; }
  .spacer { flex: 1; }
  .mini-btn { border: 1px solid #888; background: #111; color: #fff; font-size: 0.7rem; padding: 0.2rem 0.4rem; cursor: pointer; }
  .reward-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.75rem;
    max-width: 100%;
    box-sizing: border-box;
  }
  .effects-summary {
    margin-top: 0.5rem;
    width: 100%;
    box-sizing: border-box;
  }
  .effects-header {
    font-size: 0.85rem;
    color: #fff;
    margin-bottom: 0.5rem;
    text-align: center;
    font-weight: 600;
  }
  .effects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .battle-review-tabs {
    display: grid;
    /* Span full popup width and allocate more space to content than stats */
    grid-column: 1 / -1;
    grid-template-columns: auto 2fr 1fr;
    gap: 1rem;
    background: rgba(0,0,0,0.4);
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }

  .icon-column {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: 70vh;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 0.5rem;
    /* Add subtle scrollbar styling */
    scrollbar-width: thin;
    scrollbar-color: rgba(255,255,255,0.3) rgba(0,0,0,0.1);
  }
  
  .icon-column::-webkit-scrollbar {
    width: 6px;
  }
  
  .icon-column::-webkit-scrollbar-track {
    background: rgba(0,0,0,0.1);
    border-radius: 3px;
  }
  
  .icon-column::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.3);
    border-radius: 3px;
  }
  
  .icon-column::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.5);
  }

  .icon-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 4.5rem;
    height: 4.5rem;
    background: rgba(255,255,255,0.1);
    color: #ccc;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    flex-shrink: 0;
  }

  .icon-btn:hover {
    background: rgba(255,255,255,0.2);
    color: #fff;
  }

  .icon-btn.active {
    background: rgba(120,180,255,0.3);
    color: #fff;
    border: 1px solid rgba(120,180,255,0.5);
  }

  .content-area {
    min-width: 0;
  }

  .stats-panel {
    min-width: 220px;
    display: flex;
    flex-direction: column;
  }
  .effects-column {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  .effects-column-title {
    font-size: 0.75rem;
    color: #aaa;
    margin-bottom: 0.25rem;
    text-align: center;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .effect-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.25rem 0.5rem;
    background: rgba(255,255,255,0.05);
    border-radius: 3px;
    border: 1px solid rgba(255,255,255,0.1);
  }
  .effect-name {
    font-size: 0.72rem;
    color: #ddd;
    font-weight: 500;
  }
  .effect-count {
    font-size: 0.7rem;
    color: #bbb;
    font-weight: 600;
    background: rgba(255,255,255,0.1);
    padding: 0.1rem 0.3rem;
    border-radius: 2px;
  }
  .new-badge {
    font-size: 0.6rem;
    color: #4ade80;
    background: rgba(74, 222, 128, 0.2);
    padding: 0.1rem 0.25rem;
    border-radius: 2px;
    margin-left: 0.25rem;
    border: 1px solid rgba(74, 222, 128, 0.3);
  }
  .new-feature-badge {
    font-size: 0.65rem;
    color: #fbbf24;
    background: rgba(251, 191, 36, 0.2);
    padding: 0.15rem 0.35rem;
    border-radius: 3px;
    margin-left: 0.5rem;
    border: 1px solid rgba(251, 191, 36, 0.4);
    font-weight: 600;
    text-shadow: 0 0 4px rgba(251, 191, 36, 0.3);
  }
  .detail-section {
    margin-top: 0.75rem;
    border-top: 1px solid rgba(255,255,255,0.1);
    padding-top: 0.5rem;
  }
  .detail-title {
    font-size: 0.75rem;
    color: #aaa;
    margin-bottom: 0.35rem;
    text-align: center;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.25rem;
  }
  .detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.2rem 0.4rem;
    background: rgba(255,255,255,0.03);
    border-radius: 2px;
    border: 1px solid rgba(255,255,255,0.05);
  }
  .detail-name {
    font-size: 0.7rem;
    color: #ccc;
    font-weight: 500;
  }
  .detail-stats {
    font-size: 0.65rem;
    color: #999;
    font-weight: 600;
  }
  
  /* Layout for icon navigation and stats panel */

  
  /* Entity breakdown styles */
  .entity-breakdown {
    padding: 1rem;
    background: rgba(0,0,0,0.2);
    border-radius: 6px;
  }
  
  .entity-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
  }
  
  .entity-header h3 {
    margin: 0;
    color: #fff;
    font-size: 1.2rem;
  }
  
  .entity-section {
    margin-bottom: 1.5rem;
  }
  
  .entity-section h4 {
    margin: 0 0 0.75rem 0;
    color: #fff;
    font-size: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .damage-breakdown {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.5rem;
  }
  
  .damage-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem;
    background: rgba(255,255,255,0.05);
    border-radius: 4px;
  }
  
  .damage-element {
    color: #ccc;
    font-size: 0.8rem;
  }
  
  .damage-amount {
    color: #fff;
    font-weight: 600;
    font-size: 0.8rem;
  }
  
  .entity-stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.75rem;
    width: 100%;
  }
  
  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(255,255,255,0.05);
    border-radius: 4px;
    font-size: 0.8rem;
  }
  
  .stat-value {
    color: #fff;
    font-weight: 600;
    margin-left: auto;
  }
  
  .stat-detail {
    color: #ccc;
    font-size: 0.7rem;
  }
  
  .resource-breakdown {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
    margin-left: auto;
  }
  
  .resource-item {
    background: rgba(255,255,255,0.1);
    padding: 0.2rem 0.4rem;
    border-radius: 2px;
    font-size: 0.7rem;
    color: #fff;
  }
  
  /* Enhanced icons in titles */
  .effects-header,
  .effects-column-title,
  .detail-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  /* Damage bar graph styles */
  .damage-bar-container {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-top: 0.5rem;
  }
  
  .damage-bar {
    position: relative;
    height: 16px;
    background: rgba(255,255,255,0.1);
    border-radius: 2px;
    overflow: hidden;
  }
  
  .damage-bar-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s ease;
  }
  
  .damage-bar-label {
    position: absolute;
    left: 4px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 0.7rem;
    font-weight: 600;
    color: #fff;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    z-index: 1;
  }

  .damage-bar-amount {
    position: absolute;
    right: 4px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 0.7rem;
    font-weight: 600;
    color: #fff;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    z-index: 1;
  }

  /* Tooltip styles */
  .tooltip-trigger {
    position: relative;
    cursor: help;
  }
  
  .tooltip-trigger:hover .tooltip {
    opacity: 1;
    visibility: visible;
  }
  
  .tooltip {
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0,0,0,0.9);
    color: #fff;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    white-space: nowrap;
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.2s ease;
    z-index: 1000;
    border: 1px solid rgba(255,255,255,0.2);
    max-width: 300px;
    white-space: normal;
    text-align: center;
  }

  .tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 4px solid transparent;
    border-top-color: rgba(0,0,0,0.9);
  }
</style>

<div class="layout review">
  
  <div class="side rewards">
    {#if cards.length}
      <div class="reward-grid">
        {#each cards.slice(0,3) as card, i (card.id)}
          <RewardCard entry={card} type="card" on:select={handleSelect} />
        {/each}
      </div>
    {/if}
    {#if relics.length}
      <div class="reward-grid">
        {#each relics.slice(0,3) as relic, i (relic.id)}
          <CurioChoice entry={relic} on:select={handleSelect} />
        {/each}
      </div>
    {/if}
  </div>
  

  <!-- Top-level summary and raw events toggle -->
  <div class="side" style="grid-column: 1 / -1;">
    <div class="header">
      <div>Result: {summary?.result || '—'}</div>
      <div>Duration: {summary?.duration_seconds ? Math.round(summary.duration_seconds) + 's' : '—'}</div>
      <div>Events: {fmt(summary?.event_count || (events?.length || 0))}</div>
      {#if summary?.relic_effects && Object.keys(summary.relic_effects).length > 0}
        <div>Relic Effects: {Object.values(summary.relic_effects).reduce((a, b) => a + b, 0)} <span class="new-badge">NEW</span></div>
      {/if}
      {#if summary?.card_effects && Object.keys(summary.card_effects).length > 0}
        <div>Card Effects: {Object.values(summary.card_effects).reduce((a, b) => a + b, 0)} <span class="new-badge">NEW</span></div>
      {/if}
      {#if summary?.critical_hits && Object.keys(summary.critical_hits).length > 0}
        <div>Criticals: {Object.values(summary.critical_hits).reduce((a, b) => a + b, 0)}</div>
      {/if}
      {#if summary?.shield_absorbed && Object.keys(summary.shield_absorbed).length > 0}
        <div>Shields: {Object.values(summary.shield_absorbed).reduce((a, b) => a + b, 0)} absorbed</div>
      {/if}
      <span class="spacer"></span>
      <button class="mini-btn" on:click={toggleEvents}>{showEvents ? 'Hide' : 'Show'} Event Log</button>
    </div>
    {#if showEvents}
      <div class="events">
        {#if loadingEvents}
          <div class="event-row subtle">Loading events…</div>
        {:else if events.length === 0}
          <div class="event-row subtle">No events available.</div>
        {:else}
          {#each events.slice(-200) as ev}
            <div class="event-row">[{ev.event_type}] {ev.attacker_id || '—'} → {ev.target_id || '—'}{ev.amount != null ? ` (${ev.amount})` : ''}{ev.damage_type ? ` [${ev.damage_type}]` : ''}{ev.source_type ? ` {${ev.source_type}}` : ''}</div>
          {/each}
        {/if}
      </div>
    {/if}
  </div>
    
  <!-- Icon-column Battle Review Interface -->
    <div class="battle-review-tabs">
      <div class="icon-column">
        {#each availableTabs as tab}
          <button
            class="icon-btn"
            class:active={activeTab === tab.id}
            on:click={() => activeTab = tab.id}
            aria-label={tab.label}
          >
            {#if tab.icon}
              <svelte:component this={tab.icon} size={20} />
            {:else if tab.entity}
              {@const _tabFighter = toDisplayFighter(tab.entity)}
              <div style="--portrait-size: 4rem;">
                <FighterPortrait fighter={_tabFighter} {reducedMotion} />
              </div>
            {:else}
              <User size={20} />
            {/if}
          </button>
        {/each}
      </div>

      <div class="content-area">
        {#if activeTab === 'overview'}
          <div class="effects-summary">
            {#if Object.keys(overviewTotals).length > 0}
              <div class="entity-section">
                <h4>
                  <Swords size={16} />
                  Total Damage Output
                </h4>
                <div class="damage-bar-container">
                  {#each Object.entries(overviewTotals).sort((a, b) => b[1] - a[1]) as [element, damage]}
                    {@const percentage = overviewGrand > 0 ? (damage / overviewGrand * 100) : 0}
                    <div class="damage-bar">
                      <div class="damage-bar-fill" style="width: {percentage}%; background-color: {getElementBarColor(element)};"></div>
                      <div class="damage-bar-label">{element}</div>
                      <div class="damage-bar-amount">{fmt(damage)}</div>
                    </div>
                  {/each}
  </div>
</div>

  <ReviewOverlay {summary} {cards} {relics} />
            {/if}

            <!-- Party vs Foe Damage Comparison -->
            {#if summary?.damage_by_type && Object.keys(summary.damage_by_type).length > 0}
              {@const partyDamage = Object.entries(summary.damage_by_type || {})
                .filter(([id]) => partyDisplay.some(p => p.id === id))
                .reduce((acc, [id, damages]) => {
                  Object.entries(damages || {}).forEach(([elem, dmg]) => {
                    acc[elem] = (acc[elem] || 0) + (dmg || 0);
                  });
                  return acc;
                }, {})}
              {@const foeDamage = Object.entries(summary.damage_by_type || {})
                .filter(([id]) => foesDisplay.some(f => f.id === id))
                .reduce((acc, [id, damages]) => {
                  Object.entries(damages || {}).forEach(([elem, dmg]) => {
                    acc[elem] = (acc[elem] || 0) + (dmg || 0);
                  });
                  return acc;
                }, {})}
              {@const partyTotal = Object.values(partyDamage).reduce((a, b) => a + b, 0)}
              {@const foeTotal = Object.values(foeDamage).reduce((a, b) => a + b, 0)}
              {@const combatTotal = partyTotal + foeTotal}
              
              <div class="entity-section">
                <h4>
                  <User size={16} />
                  Party vs Foe Damage Comparison
                </h4>
                <div class="damage-bar-container">
                  {#if partyTotal > 0}
                    {@const partyPercentage = combatTotal > 0 ? (partyTotal / combatTotal * 100) : 0}
                    <div class="damage-bar">
                      <div class="damage-bar-fill" style="width: {partyPercentage}%; background-color: #4ade80;"></div>
                      <div class="damage-bar-label">Player Party</div>
                      <div class="damage-bar-amount">{fmt(partyTotal)}</div>
                    </div>
                  {/if}
                  {#if foeTotal > 0}
                    {@const foePercentage = combatTotal > 0 ? (foeTotal / combatTotal * 100) : 0}
                    <div class="damage-bar">
                      <div class="damage-bar-fill" style="width: {foePercentage}%; background-color: #ef4444;"></div>
                      <div class="damage-bar-label">Foe Party</div>
                      <div class="damage-bar-amount">{fmt(foeTotal)}</div>
                    </div>
                  {/if}
                </div>
              </div>

              <!-- Action Type Breakdown by Party -->
              {#if summary?.damage_by_action && Object.keys(summary.damage_by_action).length > 0}
                {@const allActionsByEntity = summary.damage_by_action || {}}
                {@const partyActions = Object.entries(allActionsByEntity)
                  .filter(([id]) => (summary.party_members || []).includes(id))
                  .reduce((acc, [id, actions]) => {
                    Object.entries(actions || {}).forEach(([action, dmg]) => {
                      acc[action] = (acc[action] || 0) + (dmg || 0);
                    });
                    return acc;
                  }, {})}
                {@const foeActions = Object.entries(allActionsByEntity)
                  .filter(([id]) => (summary.foes || []).includes(id))
                  .reduce((acc, [id, actions]) => {
                    Object.entries(actions || {}).forEach(([action, dmg]) => {
                      acc[action] = (acc[action] || 0) + (dmg || 0);
                    });
                    return acc;
                  }, {})}
                
                <div class="entity-section">
                  <h4>
                    <Swords size={16} />
                    Action Type Comparison
                  </h4>
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div>
                      <div style="font-size: 0.8rem; color: #4ade80; margin-bottom: 0.5rem; font-weight: 600;">Player Party Actions</div>
                      <div class="damage-breakdown">
                        {#each Object.entries(partyActions).sort((a, b) => b[1] - a[1]) as [action, amount]}
                          <div class="damage-item">
                            <span class="damage-element">{action}</span>
                            <span class="damage-amount">{fmt(amount)}</span>
                          </div>
                        {/each}
                      </div>
                    </div>
                    <div>
                      <div style="font-size: 0.8rem; color: #ef4444; margin-bottom: 0.5rem; font-weight: 600;">Foe Party Actions</div>
                      <div class="damage-breakdown">
                        {#each Object.entries(foeActions).sort((a, b) => b[1] - a[1]) as [action, amount]}
                          <div class="damage-item">
                            <span class="damage-element">{action}</span>
                            <span class="damage-amount">{fmt(amount)}</span>
                          </div>
                        {/each}
                      </div>
                    </div>
                  </div>
                </div>
              {/if}
            {/if}

            <div class="effects-header">
              <Sparkles size={20} />
              Full Overview <span class="new-feature-badge">NEW FEATURE</span>
            </div>
            <div class="effects-grid">
              {#if summary?.relic_effects && Object.keys(summary.relic_effects).length > 0}
                <div class="effects-column">
                  <div class="effects-column-title">
                    <Shield size={16} />
                    Relic Effects
                  </div>
                  {#each Object.entries(summary.relic_effects).sort((a, b) => b[1] - a[1]) as [relicName, count]}
                    <div class="effect-item tooltip-trigger">
                      <span class="effect-name">{relicName}</span>
                      <span class="effect-count">×{count}</span>
                      <div class="tooltip">
                        Relic effect triggered {count} time{count !== 1 ? 's' : ''}
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
              {#if summary?.card_effects && Object.keys(summary.card_effects).length > 0}
                <div class="effects-column">
                  <div class="effects-column-title">
                    <CreditCard size={16} />
                    Card Effects
                  </div>
                  {#each Object.entries(summary.card_effects).sort((a, b) => b[1] - a[1]) as [cardName, count]}
                    <div class="effect-item tooltip-trigger">
                      <span class="effect-name">{cardName}</span>
                      <span class="effect-count">×{count}</span>
                      <div class="tooltip">
                        {effectTooltips[cardName] || `Card effect triggered ${count} time${count !== 1 ? 's' : ''}`}
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          </div>

          <!-- Additional detailed tracking information -->
          {#if summary?.critical_hits && Object.keys(summary.critical_hits).length > 0}
            <div class="detail-section">
              <div class="detail-title">
                <Zap size={16} />
                Critical Hits Analysis
              </div>
              <div class="detail-grid">
                {#each Object.entries(summary.critical_hits).sort((a, b) => b[1] - a[1]) as [entity, crits]}
                  <div class="detail-item">
                    <span class="detail-name">{entity}</span>
                    <span class="detail-stats">
                      {crits} crits
                      {#if summary?.critical_damage?.[entity]}
                        ({fmt(summary.critical_damage[entity])} dmg)
                      {/if}
                    </span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if summary?.shield_absorbed && Object.keys(summary.shield_absorbed).length > 0}
            <div class="detail-section">
              <div class="detail-title">
                <Shield size={16} />
                Shield Protection
              </div>
              <div class="detail-grid">
                {#each Object.entries(summary.shield_absorbed).sort((a, b) => b[1] - a[1]) as [entity, absorbed]}
                  <div class="detail-item">
                    <span class="detail-name">{entity}</span>
                    <span class="detail-stats">{fmt(absorbed)} absorbed</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if summary?.dot_damage && Object.keys(summary.dot_damage).length > 0}
            <div class="detail-section">
              <div class="detail-title">
                <Flame size={16} />
                DoT Damage
              </div>
              <div class="detail-grid">
                {#each Object.entries(summary.dot_damage).sort((a, b) => b[1] - a[1]) as [entity, damage]}
                  <div class="detail-item">
                    <span class="detail-name">{entity}</span>
                    <span class="detail-stats">{fmt(damage)} DoT dmg</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if summary?.hot_healing && Object.keys(summary.hot_healing).length > 0}
            <div class="detail-section">
              <div class="detail-title">
                <Heart size={16} />
                HoT Healing
              </div>
              <div class="detail-grid">
                {#each Object.entries(summary.hot_healing).sort((a, b) => b[1] - a[1]) as [entity, healing]}
                  <div class="detail-item">
                    <span class="detail-name">{entity}</span>
                    <span class="detail-stats">{fmt(healing)} HoT heal</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if summary?.kills && Object.keys(summary.kills).length > 0}
            <div class="detail-section">
              <div class="detail-title">
                <Skull size={16} />
                Kills
              </div>
              <div class="detail-grid">
                {#each Object.entries(summary.kills).sort((a, b) => b[1] - a[1]) as [entity, count]}
                  <div class="detail-item">
                    <span class="detail-name">{entity}</span>
                    <span class="detail-stats">{fmt(count)} kills</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if summary?.dot_kills && Object.keys(summary.dot_kills).length > 0}
            <div class="detail-section">
              <div class="detail-title">
                <Flame size={16} />
                DoT Kills
              </div>
              <div class="detail-grid">
                {#each Object.entries(summary.dot_kills).sort((a, b) => b[1] - a[1]) as [entity, count]}
                  <div class="detail-item">
                    <span class="detail-name">{entity}</span>
                    <span class="detail-stats">{fmt(count)} DoT kills</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if summary?.ultimates_used && Object.keys(summary.ultimates_used).length > 0}
            <div class="detail-section">
              <div class="detail-title">
                <Zap size={16} />
                Ultimates Used
              </div>
              <div class="detail-grid">
                {#each Object.entries(summary.ultimates_used).sort((a, b) => b[1] - a[1]) as [entity, count]}
                  <div class="detail-item">
                    <span class="detail-name">{entity}</span>
                    <span class="detail-stats">{fmt(count)} used</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if summary?.ultimate_failures && Object.keys(summary.ultimate_failures).length > 0}
            <div class="detail-section">
              <div class="detail-title">
                <XOctagon size={16} />
                Ultimate Failures
              </div>
              <div class="detail-grid">
                {#each Object.entries(summary.ultimate_failures).sort((a, b) => b[1] - a[1]) as [entity, count]}
                  <div class="detail-item">
                    <span class="detail-name">{entity}</span>
                    <span class="detail-stats">{fmt(count)} failed</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if summary?.healing_prevented && Object.keys(summary.healing_prevented).length > 0}
            <div class="detail-section">
              <div class="detail-title">
                <HeartOff size={16} />
                Healing Prevented
              </div>
              <div class="detail-grid">
                {#each Object.entries(summary.healing_prevented).sort((a, b) => b[1] - a[1]) as [entity, amount]}
                  <div class="detail-item">
                    <span class="detail-name">{entity}</span>
                    <span class="detail-stats">{fmt(amount)} prevented</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if (summary?.resources_spent && Object.keys(summary.resources_spent).length > 0) || (summary?.resources_gained && Object.keys(summary.resources_gained).length > 0)}
            <div class="detail-section">
              <div class="detail-title">
                <Coins size={16} />
                Resource Usage
              </div>
              <div class="detail-grid">
                {#each Array.from(new Set([...Object.keys(summary.resources_spent || {}), ...Object.keys(summary.resources_gained || {})])) as entity}
                  {@const spent = summary.resources_spent?.[entity] || {}}
                  {@const gained = summary.resources_gained?.[entity] || {}}
                  <div class="detail-item">
                    <span class="detail-name">{entity}</span>
                    <span class="detail-stats">
                      {#each Array.from(new Set([...Object.keys(spent), ...Object.keys(gained)])) as type}
                        {type}: {fmt(spent[type] || 0)} spent / {fmt(gained[type] || 0)} gained
                      {/each}
                    </span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if summary?.temporary_hp_granted && Object.keys(summary.temporary_hp_granted).length > 0}
            <div class="detail-section">
              <div class="detail-title">
                <TrendingUp size={16} />
                Temporary HP
              </div>
              <div class="detail-grid">
                {#each Object.entries(summary.temporary_hp_granted).sort((a, b) => b[1] - a[1]) as [entity, tempHp]}
                  <div class="detail-item">
                    <span class="detail-name">{entity}</span>
                    <span class="detail-stats">{fmt(tempHp)} temp HP</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if summary?.effect_applications && Object.keys(summary.effect_applications).length > 0}
            <div class="detail-section">
              <div class="detail-title">
                <Sparkles size={16} />
                Effect Applications
              </div>
              <div class="detail-grid">
                {#each Object.entries(summary.effect_applications).sort((a, b) => b[1] - a[1]).slice(0, 8) as [effect, count]}
                  <div class="detail-item tooltip-trigger">
                    <span class="detail-name">{effect}</span>
                    <span class="detail-stats">×{count}</span>
                    <div class="tooltip">
                      {effectTooltips[effect] || `Effect applied ${count} time${count !== 1 ? 's' : ''}`}
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        {:else if entityData && currentTab}
          <div class="entity-breakdown">
            <div class="entity-header">
              {#if currentTab.entity}
                {@const _fighter = toDisplayFighter(currentTab.entity)}
                <div style="--portrait-size: 7rem;">
                  <FighterPortrait fighter={_fighter} {reducedMotion} />
                </div>
              {/if}
              <h3>{currentTab.label} Breakdown</h3>
            </div>

            {#if Object.keys(entityData.damage).length > 0}
              <div class="entity-section">
                <h4>Damage Output by Source</h4>
                <div class="damage-bar-container">
                  {#each Object.entries(entityData.damage).sort((a, b) => b[1] - a[1]) as [element, damage]}
                    {@const totalDamage = Object.values(entityData.damage).reduce((a, b) => a + b, 0)}
                    {@const percentage = totalDamage > 0 ? (damage / totalDamage * 100) : 0}
                    <div class="damage-bar">
                      <div class="damage-bar-fill" style="width: {percentage}%; background-color: {getElementBarColor(element)};"></div>
                      <div class="damage-bar-label">{element}</div>
                      <div class="damage-bar-amount">{fmt(damage)}</div>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            {#if Object.keys(entityData.actions).length > 0}
              <div class="entity-section">
                <h4>
                  <Swords size={16} />
                  Damage by Action
                </h4>
                <div class="damage-breakdown">
                  {#each Object.entries(entityData.actions).sort((a, b) => b[1] - a[1]) as [action, amount]}
                    <div class="damage-item">
                      <span class="damage-element">{action}</span>
                      <span class="damage-amount">{fmt(amount)}</span>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        {/if}
      </div>

      <div class="stats-panel">
        {#if entityData}
          <div class="entity-stats-grid">
            <!-- Always show critical hits stats -->
            <div class="stat-item">
              <Zap size={16} />
              <span>Critical Hits</span>
              <span class="stat-value">{entityData.criticals || 0}</span>
              {#if entityData.criticalDamage > 0}
                <span class="stat-detail">({fmt(entityData.criticalDamage)} dmg)</span>
              {/if}
            </div>

            <!-- Kills and related metrics -->
            <div class="stat-item">
              <Skull size={16} />
              <span>Kills</span>
              <span class="stat-value">{entityData.kills || 0}</span>
            </div>

            <div class="stat-item">
              <Flame size={16} />
              <span>DoT Kills</span>
              <span class="stat-value">{entityData.dotKills || 0}</span>
            </div>

            <div class="stat-item">
              <Zap size={16} />
              <span>Ultimates Used</span>
              <span class="stat-value">{entityData.ultimatesUsed || 0}</span>
            </div>

            <div class="stat-item">
              <XOctagon size={16} />
              <span>Ultimate Failures</span>
              <span class="stat-value">{entityData.ultimateFailures || 0}</span>
            </div>

            <!-- Always show shield stats if there's any damage data -->
            {#if Object.keys(entityData.damage || {}).length > 0}
              <div class="stat-item">
                <Shield size={16} />
                <span>Shield Absorbed</span>
                <span class="stat-value">{fmt(entityData.shieldAbsorbed || 0)}</span>
              </div>
            {/if}

            <!-- Always show DoT damage stats if there's any damage data -->
            {#if Object.keys(entityData.damage || {}).length > 0}
              <div class="stat-item">
                <Flame size={16} />
                <span>DoT Damage</span>
                <span class="stat-value">{fmt(entityData.dotDamage || 0)}</span>
              </div>
            {/if}

            <!-- Always show HoT healing stats if there's any damage data -->
            {#if Object.keys(entityData.damage || {}).length > 0}
              <div class="stat-item">
                <Heart size={16} />
                <span>HoT Healing</span>
                <span class="stat-value">{fmt(entityData.hotHealing || 0)}</span>
              </div>
            {/if}

            {#if Object.keys(entityData.damage || {}).length > 0}
              <div class="stat-item">
                <HeartOff size={16} />
                <span>Healing Prevented</span>
                <span class="stat-value">{fmt(entityData.healingPrevented || 0)}</span>
              </div>
            {/if}

            <!-- Always show temp HP stats if there's any damage data -->
            {#if Object.keys(entityData.damage || {}).length > 0}
              <div class="stat-item">
                <TrendingUp size={16} />
                <span>Temp HP Granted</span>
                <span class="stat-value">{fmt(entityData.tempHpGranted || 0)}</span>
              </div>
            {/if}

            <!-- Show resources if any exist -->
            {#if Object.keys(entityData.resourcesSpent || {}).length > 0 || Object.keys(entityData.resourcesGained || {}).length > 0}
              <div class="stat-item">
                <Coins size={16} />
                <span>Resources</span>
                <div class="resource-breakdown">
                  {#each Array.from(new Set([...Object.keys(entityData.resourcesSpent || {}), ...Object.keys(entityData.resourcesGained || {})])) as type}
                    <span class="resource-item">{type}: {fmt(entityData.resourcesSpent[type] || 0)} spent / {fmt(entityData.resourcesGained[type] || 0)} gained</span>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    </div>
</div>
