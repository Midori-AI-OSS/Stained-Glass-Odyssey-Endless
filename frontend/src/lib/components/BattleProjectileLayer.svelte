<script>
  import { getDamageTypePalette, stringHashIndex } from '../systems/assetLoader.js';
  import { motionStore } from '../systems/settingsStorage.js';

  const VIEWBOX = 1000;
  const MIN_LENGTH = 24;
  const DEFAULT_DURATION = 420;
  const CUBIC_SEGMENTS = 22;
  const WHITE = '#ffffff';
  const BLACK = '#000000';

  export let projectiles = [];
  export let anchors = {};
  export let reducedMotion = false;
  export let durationMs = DEFAULT_DURATION;
  export let variant = 'default';

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

  function resolvePhotonSeed(entry) {
    if (entry?.photonBladeSeed) {
      try {
        const text = String(entry.photonBladeSeed);
        if (text.trim() !== '') {
          return text;
        }
      } catch {}
    }
    const fallback = resolveSequenceSeed(entry);
    if (fallback) return fallback;
    if (entry?.id) return String(entry.id);
    return '';
  }

  function seededRandom(seed, label, modulo = 65536) {
    const safeModulo = Math.max(2, Math.floor(modulo));
    const basis = `${seed || ''}:${label}`;
    const index = stringHashIndex(basis, safeModulo);
    return index / Math.max(1, safeModulo - 1);
  }

  function clampValue(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function clampPoint(point) {
    return {
      x: clampValue(point.x, 0, VIEWBOX),
      y: clampValue(point.y, 0, VIEWBOX),
    };
  }

  function shortenTowardsTarget(start, end, factor = 0.82) {
    if (!start || !end) return { start, end };
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const length = Math.hypot(dx, dy);
    if (!Number.isFinite(length) || length === 0) {
      return { start, end };
    }
    const clamped = Math.max(0.1, Math.min(1, factor));
    const adjustedEnd = {
      x: start.x + dx * clamped,
      y: start.y + dy * clamped,
    };
    return { start, end: adjustedEnd };
  }

  function parseHexColor(hex) {
    if (typeof hex !== 'string') return null;
    let value = hex.trim();
    if (!value) return null;
    if (value.startsWith('#')) value = value.slice(1);
    if (value.length === 3) {
      value = value
        .split('')
        .map(ch => ch + ch)
        .join('');
    }
    if (value.length !== 6 || /[^0-9a-fA-F]/.test(value)) return null;
    const numeric = Number.parseInt(value, 16);
    if (!Number.isFinite(numeric)) return null;
    return {
      r: (numeric >> 16) & 0xff,
      g: (numeric >> 8) & 0xff,
      b: numeric & 0xff,
    };
  }

  function clampChannel(value) {
    return Math.min(255, Math.max(0, Math.round(value)));
  }

  function formatHex(r, g, b) {
    const value = (clampChannel(r) << 16) | (clampChannel(g) << 8) | clampChannel(b);
    return `#${value.toString(16).padStart(6, '0')}`;
  }

  function mixChannel(a, b, t) {
    return a + (b - a) * t;
  }

  function mixColors(colorA, colorB, ratio) {
    const a = parseHexColor(colorA);
    const b = parseHexColor(colorB);
    if (!a && !b) return colorA || colorB || WHITE;
    if (!a) return colorB ? formatHex(b.r, b.g, b.b) : colorB || WHITE;
    if (!b) return colorA ? formatHex(a.r, a.g, a.b) : colorA || WHITE;
    const t = Math.max(0, Math.min(1, ratio));
    const r = mixChannel(a.r, b.r, t);
    const g = mixChannel(a.g, b.g, t);
    const blue = mixChannel(a.b, b.b, t);
    return formatHex(r, g, blue);
  }

  function adjustBrightness(color, delta) {
    if (!delta) return color || WHITE;
    if (delta > 0) {
      return mixColors(color, WHITE, Math.min(1, delta));
    }
    return mixColors(color, BLACK, Math.min(1, Math.abs(delta)));
  }

  function rgbToHueDegrees(r, g, b) {
    const rn = r / 255;
    const gn = g / 255;
    const bn = b / 255;
    const max = Math.max(rn, gn, bn);
    const min = Math.min(rn, gn, bn);
    const delta = max - min;
    if (!Number.isFinite(delta) || delta === 0) return 0;
    let hue;
    if (max === rn) {
      hue = ((gn - bn) / delta) % 6;
    } else if (max === gn) {
      hue = (bn - rn) / delta + 2;
    } else {
      hue = (rn - gn) / delta + 4;
    }
    hue *= 60;
    if (hue < 0) hue += 360;
    return hue;
  }

  function resolveHue(entry, palette) {
    const normalized = Number(entry?.photonBladeHue);
    if (Number.isFinite(normalized) && normalized >= 0) {
      return Math.max(0, Math.min(360, normalized * 360));
    }
    const swatches = [palette?.base, palette?.highlight, palette?.shadow];
    for (const swatch of swatches) {
      const rgb = parseHexColor(swatch);
      if (!rgb) continue;
      const hue = rgbToHueDegrees(rgb.r, rgb.g, rgb.b);
      if (Number.isFinite(hue)) return Math.max(0, hue % 360);
    }
    return 0;
  }

  function computeColors(entry, palette, seed, entryVariant) {
    const base = palette?.base || WHITE;
    const highlight = palette?.highlight || base;
    const shadow = palette?.shadow || base;

    if (entryVariant === 'photonBlade') {
      const brightnessBias = seededRandom(seed, 'brightness');
      const glowBias = seededRandom(seed, 'glow');
      const stroke = mixColors(base, shadow, 0.35 + 0.3 * (1 - brightnessBias));
      const fill = mixColors(highlight, base, 0.4 + 0.35 * brightnessBias);
      const glow = mixColors(highlight, WHITE, 0.55 + 0.25 * glowBias);
      const accent = adjustBrightness(fill, 0.25 - glowBias * 0.4);
      return { stroke, fill, glow, accent };
    }

    const fallbackGlow = mixColors(base, WHITE, 0.45);
    return {
      stroke: base,
      fill: base,
      glow: fallbackGlow,
      accent: adjustBrightness(base, -0.2),
    };
  }

  function cubicPoint(p0, p1, p2, p3, t) {
    const mt = 1 - t;
    const mt2 = mt * mt;
    const t2 = t * t;
    const a = mt2 * mt;
    const b = 3 * mt2 * t;
    const c = 3 * mt * t2;
    const d = t * t2;
    return {
      x: a * p0.x + b * p1.x + c * p2.x + d * p3.x,
      y: a * p0.y + b * p1.y + c * p2.y + d * p3.y,
    };
  }

  function approximateCubicLength(p0, p1, p2, p3, segments = CUBIC_SEGMENTS) {
    let length = 0;
    let prev = p0;
    for (let i = 1; i <= segments; i += 1) {
      const t = i / segments;
      const point = cubicPoint(p0, p1, p2, p3, t);
      length += Math.hypot(point.x - prev.x, point.y - prev.y);
      prev = point;
    }
    return length;
  }

  function buildCubicGeometry(start, end, seed) {
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const length = Math.hypot(dx, dy);
    if (!Number.isFinite(length) || length < MIN_LENGTH) return null;

    const normX = length ? dx / length : 0;
    const normY = length ? dy / length : 0;
    const perpX = -normY;
    const perpY = normX;

    const direction = seededRandom(seed, 'direction') > 0.5 ? 1 : -1;
    const curvatureMagnitude = length * (0.16 + 0.12 * seededRandom(seed, 'curve'));
    const offset = curvatureMagnitude * direction;
    const counterOffset = -offset * (0.55 + 0.3 * seededRandom(seed, 'counter'));
    const c1Along = length * (0.24 + 0.18 * seededRandom(seed, 'alongA'));
    const c2Along = length * (0.56 + 0.2 * seededRandom(seed, 'alongB'));

    const control1 = clampPoint({
      x: start.x + normX * c1Along + perpX * offset,
      y: start.y + normY * c1Along + perpY * offset,
    });
    const control2 = clampPoint({
      x: start.x + normX * c2Along + perpX * counterOffset,
      y: start.y + normY * c2Along + perpY * counterOffset,
    });

    const p0 = { x: start.x, y: start.y };
    const p1 = control1;
    const p2 = control2;
    const p3 = { x: end.x, y: end.y };

    const lengthApprox = Math.max(MIN_LENGTH, approximateCubicLength(p0, p1, p2, p3));
    const derivative = {
      x: 3 * (p3.x - p2.x),
      y: 3 * (p3.y - p2.y),
    };
    const angle = Math.atan2(derivative.y, derivative.x);
    const arrowScale = 0.85 + 0.35 * seededRandom(seed, 'scale');

    return {
      path: `M ${p0.x} ${p0.y} C ${Math.round(p1.x)} ${Math.round(p1.y)} ${Math.round(p2.x)} ${Math.round(p2.y)} ${p3.x} ${p3.y}`,
      length: lengthApprox,
      arrow: {
        x: p3.x,
        y: p3.y,
        angleDeg: angle * (180 / Math.PI),
        scale: arrowScale,
      },
    };
  }

  function buildStraightGeometry(start, end) {
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const length = Math.hypot(dx, dy);
    if (!Number.isFinite(length) || length < MIN_LENGTH) return null;
    const angle = Math.atan2(dy, dx);
    return {
      path: `M ${start.x} ${start.y} L ${end.x} ${end.y}`,
      length: Math.max(MIN_LENGTH, length),
      arrow: {
        x: end.x,
        y: end.y,
        angleDeg: angle * (180 / Math.PI),
        scale: 1,
      },
    };
  }

  function buildProjectile(entry) {
    if (!entry || typeof entry !== 'object') return null;
    const entryVariant = String(entry.variant || variant || 'default');
    const source = normalizeAnchor(anchors?.[entry.sourceId]);
    const target = normalizeAnchor(anchors?.[entry.targetId]);
    if (!source || !target) return null;

    const { start, end } = shortenTowardsTarget(source, target);
    const startPx = {
      x: Math.round(start.x * VIEWBOX),
      y: Math.round(start.y * VIEWBOX),
    };
    const endPx = {
      x: Math.round(end.x * VIEWBOX),
      y: Math.round(end.y * VIEWBOX),
    };

    const palette = resolvePalette(entry);
    const seed = entryVariant === 'photonBlade' ? resolvePhotonSeed(entry) : resolveSequenceSeed(entry);

    const geometry = effectiveReducedMotion
      ? buildStraightGeometry(startPx, endPx)
      : entryVariant === 'photonBlade'
        ? buildCubicGeometry(startPx, endPx, seed)
        : buildStraightGeometry(startPx, endPx);

    if (!geometry) return null;

    const colors = computeColors(entry, palette, seed, entryVariant);
    const hue = resolveHue(entry, palette);

    return {
      id: entry.id || `${entryVariant}-${startPx.x}-${startPx.y}-${endPx.x}-${endPx.y}`,
      variant: entryVariant,
      path: geometry.path,
      length: geometry.length,
      stroke: colors.stroke,
      fill: colors.fill,
      glow: colors.glow,
      accent: colors.accent,
      hue,
      arrow: geometry.arrow,
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
    <g
      class={`projectile variant-${projectile.variant}`}
      data-id={projectile.id}
      style={`--blade-stroke:${projectile.stroke}; --blade-fill:${projectile.fill}; --blade-glow:${projectile.glow}; --blade-accent:${projectile.accent}; --blade-length:${projectile.length.toFixed(2)}; --blade-hue:${projectile.hue.toFixed(2)}; --blade-head-scale:${projectile.arrow?.scale ?? 1}; --blade-end-x:${projectile.arrow?.x ?? 0}px; --blade-end-y:${projectile.arrow?.y ?? 0}px; --blade-angle:${projectile.arrow?.angleDeg ?? 0}deg;`}
    >
      <path class="projectile-path" d={projectile.path} />
      <g class="projectile-head">
        <path class="projectile-head-shape" d="M 0 0 L -36 16 L -24 0 L -36 -16 Z" />
        <path class="projectile-head-flare" d="M -12 0 C -18 8 -26 8 -32 0 C -26 -8 -18 -8 -12 0 Z" />
      </g>
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

  .projectile {
    pointer-events: none;
  }

  .projectile-path {
    fill: none;
    stroke: var(--blade-stroke, rgba(255, 255, 255, 0.5));
    stroke-width: 20;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-dasharray: var(--blade-length, 80);
    stroke-dashoffset: var(--blade-length, 80);
    opacity: 0;
    animation: projectile-flight var(--projectile-duration, 420ms) ease-out forwards;
    filter: drop-shadow(0 0 14px var(--blade-glow, rgba(255, 255, 255, 0.45)));
  }

  .projectile.variant-photonBlade .projectile-path {
    stroke-width: 24;
    mix-blend-mode: screen;
    filter: drop-shadow(0 0 18px var(--blade-glow, rgba(255, 255, 255, 0.6)));
  }

  .projectile-head {
    transform-box: fill-box;
    transform-origin: center;
    opacity: 0;
    animation: projectile-head var(--projectile-duration, 420ms) ease-out forwards;
  }

  .projectile-head-shape {
    fill: var(--blade-fill, rgba(255, 255, 255, 0.7));
    stroke: var(--blade-stroke, rgba(255, 255, 255, 0.9));
    stroke-width: 4;
    stroke-linejoin: round;
    paint-order: stroke;
    filter: drop-shadow(0 0 16px var(--blade-glow, rgba(255, 255, 255, 0.5)));
  }

  .projectile-head-flare {
    fill: var(--blade-accent, rgba(255, 255, 255, 0.5));
    opacity: 0.75;
    mix-blend-mode: screen;
  }

  .reduced .projectile-path,
  .reduced .projectile-head {
    animation: none;
    opacity: 0.85;
  }

  .reduced .projectile-path {
    stroke-dashoffset: 0;
  }

  .reduced .projectile-head {
    transform: translate(var(--blade-end-x, 0px), var(--blade-end-y, 0px))
      rotate(var(--blade-angle, 0deg))
      scale(var(--blade-head-scale, 1));
  }

  @keyframes projectile-flight {
    0% {
      stroke-dashoffset: var(--blade-length, 80);
      opacity: 0;
    }

    20% {
      opacity: 1;
    }

    100% {
      stroke-dashoffset: 0;
      opacity: 0;
    }
  }

  @keyframes projectile-head {
    0% {
      opacity: 0;
      transform: translate(var(--blade-end-x, 0px), var(--blade-end-y, 0px))
        rotate(var(--blade-angle, 0deg))
        scale(calc(var(--blade-head-scale, 1) * 0.35));
    }

    35% {
      opacity: 1;
      transform: translate(var(--blade-end-x, 0px), var(--blade-end-y, 0px))
        rotate(var(--blade-angle, 0deg))
        scale(calc(var(--blade-head-scale, 1) * 0.98));
    }

    70% {
      opacity: 1;
      transform: translate(var(--blade-end-x, 0px), var(--blade-end-y, 0px))
        rotate(var(--blade-angle, 0deg))
        scale(calc(var(--blade-head-scale, 1) * 1.08));
    }

    100% {
      opacity: 0;
      transform: translate(var(--blade-end-x, 0px), var(--blade-end-y, 0px))
        rotate(var(--blade-angle, 0deg))
        scale(calc(var(--blade-head-scale, 1) * 0.6));
    }
  }
</style>
