<script>
  import { Activity, Gauge, Move, Trash2, Download, Upload, Palette, Eye } from 'lucide-svelte';
  import { THEMES, getThemeSettings, getMotionSettings, updateThemeSettings, updateMotionSettings, motionStore } from '../systems/settingsStorage.js';
  
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

  // Theme and motion settings - use stores for reactivity
  let themeSettings = getThemeSettings();
  $: motionSettings = $motionStore || getMotionSettings();
  
  $: selectedTheme = THEMES[themeSettings.selected] || THEMES.default;
  
  function updateTheme(updates) {
    themeSettings = { ...themeSettings, ...updates };
    updateThemeSettings(updates);
    scheduleSave();
  }
  
  function updateMotion(updates) {
    updateMotionSettings(updates);
    
    // Update legacy reducedMotion for backward compatibility
    reducedMotion = (motionSettings?.globalReducedMotion ?? false) || (updates.globalReducedMotion ?? false);
    scheduleSave({ reducedMotion, ...updates });
  }
</script>

<div class="settings-panel">
  <div class="control" title="Choose a visual theme for the game.">
    <div class="control-left">
      <span class="label"><Palette /> Theme Palette</span>
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
        <span class="label"><Eye /> Custom Accent</span>
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
      <span class="label"><Eye /> Background Mode</span>
    </div>
    <div class="control-right">
      <select bind:value={themeSettings.backgroundBehavior} on:change={(e) => updateTheme({ backgroundBehavior: e.target.value })}>
        <option value="rotating">Hourly Rotation</option>
        <option value="static">Static Pick</option>
        <option value="custom">Custom Asset</option>
      </select>
    </div>
  </div>

  {#if themeSettings.backgroundBehavior === 'static'}
    <div class="control" title="Choose a static background image.">
      <div class="control-left">
        <span class="label"><Eye /> Static Background</span>
      </div>
      <div class="control-right">
        <select bind:value={themeSettings.customBackground} on:change={(e) => updateTheme({ customBackground: e.target.value })}>
          <option value="">Default</option>
          <option value="/src/lib/assets/backgrounds/1bd68c8e-5053-48f8-8464-0873942ef5dc.png">Cityscape 1</option>
          <option value="/src/lib/assets/backgrounds/31158efc-ab69-40a4-87aa-8fbaab3084d4.png">Cityscape 2</option>
          <option value="/src/lib/assets/backgrounds/442c486c-fcdb-4a85-80c8-c1a4dc2792c4.png">Cityscape 3</option>
          <option value="/src/lib/assets/backgrounds/57bb288c-8dbc-4656-9132-c188b55f1d6b.png">Cityscape 4</option>
        </select>
      </div>
    </div>
  {/if}

  {#if themeSettings.backgroundBehavior === 'custom'}
    <div class="control" title="Upload a custom background image.">
      <div class="control-left">
        <span class="label"><Eye /> Custom Background</span>
      </div>
      <div class="control-right">
        <input 
          type="file" 
          accept="image/*" 
          on:change={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              const reader = new FileReader();
              reader.onload = (e) => {
                updateTheme({ customBackground: e.target.result });
              };
              reader.readAsDataURL(file);
            }
          }}
        />
      </div>
    </div>
  {/if}

  <div class="control" title="Master switch for reduced motion. Respects system preferences.">
    <div class="control-left">
      <span class="label"><Move /> Global Reduced Motion</span>
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
      <span class="label"><Move /> Disable Floating Damage</span>
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
      <span class="label"><Move /> Disable Portrait Glows</span>
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
      <span class="label"><Move /> Simplify Overlay Transitions</span>
    </div>
    <div class="control-right">
      <input 
        type="checkbox" 
        bind:checked={motionSettings.simplifyOverlayTransitions} 
        on:change={(e) => updateMotion({ simplifyOverlayTransitions: e.target.checked })}
      />
    </div>
  </div>
  
  <div class="control" title="Disable the animated background element orbs effect.">
    <div class="control-left">
      <span class="label"><Move /> Disable Element Orbs</span>
    </div>
    <div class="control-right">
      <input 
        type="checkbox" 
        bind:checked={motionSettings.disableStarStorm} 
        on:change={(e) => updateMotion({ disableStarStorm: e.target.checked })}
      />
    </div>
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
      <span class="label"><Gauge /> Framerate</span>
    </div>
    <div class="control-right">
      <select bind:value={framerate} on:change={scheduleSave}>
        <option value={30}>30</option>
        <option value={60}>60</option>
        <option value={120}>120</option>
      </select>
    </div>
  </div>
  
  <div class="control" title="Legacy reduced motion setting (use granular controls above).">
    <div class="control-left">
      <span class="label"><Move /> Reduced Motion</span>
    </div>
    <div class="control-right">
      <input type="checkbox" bind:checked={reducedMotion} on:change={scheduleSave} disabled />
      <span class="value">Use controls above</span>
    </div>
  </div>
  
  <div class="control" title="Clear all save data.">
    <div class="control-left">
      <span class="label"><Trash2 /> Wipe Save Data</span>
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
      <span class="label"><Download /> Backup Save Data</span>
    </div>
    <div class="control-right">
      <button class="icon-btn" on:click={handleBackup}>Backup</button>
    </div>
  </div>
  <div class="control" title="Import an encrypted save backup.">
    <div class="control-left">
      <span class="label"><Upload /> Import Save Data</span>
    </div>
    <div class="control-right">
      <input type="file" accept=".afsave" on:change={handleImport} />
    </div>
  </div>
</div>

<style>
  @import './settings-shared.css';
  
  input[type="color"] {
    width: 40px;
    height: 32px;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 0;
    cursor: pointer;
    background: transparent;
  }
  
  input[type="color"]:hover {
    border-color: rgba(160, 205, 255, 0.6);
  }
</style>
