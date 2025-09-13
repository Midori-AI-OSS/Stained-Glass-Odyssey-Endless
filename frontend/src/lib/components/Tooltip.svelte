<script>
  export let text = '';
  let show = false;
</script>

<div
  class="tooltip-wrapper"
  on:mouseenter={() => (show = true)}
  on:mouseleave={() => (show = false)}
  on:focusin={() => (show = true)}
  on:focusout={() => (show = false)}
>
  <slot />
  <span class="tooltip" role="tooltip" class:visible={show}>{text}</span>
</div>

<style src="./settings-shared.css"></style>
