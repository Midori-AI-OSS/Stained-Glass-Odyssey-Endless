<script>
  import { Volume2, Music, Mic } from 'lucide-svelte';
  import DotSelector from './DotSelector.svelte';
  // Parent uses 0–10 scale; DotSelector uses 0–100. Map between them.
  export let sfxVolume = 5;
  export let musicVolume = 5;
  export let voiceVolume = 5;
  let dotSfx = Math.round(Number(sfxVolume || 0) * 10);
  let dotMusic = Math.round(Number(musicVolume || 0) * 10);
  let dotVoice = Math.round(Number(voiceVolume || 0) * 10);
  $: { const v = Math.round(Number(sfxVolume || 0) * 10); if (v !== dotSfx) dotSfx = v; }
  $: { const v = Math.round(Number(musicVolume || 0) * 10); if (v !== dotMusic) dotMusic = v; }
  $: { const v = Math.round(Number(voiceVolume || 0) * 10); if (v !== dotVoice) dotVoice = v; }
  export let scheduleSave;
</script>

<div class="settings-panel">
  <div class="control" title="Adjust sound effect volume.">
    <span class="label"><Volume2 /> SFX Volume</span>
    <div class="control-right">
      <DotSelector bind:value={dotSfx} on:change={() => { sfxVolume = Math.round(dotSfx / 10); scheduleSave(); }} />
    </div>
  </div>
  <div class="control" title="Adjust background music volume.">
    <span class="label"><Music /> Music Volume</span>
    <div class="control-right">
      <DotSelector bind:value={dotMusic} on:change={() => { musicVolume = Math.round(dotMusic / 10); scheduleSave(); }} />
    </div>
  </div>
  <div class="control" title="Adjust voice volume.">
    <span class="label"><Mic /> Voice Volume</span>
    <div class="control-right">
      <DotSelector bind:value={dotVoice} on:change={() => { voiceVolume = Math.round(dotVoice / 10); scheduleSave(); }} />
    </div>
  </div>
</div>

<style src="./settings-shared.css"></style>
