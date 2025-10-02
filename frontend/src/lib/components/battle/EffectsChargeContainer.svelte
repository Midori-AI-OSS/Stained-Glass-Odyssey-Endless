<script>
  export let charges = [];
  export let reducedMotion = false;
  export let panelLabel = 'Effect charge progress';

  const numberFormatter = new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 0,
  });

  const clamp = (value, min, max) => {
    const v = Number(value);
    if (!Number.isFinite(v)) return min;
    return Math.max(min, Math.min(max, v));
  };

  function normalizeProgress(raw) {
    const value = Number(raw);
    if (!Number.isFinite(value)) return 0;
    if (value > 1 && value <= 100) {
      return clamp(value / 100, 0, 1);
    }
    return clamp(value, 0, 1);
  }

  function normalizeDamage(raw) {
    const value = Number(raw);
    if (!Number.isFinite(value)) return null;
    return Math.max(0, value);
  }

  function resolveName(entry, index) {
    const candidates = [
      entry?.name,
      entry?.label,
      entry?.id,
      entry?.effect_id,
      entry?.effectId,
    ];
    for (const candidate of candidates) {
      if (candidate === undefined || candidate === null) continue;
      const text = String(candidate).trim();
      if (text) return text;
    }
    return `Effect ${index + 1}`;
  }

  function resolveKey(entry, index, name) {
    const candidates = [entry?.id, entry?.key, entry?.effect_id, entry?.effectId, name];
    for (const candidate of candidates) {
      if (candidate === undefined || candidate === null) continue;
      const text = String(candidate).trim();
      if (text) return `${text}::${index}`;
    }
    return `entry-${index}`;
  }

  function formatDamage(value) {
    if (!Number.isFinite(value) || value <= 0) return '';
    return numberFormatter.format(Math.round(value));
  }

  function describeCharge({ name, percentLabel, damageLabel }) {
    if (!name) return percentLabel;
    if (damageLabel) {
      return `${name} ${percentLabel} charged, approximately ${damageLabel} damage`;
    }
    return `${name} ${percentLabel} charged`;
  }

  $: normalizedCharges = Array.isArray(charges)
    ? charges
        .map((entry, index) => {
          if (!entry || typeof entry !== 'object') return null;
          const name = resolveName(entry, index);
          const key = resolveKey(entry, index, name);
          const progress = normalizeProgress(entry.progress ?? entry.charge ?? entry.value ?? 0);
          const percent = Math.round(progress * 1000) / 10; // one decimal precision for width
          const percentLabel = `${Math.round(progress * 100)}%`;
          const damageValue = normalizeDamage(
            entry.estimatedDamage ?? entry.estimated_damage ?? entry.damage ?? entry.expected_damage
          );
          const damageLabel = formatDamage(damageValue);
          return {
            key,
            name,
            progress,
            percent,
            percentLabel,
            damageValue,
            damageLabel,
            ariaLabel: describeCharge({ name, percentLabel, damageLabel }),
          };
        })
        .filter(Boolean)
    : [];
</script>

{#if normalizedCharges.length}
  <section class="effects-charge-container" class:reduced={reducedMotion} aria-label={panelLabel}>
    <h2 class="sr-only">{panelLabel}</h2>
    <ol class="charge-list">
      {#each normalizedCharges as charge (charge.key)}
        <li class="charge-entry" data-testid="effect-charge-entry">
          <div class="charge-header">
            <span class="charge-name">{charge.name}</span>
            <span class="charge-percent" aria-hidden="true">{charge.percentLabel}</span>
          </div>
          <div
            class="charge-progress"
            role="progressbar"
            aria-label={charge.ariaLabel}
            aria-valuemin="0"
            aria-valuemax="100"
            aria-valuenow={Math.round(charge.progress * 100)}
            aria-valuetext={`${charge.percentLabel} charged`}
          >
            <div class="charge-fill" style={`width: ${charge.percent}%;`}></div>
          </div>
          {#if charge.damageLabel}
            <div class="charge-damage" data-testid="effect-charge-damage" aria-hidden="true">
              ≈ {charge.damageLabel}
            </div>
          {/if}
        </li>
      {/each}
    </ol>
  </section>
{/if}

<style>
  .effects-charge-container {
    pointer-events: none;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    width: clamp(220px, 22vw, 280px);
    max-width: 320px;
    padding: 0.9rem 1rem;
    border-radius: 0;
    background: linear-gradient(
        0deg,
        color-mix(in oklab, var(--accent, #8ac) 18%, transparent 82%),
        color-mix(in oklab, var(--accent, #8ac) 6%, transparent 94%)
      ),
      var(--glass-bg);
    border: var(--glass-border);
    box-shadow: var(--glass-shadow);
    color: rgba(248, 250, 255, 0.95);
    backdrop-filter: var(--glass-filter);
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }

  .charge-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .charge-entry {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }

  .charge-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 0.5rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  .charge-name {
    font-size: 0.78rem;
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .charge-percent {
    font-size: 0.75rem;
    opacity: 0.85;
  }

  .charge-progress {
    position: relative;
    width: 100%;
    height: 0.6rem;
    border-radius: 0;
    background: linear-gradient(
        0deg,
        color-mix(in oklab, var(--accent, #8ac) 12%, transparent 88%),
        color-mix(in oklab, var(--accent, #8ac) 4%, transparent 96%)
      ),
      var(--glass-bg);
    border: 1px solid color-mix(in oklab, var(--accent, #8ac) 28%, transparent 72%);
    box-shadow: inset 0 0 0 1px color-mix(in oklab, var(--accent, #8ac) 18%, transparent 82%);
    overflow: hidden;
  }

  .charge-fill {
    height: 100%;
    background: linear-gradient(
      90deg,
      color-mix(in oklab, var(--accent, #8ac) 65%, white 35%),
      color-mix(in oklab, var(--accent, #8ac) 35%, white 65%)
    );
    box-shadow: 0 0 12px color-mix(in oklab, var(--accent, #8ac) 55%, transparent 45%);
    border-right: 1px solid color-mix(in oklab, var(--accent, #8ac) 45%, transparent 55%);
    transition: width 260ms cubic-bezier(0.25, 0.9, 0.3, 1);
  }

  .charge-damage {
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', 'Fira Mono', monospace;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    opacity: 0.82;
  }

  .effects-charge-container.reduced .charge-fill {
    transition: none;
  }

  @media (prefers-reduced-motion: reduce) {
    .effects-charge-container .charge-fill {
      transition: none;
    }
  }

  @media (max-width: 720px) {
    .effects-charge-container {
      width: clamp(200px, 60vw, 260px);
      padding: 0.75rem 0.9rem;
    }

    .charge-name {
      font-size: 0.72rem;
    }

    .charge-damage {
      font-size: 0.68rem;
    }
  }
</style>
