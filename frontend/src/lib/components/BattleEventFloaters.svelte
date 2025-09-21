<script>
  import { onDestroy } from 'svelte';
  import { getDamageTypeVisual } from '$lib/systems/assetLoader.js';
  import { motionStore } from '../systems/settingsStorage.js';
  import { createFloaterTokens, deterministicVariation, EFFECT_TOKENS } from '../systems/animationTokens.js';

  export let events = [];
  export let reducedMotion = false; // Legacy prop for backward compatibility
  export let paceMs = 1200;
  export let animationSpeed = 1; // Animation speed from settings
  // Constant offsets (px) applied in addition to deterministic X offset per floater
  export let baseOffsetX = 0;
  export let baseOffsetY = -10;
  // Stagger additions within a batch so items show one-by-one
  export let staggerMs = null; // Will use tokens if null
  // Map of entity id -> { x: fraction(0..1), y: fraction(0..1) } relative to the battle field
  export let anchors = {};

  // Check both legacy prop and new granular settings using reactive store
  $: motionSettings = $motionStore || { globalReducedMotion: false, disableFloatingDamage: false };
  $: isFloatingDamageDisabled = reducedMotion || motionSettings.globalReducedMotion || motionSettings.disableFloatingDamage;

  // Create animation tokens for this component
  $: floaterTokens = createFloaterTokens({ animationSpeed, motionSettings, pacingMs: paceMs });
  $: effectiveStaggerMs = staggerMs ?? EFFECT_TOKENS.BATTLE_FLOATERS.STAGGER_STEP;

  let floaters = [];
  let counter = 0;
  const timeouts = new Map();
  const addTimers = new Set();

  const LABEL_FALLBACK_KEYS = [
    'effect_label',
    'effectLabel',
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
    'label',
    'name',
    'display_name',
    'displayName',
  ];

  const DETAIL_LABEL_KEYS = [
    'label',
    'name',
    'display_name',
    'displayName',
    'effect_name',
    'effect',
    'effect_type',
    'effectType',
    'action_name',
    'actionName',
    'source_name',
    'sourceName',
  ];

  const POSITIVE_HINTS = [
    'heal',
    'bonus',
    'boost',
    'buff',
    'shield',
    'refund',
    'grant',
    'revive',
    'revived',
    'revival',
    'extra_turn',
    'gain',
    'award',
    'summoned',
    'mitigation',
    'resist',
    'reduction',
    'charge',
  ];

  const NEGATIVE_HINTS = [
    'drain',
    'damage',
    'harm',
    'steal',
    'lose',
    'loss',
    'penalty',
    'tax',
    'sacrifice',
    'sacrificed',
    'shred',
    'debuff',
  ];

  function readLabelFromObject(candidate, fallbackKeys = LABEL_FALLBACK_KEYS) {
    if (!candidate || typeof candidate !== 'object') return '';
    const list = Array.isArray(candidate.effects) ? candidate.effects : [];
    for (const entry of list) {
      if (!entry || typeof entry !== 'object') continue;
      if (entry.name) return String(entry.name);
      if (entry.id) return String(entry.id);
    }
    for (const key of fallbackKeys) {
      const value = candidate[key];
      if (value !== undefined && value !== null && String(value).trim() !== '') {
        return String(value);
      }
    }
    return '';
  }

  function resolveLabel(metadata) {
    const label = readLabelFromObject(metadata);
    if (label) return label;
    const details = metadata && typeof metadata === 'object' ? metadata.details : null;
    if (details && typeof details === 'object') {
      return readLabelFromObject(details, DETAIL_LABEL_KEYS);
    }
    return '';
  }

  function resolveVariant(type, metadata, amount) {
    const t = String(type || '').toLowerCase();
    if (t === 'heal_received' || t === 'hot_tick') return 'heal';
    if (t === 'dot_tick') return 'dot';
    if (t === 'card_effect' || t === 'relic_effect') {
      const meta = metadata && typeof metadata === 'object' ? metadata : {};
      let searchSpace = (resolveLabel(meta) || '').toLowerCase();
      const fallbackValues = [
        meta.effect,
        meta.effect_type,
        meta.effectType,
        meta.card_name,
        meta.cardName,
        meta.relic_name,
        meta.relicName,
      ];
      if (meta.details && typeof meta.details === 'object') {
        const details = meta.details;
        fallbackValues.push(
          details.effect,
          details.effect_type,
          details.effectType,
          details.outcome,
          details.result,
          details.reason,
          details.description,
          details.label,
          details.name,
        );
      }
      for (const value of fallbackValues) {
        if (value !== undefined && value !== null) {
          const text = String(value).trim();
          if (text) searchSpace += ` ${text.toLowerCase()}`;
        }
      }
      const numericAmount = Number(amount ?? meta.amount);
      if (searchSpace.trim()) {
        if (NEGATIVE_HINTS.some((hint) => searchSpace.includes(hint))) return 'drain';
        if (POSITIVE_HINTS.some((hint) => searchSpace.includes(hint))) return 'buff';
      }
      if (Number.isFinite(numericAmount)) {
        if (numericAmount < 0) return 'drain';
        if (numericAmount > 0) return 'buff';
      }
      return 'buff';
    }
    return 'damage';
  }

  function resolveTone(variant) {
    const normalized = String(variant || '').toLowerCase();
    if (normalized === 'heal' || normalized === 'hot' || normalized === 'buff') {
      return 'heal';
    }
    return 'damage';
  }

  function scheduleRemoval(id, duration) {
    const timeoutMs = Math.max(floaterTokens.duration, Number(duration) || floaterTokens.duration) + 100;
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
    const duration = floaterTokens.duration;
    const step = Math.max(0, Math.min(Number(effectiveStaggerMs) || 0, 2000));
    list.forEach((raw, i) => {
      if (!raw || typeof raw !== 'object') return;
      const handle = setTimeout(() => {
        addTimers.delete(handle);
        const metadata = raw && typeof raw.metadata === 'object' ? raw.metadata : {};
        const amountValue = Number(raw.amount ?? metadata?.amount);
        const hasAmount = Number.isFinite(amountValue);
        const amount = hasAmount ? Math.abs(amountValue) : 0;
        const label = (raw.effectLabel || resolveLabel(metadata) || '').trim();
        const variant = resolveVariant(raw.type, metadata, amountValue);
        const damageType = raw.damageTypeId || metadata?.damage_type_id || '';
        const { icon: Icon, color } = getDamageTypeVisual(damageType, { variant });
        const showAmount = hasAmount && amount > 0;
        if (!showAmount && !label) return;
        const id = `${Date.now()}-${counter++}`;
        const target = String(raw.target_id || '');
        
        // Use deterministic offset based on target and event type for consistency
        const offsetSeed = `${target}-${variant}-${amount}-${label}`;
        const offset = deterministicVariation(offsetSeed, -EFFECT_TOKENS.BATTLE_FLOATERS.OFFSET_RANGE / 2, EFFECT_TOKENS.BATTLE_FLOATERS.OFFSET_RANGE / 2);
        const anchor = (anchors && target && anchors[target]) ? anchors[target] : null;
        const x = anchor && Number.isFinite(anchor.x) ? anchor.x : 0.5;
        const y = anchor && Number.isFinite(anchor.y) ? anchor.y : 0.52;
        const critical = Boolean(raw.isCritical || metadata?.is_critical);
        const prefix =
          variant === 'damage' || variant === 'dot' || variant === 'drain' ? '-' : '+';
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
            tone: resolveTone(variant),
            type: raw.type,
            critical,
            showAmount,
            prefix,
          }
        ];
        scheduleRemoval(id, duration);
      }, i * step);
      addTimers.add(handle);
    });
  }

  $: if (events && events.length && !isFloatingDamageDisabled) {
    pushEvents(events);
  }

  function handleAnimationEnd(entry) {
    if (!isFloatingDamageDisabled) {
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

<div class:reduced={isFloatingDamageDisabled} class="floater-host" aria-hidden="true">
  {#each floaters as entry (entry.id)}
    <div
      class={`floater ${entry.tone} ${entry.variant} ${entry.critical ? 'critical' : ''}`}
      style={`--accent: ${entry.color}; --offset: ${entry.offset}px; --x: ${entry.x}; --y: ${entry.y}; --floater-duration: ${floaterTokens.durationMs}; --x-offset: ${Number(baseOffsetX) || 0}px; --y-offset: ${Number(baseOffsetY) || 0}px;`}
      on:animationend={() => handleAnimationEnd(entry)}
    >
      <div class="badge">
        <span class="icon" style={`background:${entry.color}`}>
          {#if entry.Icon}
            <svelte:component this={entry.Icon} size={14} stroke-width={2} />
          {/if}
        </span>
        {#if entry.critical && (entry.variant === 'damage' || entry.variant === 'drain')}
          <span class="crit-prefix">CRIT:&nbsp;</span>
        {/if}
        {#if entry.showAmount}
          <span class="amount" data-variant={entry.variant}>
            {entry.prefix}{Math.round(entry.amount)}
          </span>
        {/if}
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

  .floater.critical .badge {
    font-weight: 800;
  }

  .crit-prefix {
    letter-spacing: 0.02em;
  }

  .floater.heal .badge,
  .floater.buff .badge {
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
