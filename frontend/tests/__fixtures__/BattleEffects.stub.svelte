<script>
  export let cue = '';
  let lastCue = '';
  $: {
    if (cue && String(cue).trim()) {
      lastCue = cue;
    }
  }
</script>

<div data-testid="effects-probe" data-cue={cue ?? ''} data-last-cue={lastCue}></div>
