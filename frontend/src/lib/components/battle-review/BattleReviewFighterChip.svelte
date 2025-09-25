<script>
  import BattleFighterCard from '../../battle/BattleFighterCard.svelte';

  const SIZE_MAP = {
    chip: 72,
    small: 56,
    medium: 96
  };

  export let fighter = {};
  export let rankTag = null;
  export let reducedMotion = false;
  export let highlight = false;
  export let size = 'chip';
  export let sizePx = 0;
  export let position = 'top';

  $: portraitSize = Number(sizePx) > 0 ? Number(sizePx) : SIZE_MAP[size] || SIZE_MAP.chip;
  $: decoratedFighter = rankTag != null ? { ...fighter, rank: rankTag } : fighter || {};
</script>

<div class="review-fighter-chip" style={`--portrait-size: ${portraitSize}px;`}>
  <BattleFighterCard
    fighter={decoratedFighter}
    position={position}
    reducedMotion={reducedMotion}
    highlight={highlight}
    size="small"
    sizePx={portraitSize}
  />
</div>

<style>
  .review-fighter-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: var(--portrait-size);
    height: var(--portrait-size);
  }

  .review-fighter-chip :global(.modern-fighter-card) {
    width: var(--portrait-size);
    height: var(--portrait-size);
    min-width: var(--portrait-size);
    min-height: var(--portrait-size);
  }

  .review-fighter-chip :global(.fighter-portrait) {
    border-radius: 50%;
    box-shadow: none;
  }

  .review-fighter-chip :global(.overlay-ui),
  .review-fighter-chip :global(.name-chip) {
    display: none !important;
  }

  .review-fighter-chip :global(.fighter-portrait::after) {
    display: none;
  }

  .review-fighter-chip :global(.fighter-portrait .element-effect) {
    filter: blur(0.75px);
  }

  .review-fighter-chip :global(.fighter-portrait .ult-glow),
  .review-fighter-chip :global(.fighter-portrait .ult-pulse) {
    opacity: 0.55;
  }

  .review-fighter-chip :global(.fighter-portrait .ult-gauge) {
    display: none;
  }

  .review-fighter-chip :global(.fighter-portrait .passive-indicators) {
    display: none;
  }
</style>
