<script>
  import { getRankStyle } from './rankStyles.js';

  export let rank = null;
  export let size = '1.75rem';
  export let className = '';
  export let style = '';

  $: info = getRankStyle(rank);
  $: sizeValue = typeof size === 'number' ? `${size}px` : size;
  $: baseStyle = info ? [`--rank-size: ${sizeValue}`, `--rank-color: ${info.color}`] : [];
  $: combinedStyle = info
    ? [...baseStyle, style].filter(Boolean).join('; ')
    : style;
  $: classes = info
    ? ['rank-badge', `tier-${info.tier}`, info.glitch ? 'is-glitched' : '', info.fallback ? 'is-fallback' : '', info.slug ? `rank-${info.slug}` : '', className]
        .filter(Boolean)
        .join(' ')
    : className;
</script>

{#if info}
  <div
    class={classes}
    style={combinedStyle}
    role="img"
    aria-label={info.label}
    data-rank={info.slug}
    data-rank-tier={info.tier}
    data-rank-fallback={info.fallback ? 'true' : 'false'}
    data-icon={info.icon}
  >
    <span class="badge-ring" aria-hidden="true"></span>
    <span class="badge-core" aria-hidden="true">{info.icon}</span>
    <span class="badge-label" aria-hidden="true">{info.shortLabel}</span>
    <span class="sr-only">{info.label}</span>
  </div>
{/if}

<style>
  .rank-badge {
    --rank-size: 1.75rem;
    --rank-color: #cd7f32;
    position: relative;
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: var(--rank-size);
    height: var(--rank-size);
    border-radius: 999px;
    background: radial-gradient(
      circle at 32% 28%,
      color-mix(in oklab, var(--rank-color) 75%, white 15%) 0%,
      color-mix(in oklab, var(--rank-color) 68%, black 25%) 65%,
      color-mix(in oklab, var(--rank-color) 52%, black 40%) 100%
    );
    border: 2px solid rgba(255, 255, 255, 0.85);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.45);
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #101010;
    padding: calc(var(--rank-size) * 0.08);
    overflow: hidden;
    isolation: isolate;
    z-index: 1;
  }

  .badge-ring {
    position: absolute;
    inset: calc(var(--rank-size) * -0.2);
    border-radius: 50%;
    background: radial-gradient(
      circle,
      rgba(255, 255, 255, 0.4) 0%,
      rgba(255, 255, 255, 0.15) 40%,
      rgba(0, 0, 0, 0) 70%
    );
    opacity: 0.65;
    pointer-events: none;
    mix-blend-mode: screen;
  }

  .badge-core {
    font-size: calc(var(--rank-size) * 0.55);
    line-height: 1;
    z-index: 2;
    text-shadow: 0 1px 2px rgba(255, 255, 255, 0.4);
  }

  .badge-label {
    font-size: calc(var(--rank-size) * 0.28);
    margin-top: calc(var(--rank-size) * -0.05);
    z-index: 2;
    color: color-mix(in oklab, #111 55%, var(--rank-color) 45%);
    text-shadow: 0 1px 2px rgba(255, 255, 255, 0.35);
  }

  .rank-badge.is-fallback {
    background: radial-gradient(
      circle at 32% 28%,
      color-mix(in oklab, var(--rank-color) 82%, white 8%) 0%,
      color-mix(in oklab, var(--rank-color) 60%, black 30%) 70%
    );
  }

  .rank-badge[data-rank-tier='platinum'] {
    color: #161616;
  }

  .rank-badge[data-rank-tier='diamond'] {
    color: #0d1d26;
  }

  .rank-badge.is-glitched::before,
  .rank-badge.is-glitched::after {
    content: attr(data-icon);
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: calc(var(--rank-size) * 0.55);
    opacity: 0.6;
    pointer-events: none;
    mix-blend-mode: screen;
  }

  .rank-badge.is-glitched::before {
    color: #67f3da;
    animation: rank-glitch-1 2.5s infinite;
  }

  .rank-badge.is-glitched::after {
    color: #f16f6f;
    animation: rank-glitch-2 2.5s infinite;
  }

  @keyframes rank-glitch-1 {
    0% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
    7% {
      transform: translate(calc(-50% - 1px), calc(-50% - 1px));
      opacity: 0.7;
    }
    14% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
    44% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
    50% {
      transform: translate(calc(-50% - 1.5px), calc(-50% + 1px));
      opacity: 0.7;
    }
    56% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
    86% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
    92% {
      transform: translate(calc(-50% - 0.5px), calc(-50% - 1.5px));
      opacity: 0.7;
    }
    100% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
  }

  @keyframes rank-glitch-2 {
    0% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
    9% {
      transform: translate(calc(-50% + 1.5px), calc(-50% + 1px));
      opacity: 0.7;
    }
    16% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
    46% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
    52% {
      transform: translate(calc(-50% + 1px), calc(-50% - 0.5px));
      opacity: 0.7;
    }
    58% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
    88% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
    94% {
      transform: translate(calc(-50% + 0.5px), calc(-50% + 1.5px));
      opacity: 0.7;
    }
    100% {
      transform: translate(-50%, -50%);
      opacity: 0.45;
    }
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
</style>
