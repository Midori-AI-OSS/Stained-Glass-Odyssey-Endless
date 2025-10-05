<script>
  import { onMount, onDestroy } from 'svelte';

  export let cue = '';
  export let enabled = false;

  let canvas;
  let context;
  let loaded = new Map();
  let frame;
  let initializing;
  let effekseerApi;
  let mounted = false;

  async function ensureContext() {
    if (!mounted || !enabled || !canvas) return null;
    if (context) return context;
    if (initializing) return initializing;

    initializing = (async () => {
      try {
        if (!effekseerApi) {
          const mod = await import('@zaniar/effekseer-webgl-wasm/effekseer.min.js');
          effekseerApi = mod?.default || mod?.effekseer || globalThis.effekseer;
        }
        if (!effekseerApi) return null;

        await new Promise((resolve, reject) => {
          effekseerApi.initRuntime('/effekseer.wasm', resolve, reject);
        });

        if (!enabled || !mounted) return null;

        const instance = effekseerApi.createContext();
        const gl =
          canvas.getContext('webgl2', { alpha: true, premultipliedAlpha: true }) ||
          canvas.getContext('webgl', { alpha: true, premultipliedAlpha: true }) ||
          canvas.getContext('experimental-webgl');

        if (!gl) {
          instance?.release?.();
          return null;
        }

        if (!enabled || !mounted) {
          instance?.release?.();
          return null;
        }

        instance.init(gl);
        context = instance;
        loop();
        return context;
      } catch {
        return null;
      } finally {
        initializing = null;
      }
    })();

    return initializing;
  }

  function loop() {
    if (context && enabled) {
      try {
        context.update();
        context.draw();
      } catch {
        // ignore draw failures so the loop can continue
      }
      frame = requestAnimationFrame(loop);
    } else {
      frame = null;
    }
  }

  function stopLoop() {
    if (frame) {
      cancelAnimationFrame(frame);
      frame = null;
    }
  }

  function teardown() {
    stopLoop();
    try { context?.stopAll?.(); } catch {}
    try { context?.release?.(); } catch {}
    context = null;
    loaded.clear();
  }

  async function playEffect(name) {
    if (!enabled || !name) return;
    const ctx = await ensureContext();
    if (!enabled || !ctx) return;

    let effect = loaded.get(name);
    if (!effect) {
      try {
        const url = new URL(`../assets/effects/${name}.efkefc`, import.meta.url).href;
        effect = await new Promise((resolve, reject) => {
          const e = ctx.loadEffect(
            url,
            1.0,
            () => resolve(e),
            () => reject(new Error('load failed'))
          );
        });
        loaded.set(name, effect);
      } catch {
        return;
      }
    }

    try {
      ctx.play(effect);
    } catch {
      // ignore playback failures
    }
  }

  onMount(() => {
    mounted = true;
    if (enabled) ensureContext();
    return () => {
      mounted = false;
      teardown();
    };
  });

  onDestroy(() => {
    mounted = false;
    teardown();
  });

  $: if (mounted && enabled) {
    ensureContext();
  }

  $: if (!enabled) {
    teardown();
  }

  $: if (cue) {
    playEffect(cue);
  }
</script>

<canvas bind:this={canvas} class="effect-layer"></canvas>

<style>
  .effect-layer {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }
</style>
