<script>
  import { Palette, Eye, Move } from 'lucide-svelte';
  import {
    THEMES,
    getThemeSettings,
    getMotionSettings,
    updateThemeSettings,
    updateMotionSettings,
    motionStore,
    themeStore
  } from '../systems/settingsStorage.js';

  export let scheduleSave;
  export let reducedMotion = false;

  let themeSettings = getThemeSettings();
  let motionSettings = getMotionSettings();
  $: themeSettings = $themeStore || themeSettings;
  $: motionSettings = $motionStore || getMotionSettings();

  function updateTheme(updates) {
    themeSettings = { ...themeSettings, ...updates };
    updateThemeSettings(updates);
    scheduleSave();
  }

  function updateMotion(updates) {
    updateMotionSettings(updates);
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

  <div class="control" title="Disable the animated background star storm effect.">
    <div class="control-left">
      <span class="label"><Move /> Disable Star Storm</span>
    </div>
    <div class="control-right">
      <input
        type="checkbox"
        bind:checked={motionSettings.disableStarStorm}
        on:change={(e) => updateMotion({ disableStarStorm: e.target.checked })}
      />
    </div>
  </div>
</div>

<style>
  @import './settings-shared.css';

  input[type='color'] {
    width: 40px;
    height: 32px;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 0;
    cursor: pointer;
    background: transparent;
  }

  input[type='color']:hover {
    border-color: rgba(160, 205, 255, 0.6);
  }
</style>
