<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { Volume2, Cog, Brain, Gamepad } from 'lucide-svelte';
  import { endRun, endAllRuns, wipeData, exportSave, importSave, getLrmConfig, setLrmModel, testLrmModel, getBackendHealth } from '../systems/api.js';
  import AudioSettings from './AudioSettings.svelte';
  import SystemSettings from './SystemSettings.svelte';
  import LLMSettings from './LLMSettings.svelte';
  import GameplaySettings from './GameplaySettings.svelte';
  import { getActiveRuns } from '../systems/uiApi.js';
  import { saveSettings, clearSettings, clearAllClientData } from '../systems/settingsStorage.js';

  const dispatch = createEventDispatcher();
  export let sfxVolume = 5;
  export let musicVolume = 5;
  export let voiceVolume = 5;
  export let framerate = 60;
  export let reducedMotion = false;
  export let showActionValues = false;
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

  let endingRun = false;
  let endRunStatus = '';
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
      reducedMotion,
      showActionValues
    });
    dispatch('save', {
      sfxVolume,
      musicVolume,
      voiceVolume,
      framerate: Number(framerate),
      reducedMotion,
      showActionValues
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
      sfxVolume = 5;
      musicVolume = 5;
      voiceVolume = 5;
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
    <AudioSettings
      bind:sfxVolume
      bind:musicVolume
      bind:voiceVolume
      {scheduleSave}
    />
  {:else if activeTab === 'system'}
    <SystemSettings
      bind:framerate
      bind:reducedMotion
      {scheduleSave}
      {handleWipe}
      {wipeStatus}
      {handleBackup}
      {handleImport}
      {healthStatus}
      {healthPing}
      {refreshHealth}
    />
  {:else if activeTab === 'llm' && showLrm}
    <LLMSettings
      bind:lrmModel
      {lrmOptions}
      {handleModelChange}
      {handleTestModel}
      {testReply}
    />
  {:else if activeTab === 'gameplay'}
    <GameplaySettings
      bind:showActionValues
      {scheduleSave}
      {handleEndRun}
      {endingRun}
      {endRunStatus}
    />
  {/if}

  <div class="actions">
    {#if saveStatus}
      <p class="status" data-testid="save-status">{saveStatus}</p>
    {/if}
  </div>
</div>

<style src="./settings-shared.css"></style>
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

  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }
</style>
