<script>
  import { Trash2, Download, Upload } from 'lucide-svelte';
  export let framerate = 60;
  export let reducedMotion = false;
  export let handleWipe;
  export let wipeStatus = '';
  export let handleBackup;
  export let handleImport;
  export let scheduleSave;
  export let healthStatus = 'unknown';
  export let healthPing = null;
  export let refreshHealth;
</script>

<div class="panel">
  <div class="control" title="Backend health and network latency.">
    <label>Backend Health</label>
    <span class="badge" data-status={healthStatus}>
      {healthStatus === 'healthy' ? 'Healthy' : healthStatus === 'degraded' ? 'Degraded' : healthStatus === 'error' ? 'Error' : 'Unknown'}
    </span>
    {#if healthPing !== null}
      <span class="ping">{Math.round(healthPing)}ms</span>
    {/if}
    <button on:click={() => refreshHealth(true)}>Refresh</button>
  </div>
  <div class="control" title="Limit server polling frequency.">
    <label>Framerate</label>
    <select bind:value={framerate} on:change={scheduleSave}>
      <option value={30}>30</option>
      <option value={60}>60</option>
      <option value={120}>120</option>
    </select>
  </div>
  <div class="control" title="Slow down battle animations.">
    <label>Reduced Motion</label>
    <input type="checkbox" bind:checked={reducedMotion} on:change={scheduleSave} />
  </div>
  <div class="control" title="Clear all save data.">
    <Trash2 />
    <label>Wipe Save Data</label>
    <button on:click={handleWipe}>Wipe</button>
  </div>
  {#if wipeStatus}
    <p class="status" data-testid="wipe-status">{wipeStatus}</p>
  {/if}
  <div class="control" title="Download encrypted backup of save data.">
    <Download />
    <label>Backup Save Data</label>
    <button on:click={handleBackup}>Backup</button>
  </div>
  <div class="control" title="Import an encrypted save backup.">
    <Upload />
    <label>Import Save Data</label>
    <input type="file" accept=".afsave" on:change={handleImport} />
  </div>
</div>

<style src="./settings-shared.css"></style>
