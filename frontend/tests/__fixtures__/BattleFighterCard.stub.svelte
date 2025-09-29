<script>
  export let fighter = {};
  export let position = 'bottom';
  export let effectiveReducedMotion = false;
  export let sizePx = 0;
  export let highlight = false;
</script>

<div
  data-testid="fighter-card"
  data-id={fighter?.id ?? ''}
  data-position={position}
  data-highlight={highlight ? 'yes' : 'no'}
></div>
