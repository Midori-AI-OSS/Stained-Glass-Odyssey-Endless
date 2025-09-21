<script>
  import { Activity, Gauge, Move, Trash2, Download, Upload, Palette, Eye } from 'lucide-svelte';
  import { THEMES, getThemeSettings, getMotionSettings, updateThemeSettings, updateMotionSettings } from '../systems/settingsStorage.js';
  
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

  // Theme and motion settings
  let themeSettings = getThemeSettings();
  let motionSettings = getMotionSettings();
  
  $: selectedTheme = THEMES[themeSettings.selected] || THEMES.default;
  
  function updateTheme(updates) {
    themeSettings = { ...themeSettings, ...updates };
    updateThemeSettings(updates);
    scheduleSave();
  }
  
  function updateMotion(updates) {
    motionSettings = { ...motionSettings, ...updates };
    updateMotionSettings(updates);
    // Update legacy reducedMotion for backward compatibility
    scheduleSave({ reducedMotion: motionSettings.globalReducedMotion, ...updates });
  }
</script>

<div class="settings-panel">
  <!-- Theme Settings Section -->
  <div class="section-header">
    <h3><Palette /> Theme</h3>
  </div>
  
  <div class="control" title="Choose a visual theme for the game.">
    <div class="control-left">
      <span class="label">Theme Palette</span>
    </div>
    <div class="control-right">
      <select bind:value={themeSettings.selected} on:change={(e) => updateTheme({ selected: e.target.value })}>
        {#each Object.entries(THEMES) as [key, theme]}
          <option value={key}>{theme.name}</option>
        {/each}
      </select>
    </div>
  </div>
  
  {#if themeSettings.selected === 'custom'}
    <div class="control" title="Custom accent color for the theme.">
      <div class="control-left">
        <span class="label">Custom Accent</span>
      </div>
      <div class="control-right">
        <input 
          type="color" 
          bind:value={themeSettings.customAccent} 
          on:change={(e) => updateTheme({ customAccent: e.target.value })}
        />
      </div>
    </div>
  {/if}
  
  <div class="control" title="How background images are displayed.">
    <div class="control-left">
      <span class="label">Background Mode</span>
    </div>
    <div class="control-right">
      <select bind:value={themeSettings.backgroundBehavior} on:change={(e) => updateTheme({ backgroundBehavior: e.target.value })}>
        <option value="rotating">Hourly Rotation</option>
        <option value="static">Static Pick</option>
        <option value="custom">Custom Asset</option>
      </select>
    </div>
  </div>

  <!-- Motion Settings Section -->
  <div class="section-header">
    <h3><Move /> Motion & Accessibility</h3>
  </div>
  
  <div class="control" title="Master switch for reduced motion. Respects system preferences.">
    <div class="control-left">
      <span class="label">Global Reduced Motion</span>
    </div>
    <div class="control-right">
      <input 
        type="checkbox" 
        bind:checked={motionSettings.globalReducedMotion} 
        on:change={(e) => updateMotion({ globalReducedMotion: e.target.checked })}
      />
    </div>
  </div>
  
  <div class="control" title="Disable floating damage numbers and battle text popups.">
    <div class="control-left">
      <span class="label">Disable Floating Damage</span>
    </div>
    <div class="control-right">
      <input 
        type="checkbox" 
        bind:checked={motionSettings.disableFloatingDamage} 
        on:change={(e) => updateMotion({ disableFloatingDamage: e.target.checked })}
      />
    </div>
  </div>
  
  <div class="control" title="Disable glowing effects around character portraits.">
    <div class="control-left">
      <span class="label">Disable Portrait Glows</span>
    </div>
    <div class="control-right">
      <input 
        type="checkbox" 
        bind:checked={motionSettings.disablePortraitGlows} 
        on:change={(e) => updateMotion({ disablePortraitGlows: e.target.checked })}
      />
    </div>
  </div>
  
  <div class="control" title="Use simpler transitions for overlays and menus.">
    <div class="control-left">
      <span class="label">Simplify Overlay Transitions</span>
    </div>
    <div class="control-right">
      <input 
        type="checkbox" 
        bind:checked={motionSettings.simplifyOverlayTransitions} 
        on:change={(e) => updateMotion({ simplifyOverlayTransitions: e.target.checked })}
      />
    </div>
  </div>
  
  <div class="control" title="Disable the animated background star storm effect.">
    <div class="control-left">
      <span class="label">Disable Star Storm</span>
    </div>
    <div class="control-right">
      <input 
        type="checkbox" 
        bind:checked={motionSettings.disableStarStorm} 
        on:change={(e) => updateMotion({ disableStarStorm: e.target.checked })}
      />
    </div>
  </div>

  <!-- System Settings Section -->
  <div class="section-header">
    <h3><Gauge /> System</h3>
  </div>
  
  <div class="control" title="Backend health and network latency.">
    <div class="control-left">
      <span class="label"><Activity /> Backend Health</span>
    </div>
    <div class="control-right">
      <span class="badge" data-status={healthStatus}>
        {healthStatus === 'healthy'
          ? 'Healthy'
          : healthStatus === 'degraded'
          ? 'Degraded'
          : healthStatus === 'error'
          ? 'Error'
          : 'Unknown'}
      </span>
      {#if healthPing !== null}
        <span class="ping">{Math.round(healthPing)}ms</span>
      {/if}
      <button class="icon-btn" on:click={() => refreshHealth(true)}>Refresh</button>
    </div>
  </div>
  <div class="control" title="Limit server polling frequency.">
    <div class="control-left">
      <span class="label">Framerate</span>
    </div>
    <div class="control-right">
      <select bind:value={framerate} on:change={scheduleSave}>
        <option value={30}>30</option>
        <option value={60}>60</option>
        <option value={120}>120</option>
      </select>
    </div>
  </div>
  
  <!-- Legacy reduced motion for backward compatibility -->
  <div class="control" title="Legacy reduced motion setting (use granular controls above).">
    <div class="control-left">
      <span class="label">Legacy Reduced Motion</span>
    </div>
    <div class="control-right">
      <input type="checkbox" bind:checked={reducedMotion} on:change={scheduleSave} disabled />
      <small>Use granular controls above</small>
    </div>
  </div>
  
  <!-- Data Management Section -->
  <div class="section-header">
    <h3><Trash2 /> Data Management</h3>
  </div>
  
  <div class="control" title="Clear all save data.">
    <div class="control-left">
      <span class="label">Wipe Save Data</span>
    </div>
    <div class="control-right">
      <button class="icon-btn" on:click={handleWipe}>Wipe</button>
    </div>
  </div>
  {#if wipeStatus}
    <p class="status" data-testid="wipe-status">{wipeStatus}</p>
  {/if}
  <div class="control" title="Download encrypted backup of save data.">
    <div class="control-left">
      <span class="label">Backup Save Data</span>
    </div>
    <div class="control-right">
      <button class="icon-btn" on:click={handleBackup}>Backup</button>
    </div>
  </div>
  <div class="control" title="Import an encrypted save backup.">
    <div class="control-left">
      <span class="label">Import Save Data</span>
    </div>
    <div class="control-right">
      <input type="file" accept=".afsave" on:change={handleImport} />
    </div>
  </div>
</div>

<style>
  @import './settings-shared.css';
  
  .section-header {
    margin: 1.5rem 0 0.75rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .section-header:first-child {
    margin-top: 0;
  }
  
  .section-header h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--accent, #8ac);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  small {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.8rem;
    margin-left: 0.5rem;
  }
  
  input[type="color"] {
    width: 40px;
    height: 32px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
</style>
