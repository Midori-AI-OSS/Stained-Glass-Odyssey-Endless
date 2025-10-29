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

  $: meta = JSON.stringify({
    rosterLength: Array.isArray(roster) ? roster.length : 0,
    previewId: previewId ?? '',
    selectedCount: Array.isArray(selected) ? selected.length : 0,
    userBuffPercent: Number.isFinite(userBuffPercent) ? userBuffPercent : 0,
    upgradeMode: Boolean(upgradeMode),
    hasUpgradeData: Boolean(upgradeData),
    upgradeLoading: Boolean(upgradeLoading),
    upgradeError: upgradeError ? String(upgradeError) : '',
    hasUpgradeContext: Boolean(upgradeContext),
    selectedStat: selectedStat ?? ''
  });
</script>

<div data-testid="stub-stat-tabs">
  <span data-testid="stub-stat-tabs-count">{roster.length}</span>
  <span data-testid="stub-stat-tabs-upgrade">{upgradeMode ? 'upgrade' : 'portrait'}</span>
  <span data-testid="stub-stat-tabs-props" aria-hidden="true" style="display: none">{meta}</span>
</div>
