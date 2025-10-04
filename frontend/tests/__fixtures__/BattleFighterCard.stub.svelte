<script>
  export let fighter = {};
  export let position = 'bottom';
  export let effectiveReducedMotion = false;
  export let sizePx = 0;
  export let highlight = false;
  export let tickIndicators = [];
</script>

<div
  data-testid="fighter-card"
  data-id={fighter?.id ?? ''}
  data-position={position}
  data-highlight={highlight ? 'yes' : 'no'}
  data-ticks={Array.isArray(tickIndicators) ? tickIndicators.length : 0}
  data-tick-types={Array.isArray(tickIndicators) ? tickIndicators.map(item => item?.type || '').join(',') : ''}
></div>
