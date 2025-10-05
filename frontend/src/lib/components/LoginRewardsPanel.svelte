<script>
  import { onDestroy, onMount } from 'svelte';
  import { Clock3, Gift, RefreshCw, Star, Sparkles } from 'lucide-svelte';

  import { getLoginRewardStatus } from '$lib/systems/uiApi.js';

  // When true, renders in an embedded layout suitable for panels
  export let embedded = false;
  // When true (usually alongside embedded), removes outer glass container styling
  export let flat = false;

  const MAX_VISIBLE_DAYS = 5;
  const MIN_REFRESH_INTERVAL = 5_000;

  let loading = true;
  let refreshing = false;
  let errorMessage = '';
  let status = null;
  let countdownSeconds = 0;
  let countdownTimer = null;
  let pendingAutoRefresh = false;
  let lastFetch = 0;
  let autoRefreshTimer = null;

  function getRewardKey(item) {
    if (item && item.item_id != null) {
      return `id:${item.item_id}`;
    }
    const stars = item?.stars ?? 'unknown-stars';
    const damage = item?.damage_type ?? 'unknown-damage';
    const name = item?.name ?? 'unknown-name';
    return `meta:${stars}::${damage}::${name}`;
  }

  function formatCountdown(totalSeconds) {
    const total = Number.isFinite(totalSeconds) ? Math.max(0, Math.floor(totalSeconds)) : 0;
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const seconds = total % 60;
    return [hours, minutes, seconds].map((value) => String(value).padStart(2, '0')).join(':');
  }

  function formatBonusPercent(value) {
    const numeric = Number.isFinite(value) ? Math.max(0, value) : 0;
    const percent = numeric * 100;
    if (percent >= 1000) {
      return percent.toFixed(0);
    }
    if (percent >= 100) {
      return percent.toFixed(1);
    }
    return percent.toFixed(2);
  }


  function formatResetLabel(resetIso) {
    if (!resetIso) return '';
    try {
      const resetAt = new Date(resetIso);
      return resetAt.toLocaleString(undefined, {
        hour: '2-digit',
        minute: '2-digit',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return '';
    }
  }

  function computeVisibleDays(streak) {
    const s = Math.max(1, Number.isFinite(streak) ? Math.floor(streak) : 1);
    const midIndex = Math.floor(MAX_VISIBLE_DAYS / 2); // 2 when MAX_VISIBLE_DAYS=5
    const start = Math.max(1, s - midIndex);
    return Array.from({ length: MAX_VISIBLE_DAYS }, (_, i) => start + i);
  }

  function startCountdown(seconds) {
    if (countdownTimer) {
      clearInterval(countdownTimer);
      countdownTimer = null;
    }
    countdownSeconds = Math.max(0, Number.isFinite(seconds) ? Math.floor(seconds) : 0);
    if (countdownSeconds <= 0) {
      return;
    }
    countdownTimer = setInterval(() => {
      countdownSeconds = Math.max(0, countdownSeconds - 1);
      if (countdownSeconds === 0) {
        clearInterval(countdownTimer);
        countdownTimer = null;
      }
    }, 1000);
  }

  async function loadStatus({ force = false } = {}) {
    if (refreshing) return;
    const now = Date.now();
    if (!force && status && now - lastFetch < MIN_REFRESH_INTERVAL) {
      return;
    }
    if (loading) {
      errorMessage = '';
    } else {
      refreshing = true;
    }
    try {
      const data = await getLoginRewardStatus();
      status = data;
      lastFetch = now;
      countdownSeconds = Math.max(0, Number(data?.seconds_until_reset) || 0);
      startCountdown(countdownSeconds);
      errorMessage = '';
    } catch (error) {
      console.error('Failed to load login rewards:', error);
      errorMessage = error?.message || 'Unable to load daily rewards. Please try again.';
    } finally {
      loading = false;
      refreshing = false;
    }
  }

  async function handleRefresh() {
    await loadStatus({ force: true });
  }

  function handleVisibilityChange() {
    try {
      if (typeof document === 'undefined') return;
      if (!document.hidden) {
        loadStatus({ force: true });
      }
    } catch {}
  }

  onMount(() => {
    loadStatus({ force: true });
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', handleVisibilityChange);
    }
  });

  onDestroy(() => {
    if (countdownTimer) {
      clearInterval(countdownTimer);
      countdownTimer = null;
    }
    if (autoRefreshTimer) {
      clearInterval(autoRefreshTimer);
      autoRefreshTimer = null;
    }
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    }
  });

  $: if (!loading && !refreshing && countdownSeconds === 0 && status && !pendingAutoRefresh) {
    pendingAutoRefresh = true;
    queueMicrotask(async () => {
      try {
        await loadStatus({ force: true });
      } finally {
        pendingAutoRefresh = false;
      }
    });
  }

  $: roomsCompleted = Number(status?.rooms_completed || 0);
  $: roomsRequired = Number(status?.rooms_required || 0);
  $: roomsProgress = roomsRequired > 0 ? Math.min(1, Math.max(0, roomsCompleted / roomsRequired)) : 0;
  $: roomsRemaining = Math.max(0, roomsRequired - roomsCompleted);
  $: roomsOverRequirement = Math.max(0, roomsCompleted - roomsRequired);
  $: shouldAutoPoll = Boolean(status && !status.claimed_today && roomsRemaining <= 1);
  $: {
    if (shouldAutoPoll) {
      if (!autoRefreshTimer) {
        autoRefreshTimer = setInterval(() => {
          loadStatus({ force: true });
        }, MIN_REFRESH_INTERVAL);
      }
    } else if (autoRefreshTimer) {
      clearInterval(autoRefreshTimer);
      autoRefreshTimer = null;
    }
  }
  $: dailyRdrBonus = Math.max(0, Number(status?.daily_rdr_bonus ?? 0));
  $: dailyRdrBonusLabel = formatBonusPercent(dailyRdrBonus);
  $: streak = Math.max(1, Number(status?.streak || 0));
  $: streakDays = computeVisibleDays(streak);
  $: resetLabel = formatResetLabel(status?.reset_at);
  $: countdownLabel = formatCountdown(countdownSeconds);
  $: groupedRewardItems = status?.reward_items?.length
    ? Array.from(
        status.reward_items.reduce((map, item) => {
          const key = getRewardKey(item);
          const rawQuantity = Number(item?.quantity ?? 1);
          const baseQuantity = Number.isFinite(rawQuantity) ? Math.max(1, Math.floor(rawQuantity)) : 1;
          if (map.has(key)) {
            const existing = map.get(key);
            map.set(key, {
              ...existing,
              quantity: existing.quantity + baseQuantity
            });
          } else {
            map.set(key, {
              ...item,
              groupKey: key,
              quantity: baseQuantity
            });
          }
          return map;
        }, new Map())
      )
    : [];
  $: autoDeliveryLabel = status
    ? status.claimed_today
      ? 'Today\'s bundle has been delivered to your inventory.'
      : roomsRemaining > 0
        ? `Clear ${roomsRemaining} more room${roomsRemaining === 1 ? '' : 's'} today for automatic delivery.`
        : 'Delivering bundle…'
    : 'Complete today\'s runs to unlock the automatic bundle.';
