<script>
  import { onDestroy, onMount } from 'svelte';
  import { Clock3, Gift, RefreshCw, Star, Sparkles } from 'lucide-svelte';

  import { claimLoginReward, getLoginRewardStatus } from '$lib/systems/uiApi.js';

  const MAX_VISIBLE_DAYS = 12;
  const MIN_REFRESH_INTERVAL = 5_000;

  let loading = true;
  let refreshing = false;
  let claiming = false;
  let errorMessage = '';
  let status = null;
  let countdownSeconds = 0;
  let countdownTimer = null;
  let pendingAutoRefresh = false;
  let lastFetch = 0;

  function formatCountdown(totalSeconds) {
    const total = Number.isFinite(totalSeconds) ? Math.max(0, Math.floor(totalSeconds)) : 0;
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const seconds = total % 60;
    return [hours, minutes, seconds].map((value) => String(value).padStart(2, '0')).join(':');
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
    const normalized = Math.max(1, Number.isFinite(streak) ? Math.floor(streak) : 1);
    if (normalized <= MAX_VISIBLE_DAYS) {
      return { values: Array.from({ length: normalized }, (_, index) => index + 1), truncated: false };
    }
    const start = normalized - MAX_VISIBLE_DAYS + 1;
    return {
      values: Array.from({ length: MAX_VISIBLE_DAYS }, (_, index) => start + index),
      truncated: true
    };
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
    if (refreshing || claiming) return;
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

  async function handleClaim() {
    if (!status || claiming || status.claimed_today || !status.can_claim) {
      return;
    }
    claiming = true;
    errorMessage = '';
    try {
      await claimLoginReward();
      await loadStatus({ force: true });
    } catch (error) {
      console.error('Failed to claim reward:', error);
      errorMessage = error?.message || 'Failed to claim the reward. Please try again.';
    } finally {
      claiming = false;
    }
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
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    }
  });

  $: if (!loading && !refreshing && !claiming && countdownSeconds === 0 && status && !pendingAutoRefresh) {
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
  $: streak = Math.max(1, Number(status?.streak || 0));
  $: ({ values: streakDays, truncated: streakTruncated } = computeVisibleDays(streak));
  $: resetLabel = formatResetLabel(status?.reset_at);
  $: countdownLabel = formatCountdown(countdownSeconds);
  $: claimDisabled = claiming || !status || status.claimed_today || !status.can_claim;
  $: claimButtonLabel = status
    ? status.claimed_today
      ? 'Reward Claimed'
      : status.can_claim
        ? 'Claim Reward'
        : roomsRemaining === 0
          ? 'Complete a run to unlock'
          : `Clear ${roomsRemaining} more room${roomsRemaining === 1 ? '' : 's'}`
    : 'Claim Reward';
</script>

<div class="login-reward-panel" role="region" aria-live="polite">
  <div class="panel-header">
    <div class="title-group">
      <h2>Daily Login Rewards</h2>
      {#if status}
        <span class="streak-label">Streak {streak} day{streak === 1 ? '' : 's'}</span>
      {/if}
    </div>
      <button class="refresh-btn" on:click={handleRefresh} disabled={refreshing || loading} aria-label="Refresh login rewards">
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
      {#if streakTruncated}
        <div class="chevron placeholder" aria-hidden="true">…</div>
      {/if}
      {#each streakDays as day, index}
        <div
          class="chevron"
          class:claimed={day < streak || (status.claimed_today && day === streak)}
          class:current={day === streak && !status.claimed_today}
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
      {#if !status.can_claim && !status.claimed_today}
        <p class="progress-hint">Clear {roomsRequired} rooms in the current day to unlock the reward bundle.</p>
      {:else if status.claimed_today}
        <p class="progress-hint success">Today's bundle has been delivered to your inventory.</p>
      {/if}
    </div>

    <div class="reward-items" aria-label="Today's reward items">
      {#if status.reward_items && status.reward_items.length > 0}
        {#each status.reward_items as item}
          <div
            class="reward-chip"
            title={`${item?.name || 'Reward'} • ${Math.max(1, Number(item?.stars) || 1)}★ ${String(item?.damage_type || 'Unknown').toUpperCase()}`}
          >
            <div class="reward-stars" aria-hidden="true">
              {#each Array(Math.max(1, Number(item?.stars) || 1)) as _, idx}
                <Star size={12} />
              {/each}
            </div>
            <div class="reward-meta">
              <span class="reward-name">{item?.name || `${item?.stars ?? 1}★ ${item?.damage_type || 'Unknown'}`}</span>
              <span class="reward-type">{(item?.damage_type || '').toUpperCase()} • ID {item?.item_id}</span>
            </div>
          </div>
        {/each}
      {:else}
        <div class="reward-empty">Reward preview unlocks after your first run of the day.</div>
      {/if}
    </div>

    <div class="actions">
      <button class="claim-btn" on:click={handleClaim} disabled={claimDisabled}>
        {#if status.claimed_today}
          <Sparkles size={16} />
        {:else}
          <Gift size={16} />
        {/if}
        <span>{claimButtonLabel}</span>
      </button>
      {#if claiming}
        <div class="claim-status">Claiming reward…</div>
      {/if}
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
    font-size: 1.15rem;
    letter-spacing: 0.02em;
    text-shadow: 0 2px 6px rgba(0, 0, 0, 0.6);
  }

  .streak-label {
    font-size: 0.82rem;
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .refresh-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    border: none;
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
    padding: 0.35rem 0.65rem;
    cursor: pointer;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    transition: background 0.2s ease;
  }

  .refresh-btn:hover:not(:disabled) {
    background: rgba(120, 180, 255, 0.2);
  }

  .refresh-btn:disabled {
    opacity: 0.6;
    cursor: default;
  }

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
    gap: 0.4rem;
    flex-wrap: nowrap;
    overflow: hidden;
  }

  .chevron {
    position: relative;
    min-width: 3rem;
    height: 1.75rem;
    clip-path: polygon(0 0, 82% 0, 100% 50%, 82% 100%, 0 100%);
    background: rgba(255, 255, 255, 0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.78rem;
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.12);
    transition: transform 0.2s ease, background 0.2s ease, border 0.2s ease;
  }

  .chevron.placeholder {
    min-width: 2.2rem;
    clip-path: none;
    background: transparent;
    border: none;
    font-size: 1.1rem;
    opacity: 0.7;
  }

  .chevron.claimed {
    background: linear-gradient(135deg, rgba(120, 255, 200, 0.28), rgba(60, 160, 110, 0.4));
    border-color: rgba(120, 255, 200, 0.4);
  }

  .chevron.current {
    background: linear-gradient(135deg, rgba(255, 200, 120, 0.25), rgba(255, 170, 70, 0.5));
    border-color: rgba(255, 210, 120, 0.8);
    box-shadow: 0 0 12px rgba(255, 190, 90, 0.45);
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
    font-size: 0.82rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
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
    font-size: 0.72rem;
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
    align-items: flex-start;
  }

  .claim-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    border: none;
    background: linear-gradient(135deg, rgba(255, 180, 70, 0.9), rgba(255, 120, 60, 0.9));
    color: #1b0900;
    padding: 0.55rem 1.1rem;
    cursor: pointer;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    box-shadow: 0 6px 12px rgba(255, 120, 60, 0.35);
    transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
  }

  .claim-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 8px 18px rgba(255, 140, 60, 0.45);
  }

  .claim-btn:disabled {
    opacity: 0.55;
    cursor: default;
    box-shadow: none;
  }

  .claim-status {
    font-size: 0.78rem;
    opacity: 0.8;
  }

  @media (max-width: 1024px) {
    .login-reward-panel {
      width: clamp(260px, 88vw, 580px);
      padding: 0.85rem 1rem;
      gap: 0.8rem;
    }

    .chevron {
      min-width: 2.6rem;
      font-size: 0.7rem;
    }

    .reward-items {
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    }
  }

  @media (max-width: 720px) {
    .login-reward-panel {
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
