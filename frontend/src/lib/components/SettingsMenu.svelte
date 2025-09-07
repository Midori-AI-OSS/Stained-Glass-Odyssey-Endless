<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import {
    Volume2,
    Music,
    Mic,
    Power,
    Trash2,
    Download,
    Upload,
    Cog,
    Brain,
    Gamepad
  } from 'lucide-svelte';
  import { endRun, endAllRuns, wipeData, exportSave, importSave, getLrmConfig, setLrmModel, testLrmModel, getBackendHealth } from '../systems/api.js';
  import { getActiveRuns } from '../systems/uiApi.js';
  import { saveSettings, clearSettings, clearAllClientData } from '../systems/settingsStorage.js';

  const dispatch = createEventDispatcher();
  export let sfxVolume = 50;
  export let musicVolume = 50;
  export let voiceVolume = 50;
  export let framerate = 60;
  export let reducedMotion = false;
  export let lrmModel = '';
  export let runId = '';
  export let backendFlavor = typeof window !== 'undefined' ? window.backendFlavor || '' : '';

  let showLrm = false;
  $: showLrm = (backendFlavor || '').toLowerCase().includes('llm');

  let saveStatus = '';
  let saveTimeout;
  let resetTimeout;
  let lrmOptions = [];
  let testReply = '';

  let activeTab = 'audio';

  // Feedback for End Run action
  let endingRun = false;
  let endRunStatus = '';

  // Backend health (moved from floating ping indicator)
  let healthStatus = 'unknown'; // 'healthy' | 'degraded' | 'error' | 'unknown'
  let healthPing = null;
  let lastHealthFetch = 0;

  async function refreshHealth(force = false) {
    const now = Date.now();
    if (!force && now - lastHealthFetch < 1500) return; // throttle within tab
    try {
      const { status, ping_ms } = await getBackendHealth();
      healthStatus = status === 'ok' ? 'healthy' : (status === 'degraded' ? 'degraded' : (status === 'error' ? 'error' : String(status)));
      healthPing = typeof ping_ms === 'number' ? ping_ms : null;
    } catch {
      healthStatus = 'error';
      healthPing = null;
    } finally {
      lastHealthFetch = now;
    }
  }

  onMount(async () => {
    if (showLrm) {
      try {
        const cfg = await getLrmConfig();
        lrmOptions = cfg?.available_models || [];
        lrmModel = cfg?.current_model || lrmModel;
        saveSettings({ lrmModel });
      } catch {
        /* ignore */
      }
    }
    // Preload health once so System tab has data quickly
    refreshHealth(true);
  });
  $: (activeTab === 'system') && refreshHealth(false);

  function save() {
    saveSettings({
      sfxVolume,
      musicVolume,
      voiceVolume,
      framerate: Number(framerate),
      reducedMotion
    });
    dispatch('save', {
      sfxVolume,
      musicVolume,
      voiceVolume,
      framerate: Number(framerate),
      reducedMotion
    });
    saveStatus = 'Saved';
    clearTimeout(resetTimeout);
    resetTimeout = setTimeout(() => {
      saveStatus = '';
    }, 1000);
  }

  function scheduleSave() {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(save, 300);
  }

  function handleModelChange() {
    saveSettings({ lrmModel });
    dispatch('save', { lrmModel });
    setLrmModel(lrmModel).catch(() => {});
  }

  async function handleTestModel() {
    testReply = '';
    try {
      const res = await testLrmModel('Say hello');
      testReply = res?.response || '';
    } catch {
      testReply = 'Error';
    }
  }


  async function handleEndRun() {
    endingRun = true;
    endRunStatus = runId ? 'Ending run…' : 'Ending all runs…';
    // Immediately halt any battle snapshot polling while ending the run
    try { if (typeof window !== 'undefined') window.afHaltSync = true; } catch {}

    let ended = false;
    if (runId) {
      try {
        await endRun(runId);
        // Verify deletion; if the run persists, fall back to end-all
        try {
          const data = await getActiveRuns();
          const stillActive = Array.isArray(data?.runs) && data.runs.some(r => r.run_id === runId);
          if (stillActive) {
            await endAllRuns();
            endRunStatus = 'Run force-ended';
          } else {
            endRunStatus = 'Run ended';
          }
          ended = true;
        } catch {
          endRunStatus = 'Run ended';
          ended = true;
        }
      } catch (e) {
        console.error('Failed to end run', e);
      }
    }

    if (!ended) {
      try {
        await endAllRuns();
        endRunStatus = 'Run force-ended';
      } catch (e) {
        console.error('Failed to force end runs', e);
        endRunStatus = 'Failed to end run';
      }
    }

    endingRun = false;
    dispatch('endRun');
    // Clear status after a short delay so users see feedback
    try { setTimeout(() => (endRunStatus = ''), 1200); } catch {}
  }

  async function handleEndAllRuns() {
    try {
      // Halt any polling to avoid races while clearing runs
      try { if (typeof window !== 'undefined') window.afHaltSync = true; } catch {}
      await endAllRuns();
    } catch (e) {
      console.error('Failed to end all runs', e);
    } finally {
      // Notify parent to refresh local run state
      dispatch('endRun');
    }
  }

  let wipeStatus = '';

  async function handleWipe() {
    wipeStatus = '';
    if (!confirm('This will erase all save data. Continue?')) return;
    let ok = true;
    try {
      await wipeData();
    } catch (e) {
      ok = false;
    } finally {
      // Always clear client state and reload, even if backend wipe fails
      clearSettings();
      await clearAllClientData();
      sfxVolume = 50;
      musicVolume = 50;
      voiceVolume = 50;
      framerate = 60;
      reducedMotion = false;
      runId = '';
      wipeStatus = ok ? 'Save data wiped. Reloading…' : 'Backend wipe failed; cleared local data. Reloading…';
      setTimeout(() => {
        try { window.location.reload(); } catch {}
      }, 50);
    }
  }

  async function handleBackup() {
    const blob = await exportSave();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'backup.afsave';
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleImport(event) {
    const [file] = event.target.files;
    if (file) {
      await importSave(file);
    }
  }
</script>

<div data-testid="settings-menu" class="tabbed">
  <div class="tabs">
    <button class:active={activeTab === 'audio'} on:click={() => (activeTab = 'audio')} title="Audio">
      <Volume2 />
    </button>
    <button class:active={activeTab === 'system'} on:click={() => (activeTab = 'system')} title="System">
      <Cog />
    </button>
    {#if showLrm}
      <button class:active={activeTab === 'llm'} on:click={() => (activeTab = 'llm')} title="LLM">
        <Brain />
      </button>
    {/if}
    <button class:active={activeTab === 'gameplay'} on:click={() => (activeTab = 'gameplay')} title="Gameplay">
      <Gamepad />
    </button>
  </div>

  {#if activeTab === 'audio'}
    <div class="panel">
      <div class="control" title="Adjust sound effect volume.">
        <Volume2 />
        <label>SFX Volume</label>
        <input type="range" min="0" max="100" bind:value={sfxVolume} on:input={scheduleSave} />
      </div>
      <div class="control" title="Adjust background music volume.">
        <Music />
        <label>Music Volume</label>
        <input type="range" min="0" max="100" bind:value={musicVolume} on:input={scheduleSave} />
      </div>
      <div class="control" title="Adjust voice volume.">
        <Mic />
        <label>Voice Volume</label>
        <input type="range" min="0" max="100" bind:value={voiceVolume} on:input={scheduleSave} />
      </div>
    </div>
  {:else if activeTab === 'system'}
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
  {:else if activeTab === 'llm' && showLrm}
    <div class="panel">
      <div class="control" title="Select language reasoning model.">
        <label>LRM Model</label>
        <select bind:value={lrmModel} on:change={handleModelChange}>
          {#each lrmOptions as opt}
            <option value={opt}>{opt}</option>
          {/each}
        </select>
      </div>
      <div class="control" title="Send a sample prompt to the selected model.">
        <label>Test Model</label>
        <button on:click={handleTestModel}>Test</button>
      </div>
      {#if testReply}
        <p class="status" data-testid="lrm-test-reply">{testReply}</p>
      {/if}
    </div>
  {:else if activeTab === 'gameplay'}
    <div class="panel">
      <div class="control" title="End the current run.">
        <Power />
        <label>End Run</label>
        <button on:click={handleEndRun} disabled={endingRun}>{endingRun ? 'Ending…' : 'End'}</button>
        {#if endRunStatus}
          <span class="status" data-testid="endrun-status">{endRunStatus}</span>
        {/if}
      </div>
    </div>
  {/if}

  <div class="actions">
    {#if saveStatus}
      <p class="status" data-testid="save-status">{saveStatus}</p>
    {/if}
  </div>
</div>

<style>
  .tabbed {
    min-width: 600px;
    min-height: 360px;
  }

  .tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .tabs button {
    border: 2px solid #fff;
    background: #0a0a0a;
    color: #fff;
    padding: 0.3rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .tabs button.active {
    background: #fff;
    color: #0a0a0a;
  }

  .panel {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .control {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  label {
    flex: 1;
    font-size: 0.85rem;
  }

  input[type='range'] {
    flex: 2;
  }

  select {
    flex: 2;
    background: #0a0a0a;
    color: #fff;
    border: 1px solid #fff;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }

  button {
    border: 2px solid #fff;
    background: #0a0a0a;
    color: #fff;
    padding: 0.3rem 0.6rem;
  }

  .status {
    margin: 0;
    font-size: 0.8rem;
  }

  .badge {
    border: 1px solid rgba(255,255,255,0.6);
    padding: 0.1rem 0.4rem;
    border-radius: 2px;
    font-size: 0.75rem;
  }
  .badge[data-status='healthy'] { color: #00ff88; border-color: #00ff88; }
  .badge[data-status='degraded'] { color: #ffaa00; border-color: #ffaa00; }
  .badge[data-status='error'] { color: #ff4444; border-color: #ff4444; }
  .ping { font-size: 0.75rem; opacity: 0.9; }
</style>
