<script>
  import { Volume2, Music, Mic } from 'lucide-svelte';
  import DotSelector from './DotSelector.svelte';
  export let sfxVolume = 50;
  export let musicVolume = 50;
  export let voiceVolume = 50;
  export let scheduleSave;
</script>

<div class="settings-panel">
  <div class="control" title="Adjust sound effect volume.">
    <span class="label"><Volume2 /> SFX Volume</span>
    <DotSelector bind:value={sfxVolume} on:change={scheduleSave} />
  </div>
  <div class="control" title="Adjust background music volume.">
    <span class="label"><Music /> Music Volume</span>
    <DotSelector bind:value={musicVolume} on:change={scheduleSave} />
  </div>
  <div class="control" title="Adjust voice volume.">
    <span class="label"><Mic /> Voice Volume</span>
    <DotSelector bind:value={voiceVolume} on:change={scheduleSave} />
  </div>
</div>

<style src="./settings-shared.css"></style>
