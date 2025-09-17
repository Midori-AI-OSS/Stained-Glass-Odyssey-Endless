<script>
  import { getDamageTypeColor, getElementColor } from '$lib/systems/assetLoader.js';

  export let activeId = null;
  export let activeTargetId = null;
  export let anchors = {};
  export let combatants = [];
  export let events = [];
  export let reducedMotion = false;

  const markerId = `target-arrow-${Math.random().toString(36).slice(2, 8)}`;
  const CANVAS_SIZE = 1000;

  let combatantById = new Map();
  $: combatantById = new Map(
    (combatants || [])
      .filter(entry => entry && entry.id !== undefined && entry.id !== null)
      .map(entry => [String(entry.id), entry])
  );

  function normalizeId(value) {
    if (value === undefined || value === null) return '';
    try {
      return String(value);
    } catch {
      return '';
    }
  }

  function clampCoord(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return 0;
    return Math.max(0, Math.min(1, number));
  }

  function toPoint(anchor) {
    if (!anchor || typeof anchor !== 'object') return null;
    return {
      x: clampCoord(anchor.x),
      y: clampCoord(anchor.y),
    };
  }

  function toCanvas(point) {
    if (!point) return null;
    return {
      x: point.x * CANVAS_SIZE,
      y: point.y * CANVAS_SIZE,
    };
  }

  function findCombatant(id) {
    const key = normalizeId(id);
    if (!key) return null;
    return combatantById.get(key) || null;
  }

  function resolveElementColor(fighter) {
    if (!fighter) return '#f6d365';
    const element =
      fighter.element ||
      fighter.damage_type ||
      (Array.isArray(fighter.damage_types) && fighter.damage_types[0]) ||
      null;
    return getElementColor(element || 'generic');
  }

  function resolveVariant(type) {
    const t = String(type || '').toLowerCase();
    if (t === 'heal_received') return 'heal';
    if (t === 'hot_tick') return 'hot';
    if (t === 'dot_tick') return 'dot';
    return 'damage';
  }

  function findColorSource() {
    if (!Array.isArray(events)) return null;
    const attackerKey = normalizeId(activeId);
    const targetKey = normalizeId(activeTargetId);
    for (let i = events.length - 1; i >= 0; i -= 1) {
      const evt = events[i];
      if (!evt || typeof evt !== 'object') continue;
      const source = normalizeId(evt.source_id);
      const target = normalizeId(evt.target_id);
      if (attackerKey && source === attackerKey) return evt;
      if (targetKey && target === targetKey) return evt;
    }
    return null;
  }

  $: attackerKey = normalizeId(activeId);
  $: targetKey = normalizeId(activeTargetId);
  $: attackerAnchor = attackerKey && anchors ? anchors[attackerKey] : null;
  $: targetAnchor = targetKey && anchors ? anchors[targetKey] : null;
  $: attackerPoint = toPoint(attackerAnchor);
  $: targetPoint = toPoint(targetAnchor);
  $: attackerCanvas = toCanvas(attackerPoint);
  $: targetCanvas = toCanvas(targetPoint);

  $: arrowEvent = findColorSource();
  $: arrowColor = (() => {
    if (arrowEvent) {
      const damageType = arrowEvent.damageTypeId || arrowEvent.metadata?.damage_type_id;
      if (damageType) {
        const variant = resolveVariant(arrowEvent.type);
        return getDamageTypeColor(damageType, { variant });
      }
    }
    const fallback = findCombatant(attackerKey) || findCombatant(targetKey);
    return resolveElementColor(fallback);
  })();

  $: arrowVisible =
    attackerCanvas &&
    targetCanvas &&
    (Math.abs(attackerCanvas.x - targetCanvas.x) > 1 || Math.abs(attackerCanvas.y - targetCanvas.y) > 1);

  $: showAttackerPulse = Boolean(attackerCanvas);
  $: showTargetPulse = Boolean(targetCanvas);
</script>

{#if showAttackerPulse || showTargetPulse}
  <div class:reduced={reducedMotion} class="targeting-overlay" style={`--arrow-color:${arrowColor};`}>
    <svg viewBox="0 0 1000 1000" preserveAspectRatio="none">
      <defs>
        <!-- Smaller arrowhead -->
        <marker id={markerId} viewBox="0 0 12 12" refX="7" refY="6" markerWidth="8" markerHeight="8" orient="auto">
          <path d="M0,0 L12,6 L0,12 z" fill="var(--arrow-color)" />
        </marker>
      </defs>
      {#if arrowVisible}
        <line
          class="arrow-line"
          x1={attackerCanvas?.x ?? 0}
          y1={attackerCanvas?.y ?? 0}
          x2={targetCanvas?.x ?? 0}
          y2={targetCanvas?.y ?? 0}
          marker-end={`url(#${markerId})`}
        />
      {/if}
      <!-- Attacker pulse removed per UX feedback -->
      <!-- Target pulse removed per UX feedback -->
    </svg>
  </div>
{/if}

<style>
  .targeting-overlay {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 4;
  }

  .targeting-overlay svg {
    width: 100%;
    height: 100%;
    overflow: visible;
  }

  .arrow-line {
    stroke: var(--arrow-color, #f6d365);
    stroke-width: 3; /* thinner arrow */
    stroke-linecap: round;
    filter: drop-shadow(0 0 10px rgba(0, 0, 0, 0.35));
  }

  .targeting-overlay:not(.reduced) .arrow-line {
    stroke-dasharray: 14 12;
    animation: arrow-flow 0.7s linear infinite;
  }

  .targeting-overlay.reduced .arrow-line {
    stroke-dasharray: none;
    animation: none;
  }

  .node {
    fill: rgba(0, 0, 0, 0);
    stroke: var(--arrow-color, #f6d365);
    stroke-width: 3;
    filter: drop-shadow(0 0 8px rgba(0, 0, 0, 0.45));
    transform-box: fill-box;
    transform-origin: center;
  }

  .node.attacker {
    fill: var(--arrow-color, #f6d365);
    opacity: 0.22;
  }

  .targeting-overlay:not(.reduced) .node.attacker {
    animation: attacker-pulse 1s ease-in-out infinite;
  }

  .targeting-overlay.reduced .node.attacker {
    animation: none;
  }

  .node.target.outer {
    fill: rgba(0, 0, 0, 0.35);
    stroke-width: 2;
  }

  .node.target.inner {
    fill: var(--arrow-color, #f6d365);
    opacity: 0.45;
    stroke: none;
  }

  .targeting-overlay:not(.reduced) .node.target.inner {
    animation: target-pulse 1s ease-in-out infinite alternate;
  }

  .targeting-overlay.reduced .node.target.inner {
    animation: none;
  }

  @keyframes arrow-flow {
    from {
      stroke-dashoffset: 0;
    }
    to {
      stroke-dashoffset: 52;
    }
  }

  @keyframes attacker-pulse {
    0%, 100% {
      transform: scale(1);
      opacity: 0.22;
    }
    50% {
      transform: scale(1.08);
      opacity: 0.35;
    }
  }

  @keyframes target-pulse {
    0% {
      transform: scale(1);
      opacity: 0.35;
    }
    100% {
      transform: scale(1.12);
      opacity: 0.6;
    }
  }
</style>
