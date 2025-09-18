<script>
  import { onDestroy } from 'svelte';
  import { getDamageTypeVisual } from '$lib/systems/assetLoader.js';

  const RANDOM_OFFSETS = 120;
  const BASE_DURATION = 900;

  export let events = [];
  export let reducedMotion = false;
  export let paceMs = 1200;
  // Constant offsets (px) applied in addition to random X offset per floater
  export let baseOffsetX = 0;
  export let baseOffsetY = -10;
  // Stagger additions within a batch so items show one-by-one
  export let staggerMs = 140;
  // Map of entity id -> { x: fraction(0..1), y: fraction(0..1) } relative to the battle field
  export let anchors = {};

  let floaters = [];
  let counter = 0;
  const timeouts = new Map();
  const addTimers = new Set();

  function resolveVariant(type) {
    const t = String(type || '').toLowerCase();
    if (t === 'heal_received' || t === 'hot_tick') return 'heal';
    if (t === 'dot_tick') return 'dot';
    return 'damage';
  }

  function resolveLabel(metadata) {
    if (!metadata || typeof metadata !== 'object') return '';
    const list = Array.isArray(metadata.effects) ? metadata.effects : [];
    for (const entry of list) {
      if (!entry || typeof entry !== 'object') continue;
      if (entry.name) return String(entry.name);
      if (entry.id) return String(entry.id);
    }
    return '';
  }

  function scheduleRemoval(id, duration) {
    const timeoutMs = Math.max(BASE_DURATION, Number(duration) || BASE_DURATION) + 100;
    const handle = setTimeout(() => removeFloater(id), timeoutMs);
    timeouts.set(id, handle);
  }

  function removeFloater(id) {
    const handle = timeouts.get(id);
    if (handle) {
      clearTimeout(handle);
      timeouts.delete(id);
    }
    floaters = floaters.filter((entry) => entry.id !== id);
  }

  function pushEvents(list) {
    if (!Array.isArray(list) || list.length === 0) return;
    const duration = Math.max(BASE_DURATION, Number(paceMs) || BASE_DURATION);
    const step = Math.max(0, Math.min(Number(staggerMs) || 0, 2000));
    list.forEach((raw, i) => {
      if (!raw || typeof raw !== 'object') return;
      const handle = setTimeout(() => {
        addTimers.delete(handle);
        const amount = Math.abs(Number(raw.amount ?? 0));
        if (!Number.isFinite(amount) || amount <= 0) return;
        const variant = resolveVariant(raw.type);
        const damageType = raw.damageTypeId || raw.metadata?.damage_type_id || '';
        const { icon: Icon, color } = getDamageTypeVisual(damageType, { variant });
        const label = raw.effectLabel || resolveLabel(raw.metadata);
        const id = `${Date.now()}-${counter++}`;
        const offset = Math.random() * RANDOM_OFFSETS - RANDOM_OFFSETS / 2;
        const target = String(raw.target_id || '');
        const anchor = (anchors && target && anchors[target]) ? anchors[target] : null;
        const x = anchor && Number.isFinite(anchor.x) ? anchor.x : 0.5;
        const y = anchor && Number.isFinite(anchor.y) ? anchor.y : 0.52;
        const critical = Boolean(raw.isCritical || raw.metadata?.is_critical);
        floaters = [
          ...floaters,
          {
            id,
            Icon,
            color,
            amount,
            variant,
            label,
            offset,
            x,
            y,
            tone: variant === 'heal' || variant === 'hot' ? 'heal' : 'damage',
            type: raw.type,
            critical,
          }
        ];
        scheduleRemoval(id, duration);
      }, i * step);
      addTimers.add(handle);
    });
  }

  $: if (events && events.length) {
    pushEvents(events);
  }

  function handleAnimationEnd(entry) {
    if (!reducedMotion) {
      removeFloater(entry.id);
    }
  }

  onDestroy(() => {
    for (const handle of timeouts.values()) {
      clearTimeout(handle);
    }
    timeouts.clear();
    for (const t of addTimers) clearTimeout(t);
    addTimers.clear();
  });
</script>

<div class:reduced={reducedMotion} class="floater-host" aria-hidden="true">
  {#each floaters as entry (entry.id)}
    <div
      class={`floater ${entry.tone} ${entry.variant}`}
      style={`--accent: ${entry.color}; --offset: ${entry.offset}px; --x: ${entry.x}; --y: ${entry.y}; --floater-duration: ${Math.max(BASE_DURATION, Number(paceMs) || BASE_DURATION)}ms; --x-offset: ${Number(baseOffsetX) || 0}px; --y-offset: ${Number(baseOffsetY) || 0}px;`}
      on:animationend={() => handleAnimationEnd(entry)}
    >
      <div class="badge">
        <span class="icon" style={`background:${entry.color}`}> 
          {#if entry.Icon}
            <svelte:component this={entry.Icon} size={14} stroke-width={2} />
          {/if}
        </span>
        <span class="amount" data-variant={entry.variant}>
          {entry.variant === 'heal' || entry.variant === 'hot' ? '+' : '-'}{Math.round(entry.amount)}
          {entry.critical && entry.variant === 'damage' ? '!' : ''}
        </span>
        {#if entry.label}
          <span class="label">{entry.label}</span>
        {/if}
      </div>
    </div>
  {/each}
</div>

<style>
  .floater-host {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 3;
    overflow: hidden;
    display: block;
  }

  .floater {
    position: absolute;
    left: calc(var(--x, 0.5) * 100% + var(--offset, 0px) + var(--x-offset, 0px));
    top: calc(var(--y, 0.52) * 100% + var(--y-offset, 0px));
    transform: translate(-50%, 0);
    animation: float-up var(--floater-duration, 1200ms) cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
  }

  .floater.dot {
    filter: drop-shadow(0 0 6px rgba(0, 0, 0, 0.4));
  }

  .floater .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.6rem;
    border-radius: 999px;
    background: rgba(15, 15, 20, 0.75);
    border: 1px solid var(--accent, rgba(255, 255, 255, 0.35));
    color: white;
    font-weight: 600;
    font-size: 0.95rem;
    letter-spacing: 0.01em;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
  }

  .floater.heal .badge {
    background: rgba(30, 40, 30, 0.75);
  }

  .floater .icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.6rem;
    height: 1.6rem;
    border-radius: 999px;
    color: #101010;
  }

  .floater .amount {
    min-width: 3ch;
    text-align: right;
  }

  .floater .label {
    font-size: 0.8rem;
    opacity: 0.85;
    text-transform: capitalize;
  }

  @keyframes float-up {
    0% {
      opacity: 0;
      transform: translate(-50%, 24px) scale(0.9);
    }
    10% {
      opacity: 1;
      transform: translate(-50%, 0) scale(1);
    }
    85% {
      opacity: 1;
      transform: translate(-50%, -48px) scale(1);
    }
    100% {
      opacity: 0;
      transform: translate(-50%, -56px) scale(0.98);
    }
  }

  .floater-host.reduced .floater {
    animation: none;
    opacity: 1;
    transform: translate(-50%, 0);
  }

  .floater-host.reduced .badge {
    transition: opacity 0.25s ease;
  }
</style>
