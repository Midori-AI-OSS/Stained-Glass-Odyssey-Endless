<script>
  export let projectiles = [];
  export let anchors = {};
  export let reducedMotion = false;
  export let durationMs = 0;
</script>

<script>
  $: projectileCount = Array.isArray(projectiles) ? projectiles.length : 0;
  $: startIds = Array.isArray(projectiles)
    ? projectiles.map((entry) => entry?.sourceId || '').join(',')
    : '';
  $: targetIds = Array.isArray(projectiles)
    ? projectiles.map((entry) => entry?.targetId || '').join(',')
    : '';
  $: sequenceKeys = Array.isArray(projectiles)
    ? projectiles.map((entry) => entry?.sequenceKey || '').join(',')
    : '';
</script>

<div
  data-testid="projectiles-probe"
  data-count={projectileCount}
  data-starts={startIds}
  data-targets={targetIds}
  data-sequences={sequenceKeys}
  data-duration={durationMs}
  data-reduced={reducedMotion ? 'yes' : 'no'}
></div>
