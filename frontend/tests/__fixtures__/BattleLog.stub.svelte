<script>
  export let logs = [];
  export let highlightedId = null;
  export let reducedMotion = false;
</script>

<div data-testid="battle-log" data-count={Array.isArray(logs) ? logs.length : 0} data-highlight={highlightedId ?? ''}></div>
