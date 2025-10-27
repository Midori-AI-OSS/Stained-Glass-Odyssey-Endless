<script>
  export let roster = [];
  export let previewId = null;
  export let selected = [];
  export let userBuffPercent = 0;
  export let upgradeMode = false;
  export let upgradeData = null;
  export let upgradeLoading = false;
  export let upgradeError = null;
  export let upgradeContext = null;
  export let selectedStat = null;
</script>

<div data-testid="stub-stat-tabs">
  <span data-testid="stub-stat-tabs-count">{roster.length}</span>
  <span data-testid="stub-stat-tabs-upgrade">{upgradeMode ? 'upgrade' : 'portrait'}</span>
</div>