</script>

<div class="login-reward-panel" class:embedded class:flat role="region" aria-live="polite">
  <div class="panel-header">
    <div class="title-group">
      <h2>Daily Login Rewards</h2>
      {#if status}
        <span class="streak-label">Streak {streak} day{streak === 1 ? '' : 's'}</span>
      {/if}
    </div>
      <button class="icon-btn refresh-btn" on:click={handleRefresh} disabled={refreshing || loading} aria-label="Refresh login rewards">
        <span class="refresh-icon" class:spinning={refreshing}>
          <RefreshCw size={16} />
        </span>
        <span>Refresh</span>
      </button>
  </div>

  {#if loading}
    <div class="loading">Loading daily rewards…</div>
  {:else if errorMessage}
    <div class="error-banner">{errorMessage}</div>
  {:else if status}
    <div class="streak-track" aria-label={`Current streak ${streak} days`}>
      {#each streakDays as day, index}
        <div
          class="chevron"
          class:claimed={day < streak || (status.claimed_today && day === streak)}
          class:current={day === streak && !status.claimed_today}
          class:future={day > streak}
          aria-current={day === streak && !status.claimed_today ? 'step' : undefined}
        >
          <span>{day}</span>
        </div>
      {/each}
    </div>

    <div class="countdown-row">
      <div class="timer">
        <Clock3 size={16} />
        <span>Resets in {countdownLabel}</span>
      </div>
      {#if resetLabel}
        <span class="reset-label">Next reset {resetLabel} PT</span>
      {/if}
    </div>

    <div class="progress-card">
      <div class="progress-header">
        <span class="progress-title">Rooms Cleared</span>
        <span class="progress-count">{roomsCompleted} / {roomsRequired}</span>
      </div>
      <div class="progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="{roomsRequired}" aria-valuenow="{Math.min(roomsCompleted, roomsRequired)}">
        <div class="progress-fill" style={`width: ${Math.round(roomsProgress * 100)}%`}></div>
      </div>
      {#if !status.claimed_today}
        <p class="progress-hint">Clear {roomsRequired} rooms in the current day to trigger automatic delivery.</p>
      {:else if status.claimed_today}
        <p class="progress-hint success">Today's bundle has been delivered to your inventory.</p>
      {/if}
    </div>

    <div class="bonus-card" aria-label="Daily run drop rate bonus">
      <div class="bonus-header">
        <Sparkles size={14} aria-hidden="true" />
        <span>Run Drop Rate Bonus</span>
      </div>
      <div class="bonus-value" class:positive={dailyRdrBonus > 0} title={`+${dailyRdrBonusLabel}% daily RDR`}>
        +{dailyRdrBonusLabel}%
      </div>
      <p class="bonus-hint">
        {#if dailyRdrBonus > 0}
          Bonus scales with a {streak}-day streak and {roomsOverRequirement} extra room{roomsOverRequirement === 1 ? '' : 's'} cleared today.
        {:else}
          Clear extra rooms after meeting today's goal to start building this bonus.
        {/if}
      </p>
    </div>

    <div class="reward-items" aria-label="Today's reward items">
      {#if groupedRewardItems.length > 0}
        {#each groupedRewardItems as item (item.groupKey)}
          <div
            class="reward-chip"
            title={`${item?.name || 'Reward'} • ${Math.max(1, Number(item?.stars) || 1)}★ ${String(item?.damage_type || 'Unknown').toUpperCase()}${item.quantity > 1 ? ` • ${item.quantity}x` : ''}`}
          >
            <div class="reward-stars" aria-hidden="true">
              {#each Array(Math.max(1, Number(item?.stars) || 1)) as _, idx}
                <Star size={12} />
              {/each}
            </div>
            <div class="reward-meta">
              <span class="reward-name">
                {item?.name || `${item?.stars ?? 1}★ ${item?.damage_type || 'Unknown'}`}
                {#if item.quantity > 1}
                  {' '}
                  ({item.quantity}x)
                {/if}
              </span>
              <span class="reward-type">{(item?.damage_type || '').toUpperCase()} • ID {item?.item_id}</span>
            </div>
          </div>
        {/each}
      {:else}
        <div class="reward-empty">Reward preview unlocks after your first run of the day.</div>
      {/if}
    </div>

    <div class="actions">
      <div class="auto-delivery" class:delivered={status.claimed_today}>
        <Gift size={16} />
        <span>{autoDeliveryLabel}</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .login-reward-panel {
    position: absolute;
    top: calc(var(--ui-top-offset, 0px) + 1.2rem);
    left: 50%;
    transform: translateX(-50%);
    width: clamp(280px, 60vw, 660px);
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
    padding: 1rem 1.2rem;
    display: flex;
    flex-direction: column;
    gap: 0.9rem;
    color: #fff;
    z-index: 10;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }

  /* Embedded variant for use inside side panels */
  .login-reward-panel.embedded {
    /* In embedded mode, force normal document flow and neutral stacking */
    position: static !important;
    top: auto !important;
    left: auto !important;
    transform: none !important;
    width: 100% !important;
    z-index: auto !important;
    margin-top: 0.25rem;
  }

  /* Flat variant removes outer glass container visuals */
  .login-reward-panel.embedded.flat {
    background: transparent;
    box-shadow: none;
    border: none;
    backdrop-filter: none;
    padding: 0;
    padding-top: 0.3rem;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
  }

  .title-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .panel-header h2 {
    margin: 0;
    font-size: 1.1rem; /* match About panel section title */
    letter-spacing: 0.02em;
    text-shadow: 0 2px 6px rgba(0, 0, 0, 0.6);
  }

  .streak-label {
    font-size: 0.78rem; /* slightly smaller meta text */
    opacity: 0.9;
    letter-spacing: 0.04em;
  }

  /* Shared game button style (icon-btn) */
  .icon-btn {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.45rem;
    color: #fff;
    padding: 0.45rem 0.9rem;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    box-shadow: 0 1px 4px 0 rgba(0,40,120,0.10);
    transition: background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
  }
  .icon-btn:hover:not(:disabled) { background: rgba(120,180,255,0.22); border-color: rgba(160,205,255,0.6); box-shadow: 0 2px 8px 0 rgba(0,40,120,0.18); }
  .icon-btn:active:not(:disabled) { transform: translateY(1px); }
  .icon-btn:disabled { opacity: 0.55; cursor: not-allowed; box-shadow: none; }

  .refresh-btn .refresh-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .refresh-btn .refresh-icon.spinning {
    animation: spin 1.2s linear infinite;
  }

  .loading,
  .error-banner {
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 0.8rem;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .error-banner {
    color: #ffbdbd;
    border-color: rgba(255, 140, 140, 0.35);
  }

  .streak-track {
    display: flex;
    align-items: center;
    gap: 0; /* use overlap via adjacent sibling margin */
    width: 100%;
    flex-wrap: nowrap;
    overflow: hidden;
  }

  .chevron {
    position: relative;
    flex: 1 1 0;
    min-width: 0;
    height: 1.75rem;
    clip-path: polygon(0 0, 82% 0, 100% 50%, 82% 100%, 0 100%);
    background: rgba(255, 255, 255, 0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem; /* small but readable inside chevrons */
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.12);
    transition: transform 0.2s ease, background 0.2s ease, border 0.2s ease;
    /* no fixed width; fill row evenly */
    z-index: 2; /* default above claimed */
  }

  /* All chevrons use the same right-pointing shape; overlap handles continuity */

  /* Overlap chevrons slightly; later chevrons render above earlier by DOM order */
  .chevron + .chevron { margin-left: -0.5rem; }
  .chevron > span { pointer-events: none; }

  /* Make the last chevron end flat (no right arrow tip) */
  .streak-track > .chevron:last-child {
    clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%);
  }

  .chevron.placeholder {
    min-width: 2.2rem;
    clip-path: none;
    background: transparent;
    border: none;
    font-size: 1.1rem;
    opacity: 0.7;
    margin-right: 0; /* do not overlap the ellipsis */
  }

  .chevron.claimed {
    background: linear-gradient(135deg, rgba(120, 255, 200, 0.28), rgba(60, 160, 110, 0.4));
    border-color: rgba(120, 255, 200, 0.4);
    z-index: 1; /* stack beneath current/unclaimed */
  }

  .chevron.future {
    /* Desaturated dark red tending toward gray */
    background: #2a1a1a; /* fallback */
    background: color-mix(in srgb, #3a0000 35%, #1a1a1a);
    border-color: #4a2a2a; /* fallback */
    border-color: color-mix(in srgb, #700000 35%, #333333);
    filter: none;
    opacity: 1;
  }

  .chevron.current {
    background: linear-gradient(135deg, rgba(255, 200, 120, 0.85), rgba(255, 170, 70, 0.95));
    border-color: rgba(255, 210, 120, 0.95);
    box-shadow: 0 0 12px rgba(255, 190, 90, 0.45);
    z-index: 3; /* ensure on top */
  }

  .countdown-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.92);
  }

  .timer {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-weight: 600;
  }

  .reset-label {
    opacity: 0.8;
    font-size: 0.78rem;
    letter-spacing: 0.04em;
  }

  .progress-card {
    background: rgba(0, 0, 0, 0.32);
    border: 1px solid rgba(255, 255, 255, 0.14);
    padding: 0.75rem 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.82rem; /* leave slightly smaller than body */
    letter-spacing: 0.05em;
    /* natural case, no forced uppercase */
    text-transform: none;
    font-weight: 600;
    opacity: 0.85;
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    position: relative;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, rgba(80, 180, 255, 0.9), rgba(160, 220, 255, 0.8));
    transition: width 0.3s ease;
  }

  .progress-hint {
    margin: 0;
    font-size: 0.78rem;
    opacity: 0.78;
  }

  .progress-hint.success {
    color: #c0ffda;
    opacity: 1;
  }

  .bonus-card {
    background: rgba(0, 0, 0, 0.32);
    border: 1px solid rgba(255, 255, 255, 0.14);
    padding: 0.75rem 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .bonus-header {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.78rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    opacity: 0.85;
  }

  .bonus-value {
    font-size: 1.25rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    font-variant-numeric: tabular-nums;
  }

  .bonus-value.positive {
    color: #9fe5ff;
  }

  .bonus-hint {
    margin: 0;
    font-size: 0.78rem;
    line-height: 1.3;
    opacity: 0.82;
  }

  .reward-items {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.6rem;
  }

  .reward-chip {
    display: flex;
    gap: 0.5rem;
    padding: 0.5rem 0.6rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    align-items: center;
  }

  .reward-stars {
    display: inline-flex;
    gap: 0.12rem;
    color: #ffd580;
  }

  .reward-meta {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .reward-name {
    font-size: 0.85rem;
    font-weight: 600;
  }

  .reward-type {
    font-size: 0.75rem; /* align with other small meta text */
    opacity: 0.7;
    letter-spacing: 0.06em;
  }

  .reward-empty {
    grid-column: 1 / -1;
    padding: 0.6rem 0.75rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px dashed rgba(255, 255, 255, 0.18);
    font-size: 0.8rem;
    text-align: center;
  }

  .actions {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    align-items: stretch;
  }

  .auto-delivery {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 0.8rem;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.16);
    color: #fff;
    font-size: 0.82rem;
    letter-spacing: 0.02em;
    box-shadow: 0 1px 4px 0 rgba(0, 40, 120, 0.12);
  }

  .auto-delivery span {
    line-height: 1.3;
  }

  .auto-delivery.delivered {
    background: rgba(90, 160, 120, 0.22);
    border-color: rgba(140, 220, 180, 0.45);
    box-shadow: 0 2px 10px rgba(0, 60, 60, 0.25);
  }

  @media (max-width: 1024px) {
    .login-reward-panel {
      width: clamp(260px, 88vw, 580px);
      padding: 0.85rem 1rem;
      gap: 0.8rem;
    }
    .chevron { font-size: 0.7rem; }

    .reward-items {
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    }
  }

  @media (max-width: 720px) {
    .login-reward-panel,
    .login-reward-panel.embedded,
    .login-reward-panel.embedded.flat {
      position: relative;
      transform: none;
      left: auto;
      width: 100%;
      margin: 0 auto;
    }

    .panel-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .refresh-btn {
      align-self: flex-end;
    }
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>
