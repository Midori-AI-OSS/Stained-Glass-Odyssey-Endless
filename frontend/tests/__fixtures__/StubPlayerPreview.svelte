<script>
  export let roster = [];
  export let previewId = null;
  export let mode = 'portrait';
  export let upgradeContext = null;
  export let upgradeData = null;
  export let upgradeLoading = false;
  export let upgradeError = null;
  export let selectedStat = null;

  $: meta = JSON.stringify({
    rosterLength: Array.isArray(roster) ? roster.length : 0,
    hasUpgradeContext: Boolean(upgradeContext),
    hasUpgradeData: Boolean(upgradeData),
    upgradeLoading: Boolean(upgradeLoading),
    upgradeError: upgradeError ? String(upgradeError) : '',
    selectedStat: selectedStat ?? ''
  });
</script>

<div data-testid="stub-player-preview">
  <span data-testid="stub-player-preview-id">{previewId}</span>
  <span data-testid="stub-player-preview-mode">{mode}</span>
  <span data-testid="stub-player-preview-props" aria-hidden="true" style="display: none">{meta}</span>
</div>
