<script>
  export let roster = [];
  export let previewId = null;
  export let mode = 'portrait';
  export let upgradeContext = null;
  export let upgradeData = null;
  export let upgradeLoading = false;
  export let upgradeError = null;
  export let selectedStat = null;
</script>

<div data-testid="stub-player-preview">
  <span data-testid="stub-player-preview-id">{previewId}</span>
  <span data-testid="stub-player-preview-mode">{mode}</span>
</div>
