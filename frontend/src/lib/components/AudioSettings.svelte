<script>
  import { Volume2, Music, Mic } from 'lucide-svelte';
  export let sfxVolume = 5;
  export let musicVolume = 5;
  export let voiceVolume = 5;
  export let scheduleSave;
</script>

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

<style src="./settings-shared.css"></style>
