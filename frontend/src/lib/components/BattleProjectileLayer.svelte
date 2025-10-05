<script>
  import { getDamageTypePalette, stringHashIndex } from '../systems/assetLoader.js';
  import { motionStore } from '../systems/settingsStorage.js';

  const VIEWBOX = 1000;
  const MIN_LENGTH = 24;
  const DEFAULT_DURATION = 420;

  export let projectiles = [];
  export let anchors = {};
  export let reducedMotion = false;
  export let durationMs = DEFAULT_DURATION;

  $: motionSettings = $motionStore || { globalReducedMotion: false };
  $: effectiveReducedMotion = Boolean(
    reducedMotion || motionSettings.globalReducedMotion || motionSettings.disableFloatingDamage
  );

  function normalizeAnchor(anchor) {
    if (!anchor || typeof anchor !== 'object') return null;
    const x = Number(anchor.x);
    const y = Number(anchor.y);
    if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
    return { x: Math.max(0, Math.min(1, x)), y: Math.max(0, Math.min(1, y)) };
  }

  function clampDuration(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return DEFAULT_DURATION;
    return Math.max(120, Math.min(1200, numeric));
  }

  function resolvePalette(entry) {
    if (!entry) {
      return getDamageTypePalette('generic');
    }
    if (entry.palette && typeof entry.palette === 'object') {
      const { base, highlight, shadow } = entry.palette;
      if (base || highlight || shadow) {
        return entry.palette;
      }
    }
    return getDamageTypePalette(entry.damageTypeId || 'generic');
  }

  function resolveSequenceSeed(entry) {
    if (!entry) return '';
    const candidates = [
      entry.sequenceKey,
      entry.sequence,
      entry.sequenceToken,
      entry.metadata?.attack_sequence,
      entry.metadata?.attackSequence,
      entry.metadata?.sequence,
      `${entry.sourceId || ''}->${entry.targetId || ''}`,
      entry.id,
    ];
    for (const candidate of candidates) {
      if (candidate === undefined || candidate === null) continue;
      try {
        const text = typeof candidate === 'string' ? candidate : JSON.stringify(candidate);
        if (text && text.trim() !== '') return text;
      } catch {}
    }
    return '';
  }

  function buildColor(entry) {
    const palette = resolvePalette(entry) || {};
    const swatches = [palette.base, palette.highlight, palette.shadow].filter(Boolean);
    if (!swatches.length) {
      return 'rgba(255, 255, 255, 0.45)';
    }
    const seed = resolveSequenceSeed(entry);
    const index = stringHashIndex(seed || entry.id || Date.now(), swatches.length);
    return swatches[Math.max(0, Math.min(swatches.length - 1, index))] || swatches[0];
  }

  function shortenTowardsTarget(start, end, factor = 0.82) {
    if (!start || !end) return { start, end };
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const length = Math.hypot(dx, dy);
    if (!length) return { start, end };
    const clamped = Math.max(0.1, Math.min(1, factor));
    const adjustedEnd = {
      x: start.x + dx * clamped,
      y: start.y + dy * clamped,
    };
    return { start, end: adjustedEnd };
  }

  function buildProjectile(entry) {
    if (!entry || typeof entry !== 'object') return null;
    const source = normalizeAnchor(anchors?.[entry.sourceId]);
    const target = normalizeAnchor(anchors?.[entry.targetId]);
    if (!source || !target) return null;
    const { start, end } = shortenTowardsTarget(source, target);
    const x1 = Math.round(start.x * VIEWBOX);
    const y1 = Math.round(start.y * VIEWBOX);
    const x2 = Math.round(end.x * VIEWBOX);
    const y2 = Math.round(end.y * VIEWBOX);
    const dx = x2 - x1;
    const dy = y2 - y1;
    const length = Math.hypot(dx, dy);
    if (!Number.isFinite(length) || length < MIN_LENGTH) {
      return null;
    }
    const dash = Math.max(MIN_LENGTH, Math.round(length));
    const color = buildColor(entry);
    return {
      id: entry.id,
      x1,
      y1,
      x2,
      y2,
      dash,
      color,
    };
  }

  $: cleanedDuration = clampDuration(durationMs);
  $: renderList = Array.isArray(projectiles)
    ? projectiles.map(buildProjectile).filter(Boolean)
    : [];
</script>

<svg
  class:reduced={effectiveReducedMotion}
  class="projectile-layer"
  viewBox={`0 0 ${VIEWBOX} ${VIEWBOX}`}
  preserveAspectRatio="none"
  style={`--projectile-duration:${cleanedDuration}ms;`}
  aria-hidden="true"
>
  {#each renderList as projectile (projectile.id)}
    <g class="projectile" data-id={projectile.id}>
      <line
        class="projectile-line"
        x1={projectile.x1}
        y1={projectile.y1}
        x2={projectile.x2}
        y2={projectile.y2}
        style={`--projectile-color:${projectile.color}; --projectile-dash:${projectile.dash};`}
      />
      <circle
        class="projectile-head"
        cx={projectile.x2}
        cy={projectile.y2}
        r={14}
        style={`--projectile-color:${projectile.color};`}
      />
    </g>
  {/each}
</svg>

<style>
  .projectile-layer {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }

  .projectile-line {
    stroke: var(--projectile-color, rgba(255, 255, 255, 0.5));
    stroke-width: 22;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-dasharray: var(--projectile-dash, 60);
    stroke-dashoffset: var(--projectile-dash, 60);
    animation: projectile-flight var(--projectile-duration, 420ms) ease-out forwards;
  }

  .projectile-head {
    fill: var(--projectile-color, rgba(255, 255, 255, 0.5));
    opacity: 0;
    transform-origin: center;
    animation: projectile-pop var(--projectile-duration, 420ms) ease-out forwards;
  }

  .reduced .projectile-line,
  .reduced .projectile-head {
    animation: none;
    stroke-dashoffset: 0;
    opacity: 0.75;
  }

  @keyframes projectile-flight {
    0% {
      stroke-dashoffset: var(--projectile-dash, 60);
      opacity: 0;
    }

    25% {
      opacity: 1;
    }

    100% {
      stroke-dashoffset: 0;
      opacity: 0;
    }
  }

  @keyframes projectile-pop {
    0% {
      opacity: 0;
      transform: scale(0.3);
    }

    40% {
      opacity: 1;
      transform: scale(1);
    }

    100% {
      opacity: 0;
      transform: scale(0.6);
    }
  }
</style>
