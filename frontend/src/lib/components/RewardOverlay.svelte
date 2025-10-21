<script>
  import { createEventDispatcher, onDestroy, onMount } from 'svelte';
  import { cubicOut } from 'svelte/easing';
  import { scale } from 'svelte/transition';
  import RewardCard from './RewardCard.svelte';
  import CurioChoice from './CurioChoice.svelte';
  import { getMaterialIcon, onMaterialIconError } from '../systems/assetLoader.js';
  import { createRewardDropSfx } from '../systems/sfx.js';
  import { formatRewardPreview } from '../utils/rewardPreviewFormatter.js';
  import {
    rewardPhaseState,
    rewardPhaseController,
    advanceRewardPhase
  } from '../systems/overlayState.js';
  import { warn as logWarn } from '../systems/logger.js';
  import { emitRewardTelemetry } from '../systems/rewardTelemetry.js';

  export let cards = [];
  export let relics = [];
  export let items = [];
  export let gold = 0;
  export let partyStats = [];
  export let ended = false;
  export let nextRoom = '';
  export let fullIdleMode = false;
  export let sfxVolume = 5;
  export let reducedMotion = false;
  export let stagedCards = [];
  export let stagedRelics = [];
  export let awaitingCard = false;
  export let awaitingRelic = false;
  export let awaitingLoot = false;
  export let awaitingNext = false;

  const dispatch = createEventDispatcher();

  const DEFAULT_PHASE_SEQUENCE = ['drops', 'cards', 'relics', 'battle_review'];
  const PHASE_LABELS = {
    drops: 'Drops',
    cards: 'Cards',
    relics: 'Relics',
    battle_review: 'Battle Review'
  };
  const DROPS_COMPLETE_EVENT = 'drops-complete';

  const phaseListenerDisposers = [];
  let overlayRootEl = null;
  let advanceButtonEl = null;
  let phaseAnnouncement = '';
  let countdownAnnouncement = '';
  let lastAnnouncedPhase = null;
  let fallbackLogSignature = null;
  let lastAdvanceFocusable = false;

  onMount(() => {
    const exitDisposer = rewardPhaseController.on('exit', (detail) => {
      if (!detail || detail.phase !== 'drops') {
        return;
      }
      emitRewardTelemetry(DROPS_COMPLETE_EVENT, {
        from: detail.phase,
        to: detail.to ?? null,
        reason: detail.reason ?? 'exit',
        next: detail.snapshot?.current ?? null,
        sequence: Array.isArray(detail.snapshot?.sequence) ? detail.snapshot.sequence.slice() : []
      });
    });
    if (typeof exitDisposer === 'function') {
      phaseListenerDisposers.push(exitDisposer);
    }
  });

  // Render immediately; CSS animations handle reveal on mount

  $: normalizedSfxVolume = (() => {
    const value = Number(sfxVolume);
    if (!Number.isFinite(value)) return 5;
    if (value < 0) return 0;
    if (value > 10) return 10;
    return value;
  })();
  $: iconQuiet = Boolean(reducedMotion || normalizedSfxVolume <= 0);
  $: revealDelay = (index) => (reducedMotion ? 0 : index * 120);
  $: lootItems = Array.isArray(items) ? items : [];
  $: hasLootItems = lootItems.length > 0;
  $: dataReducedMotion = reducedMotion ? 'true' : 'false';
  $: dataSfxVolume = String(normalizedSfxVolume);
  $: phaseSnapshot = $rewardPhaseState;
  $: rawPhaseSequence =
    Array.isArray(phaseSnapshot?.sequence) && phaseSnapshot.sequence.length > 0
      ? phaseSnapshot.sequence
      : [];
  $: phaseSequence = rawPhaseSequence.length > 0 ? rawPhaseSequence : DEFAULT_PHASE_SEQUENCE;
  $: completedPhaseSet = new Set(Array.isArray(phaseSnapshot?.completed) ? phaseSnapshot.completed : []);
  $: currentPhase = phaseSnapshot?.current ?? null;
  $: nextPhase = phaseSnapshot?.next ?? null;
  $: phaseDiagnostics = Array.isArray(phaseSnapshot?.diagnostics) ? phaseSnapshot.diagnostics : [];
  $: fallbackActive =
    rawPhaseSequence.length === 0 || !currentPhase || (phaseDiagnostics?.length ?? 0) > 0;
  $: dropsPhaseActive = !fallbackActive && currentPhase === 'drops';
  $: showDropsSection = fallbackActive
    ? hasLootItems || awaitingLoot || gold > 0
    : dropsPhaseActive && (hasLootItems || awaitingLoot || gold > 0);
  $: nonDropContentHidden = fallbackActive ? false : dropsPhaseActive;
  $: phaseEntries = phaseSequence.map((phase, index) => {
    const resolvedLabel = PHASE_LABELS[phase] ?? phase.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    const isCurrent = !fallbackActive && phase === currentPhase;
    const status = fallbackActive
      ? 'legacy'
      : completedPhaseSet.has(phase)
        ? 'completed'
        : isCurrent
          ? 'current'
          : 'upcoming';
    return {
      phase,
      index: index + 1,
      label: resolvedLabel,
      status,
      isCurrent
    };
  });
  $: nextPhaseLabel = !fallbackActive && nextPhase
    ? PHASE_LABELS[nextPhase] ?? nextPhase.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    : '';
  $: fallbackPhaseMessage = fallbackActive
    ? 'Reward phases unavailable. Showing legacy overlay.'
    : '';

  const ADVANCE_COUNTDOWN_SECONDS = 10;
  let advanceCountdownSeconds = ADVANCE_COUNTDOWN_SECONDS;
  let advanceCountdownTimer = null;
  let advanceCountdownContext = null;
  let advanceCountdownDeadline = 0;
  let advanceInFlight = false;

  $: advanceCountdownLabel = formatCountdown(advanceCountdownSeconds);
  $: showAdvancePanel = !fallbackActive && Boolean(currentPhase && nextPhase);
  $: phaseAdvanceAvailable = !fallbackActive && computeAdvanceAvailability(currentPhase, nextPhase);
  $: advanceButtonDisabled = !phaseAdvanceAvailable || advanceInFlight || fallbackActive;
  $: advanceCountdownActive = Boolean(advanceCountdownTimer) && phaseAdvanceAvailable;
  $: advanceStatusMessage = (() => {
    if (!showAdvancePanel) return '';
    if (!phaseAdvanceAvailable) {
      return 'Advance locked until this phase is complete.';
    }
    if (advanceCountdownActive) {
      return `Advance ready. Auto in ${advanceCountdownLabel}.`;
    }
    return 'Advance ready.';
  })();
  $: countdownAnnouncement = showAdvancePanel ? advanceStatusMessage : '';

  $: {
    if (fallbackActive) {
      lastAnnouncedPhase = null;
      phaseAnnouncement = fallbackPhaseMessage;
    } else if (currentPhase && currentPhase !== lastAnnouncedPhase) {
      const label = PHASE_LABELS[currentPhase] ?? currentPhase.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
      const nextLabel = nextPhaseLabel || '';
      phaseAnnouncement = nextLabel
        ? `Entered ${label} phase. Next: ${nextLabel}.`
        : `Entered ${label} phase. Final reward step.`;
      lastAnnouncedPhase = currentPhase;
    }
  }

  $: {
    if (fallbackActive) {
      const signature = JSON.stringify({
        diagnostics: phaseDiagnostics,
        currentPhase,
        sequence: rawPhaseSequence
      });
      if (signature !== fallbackLogSignature) {
        fallbackLogSignature = signature;
        logWarn('RewardOverlay: reward progression invalid, falling back to legacy overlay', {
          diagnostics: phaseDiagnostics,
          snapshot: phaseSnapshot ?? null
        });
      }
    } else {
      fallbackLogSignature = null;
    }
  }

  $: {
    const focusable =
      !fallbackActive &&
      showAdvancePanel &&
      phaseAdvanceAvailable &&
      !advanceButtonDisabled &&
      advanceButtonEl != null;
    if (focusable && !lastAdvanceFocusable) {
      queueMicrotask(() => {
        if (!advanceButtonEl) return;
        if (document.activeElement !== advanceButtonEl) {
          advanceButtonEl.focus();
        }
      });
    }
    if (!focusable && lastAdvanceFocusable) {
      queueMicrotask(() => {
        if (advanceButtonEl && document.activeElement === advanceButtonEl && overlayRootEl) {
          overlayRootEl.focus();
        }
      });
    }
    lastAdvanceFocusable = focusable;
  }

  $: {
    if (showAdvancePanel && phaseAdvanceAvailable && currentPhase && nextPhase && !advanceInFlight) {
      ensureAdvanceCountdown(currentPhase, nextPhase);
    } else {
      resetAdvanceCountdown(true);
    }
  }

  function titleForItem(item) {
    if (!item) return '';
    const uiMeta = item.ui && typeof item.ui === 'object' ? item.ui : null;
    if (uiMeta) {
      const label = uiMeta.label || uiMeta.title;
      if (label) return label;
    }
    if (item.name) return item.name;
    const id = String(item.id || '').toLowerCase();
    const cap = id.charAt(0).toUpperCase() + id.slice(1);
    const stars = Number.isFinite(item.stars) ? String(item.stars) : '';
    return stars ? `${cap} Upgrade (${stars})` : `${cap} Upgrade`;
  }

  const starColors = {
    1: '#808080',
    2: '#1E90FF',
    3: '#228B22',
    4: '#800080',
    5: '#FF3B30',
    6: '#FFD700',
    fallback: '#708090'
  };

  function sanitizeStars(value) {
    const num = Number(value);
    if (!Number.isFinite(num) || num <= 0) return 1;
    return Math.min(Math.round(num), 6);
  }

  function accentForItem(item) {
    if (String(item?.id || '') === 'ticket') {
      return starColors.fallback;
    }
    const stars = sanitizeStars(item?.stars);
    return starColors[stars] || starColors.fallback;
  }

  function materialKeyForItem(item) {
    const id = String(item?.id || '').trim();
    if (!id) return '';
    if (id === 'ticket') return 'ticket';
    const rawStars = Number(item?.stars);
    if (!Number.isFinite(rawStars) || rawStars <= 0) {
      return id;
    }
    const stars = sanitizeStars(rawStars);
    return `${id}_${stars}`;
  }

  function stackFromItem(item) {
    if (!item || typeof item !== 'object') return 1;
    const candidates = ['count', 'quantity', 'qty', 'amount'];
    for (const key of candidates) {
      if (key in item) {
        const value = Number(item[key]);
        if (Number.isFinite(value) && value > 0) {
          return Math.max(1, Math.floor(value));
        }
      }
    }
    if (typeof item.stacks === 'number' && Number.isFinite(item.stacks)) {
      const stacks = Number(item.stacks);
      if (stacks > 0) return Math.floor(stacks);
    }
    return 1;
  }

  function rewardEntryKey(entry, index, prefix = 'reward') {
    if (!entry || typeof entry !== 'object') {
      return `${prefix}-${index}`;
    }
    if (entry.id != null && entry.id !== '') {
      return String(entry.id);
    }
    if (entry.slug != null && entry.slug !== '') {
      return String(entry.slug);
    }
    if (entry.key != null && entry.key !== '') {
      return String(entry.key);
    }
    return `${prefix}-${index}`;
  }

  function selectionKeyFromDetail(detail, fallbackPrefix = 'reward') {
    if (!detail || typeof detail !== 'object') return null;
    if (detail.key != null) return String(detail.key);
    if (detail.id != null) return String(detail.id);
    if (detail.entry) {
      return rewardEntryKey(detail.entry, 0, fallbackPrefix);
    }
    return null;
  }

  $: dropEntries = (() => {
    if (!hasLootItems) return [];
    const grouped = [];
    const seen = new Map();
    let fallbackIndex = 0;
    for (const item of lootItems) {
      if (!item || typeof item !== 'object') continue;
      const baseKey = materialKeyForItem(item);
      const groupKey = baseKey || `fallback-${fallbackIndex++}`;
      const iconKey = baseKey || String(item.id || '');
      const count = stackFromItem(item);
      const label = titleForItem(item);
      const accent = accentForItem(item);
      const existing = seen.get(groupKey);
      if (existing) {
        existing.count += count;
        if (label) existing.label = label;
        continue;
      }
      const safeLabel = label || (iconKey ? iconKey.replace(/_/g, ' ') : 'Loot item');
      const entry = {
        key: `drop-${groupKey}`,
        icon: getMaterialIcon(iconKey),
        label: safeLabel,
        count,
        accent
      };
      seen.set(groupKey, entry);
      grouped.push(entry);
    }
    return grouped;
  })();

  const DROP_REVEAL_INTERVAL_MS = 220;
  let visibleDrops = [];
  let dropRevealTimers = [];
  let dropRevealGeneration = 0;
  let dropSfxPlayer = null;
  let dropPopTransition = null;
  let lastDropSignature = null;
  let lastReducedMotion = null;
  let lootSfxEnabled = true;
  let lootSfxBlocked = false;
  let lootSfxNoticeLogged = false;

  $: dropPopTransition = reducedMotion
    ? null
    : { duration: 180, easing: cubicOut, start: 0.75 };

  function clearDropRevealTimers() {
    if (dropRevealTimers.length === 0) return;
    for (const timer of dropRevealTimers) {
      clearTimeout(timer);
    }
    dropRevealTimers = [];
  }

  function stopDropAudio(release = false) {
    if (!dropSfxPlayer) return;
    try {
      dropSfxPlayer.stop?.();
    } catch {
      // ignore playback reset failures
    }
    if (release) {
      dropSfxPlayer = null;
    }
  }

  function playRewardDropAudio() {
    if (!lootSfxEnabled || lootSfxBlocked) return;
    if (reducedMotion) return;
    if (normalizedSfxVolume <= 0) {
      stopDropAudio(true);
      return;
    }
    if (!dropSfxPlayer) {
      dropSfxPlayer = createRewardDropSfx(normalizedSfxVolume, { reducedMotion });
    }
    if (!dropSfxPlayer || typeof dropSfxPlayer.play !== 'function') return;
    if (typeof dropSfxPlayer.setVolume === 'function') {
      dropSfxPlayer.setVolume(normalizedSfxVolume);
    }
    const playPromise = dropSfxPlayer.play();
    if (playPromise && typeof playPromise.catch === 'function') {
      playPromise.catch((error) => {
        if (error?.name === 'NotAllowedError') {
          lootSfxEnabled = false;
          lootSfxBlocked = true;
          if (!lootSfxNoticeLogged) {
            console.info('Reward drop audio blocked until user interaction enables playback.');
            lootSfxNoticeLogged = true;
          }
        }
      });
    }
  }

  function handleLootSfxGesture() {
    const wasBlocked = lootSfxBlocked;
    if (lootSfxBlocked) {
      lootSfxBlocked = false;
    }
    lootSfxEnabled = true;
    lootSfxNoticeLogged = false;
    if (dropSfxPlayer && typeof dropSfxPlayer.setVolume === 'function') {
      dropSfxPlayer.setVolume(normalizedSfxVolume);
    }
    if (wasBlocked && visibleDrops.length > 0) {
      playRewardDropAudio();
    }
  }

  function updateDropSequence(entries, motionReduced) {
    dropRevealGeneration += 1;
    const generation = dropRevealGeneration;
    clearDropRevealTimers();
    if (!Array.isArray(entries) || entries.length === 0) {
      visibleDrops = [];
      stopDropAudio(true);
      return;
    }
    if (motionReduced) {
      stopDropAudio(true);
      visibleDrops = entries;
      return;
    }
    stopDropAudio();
    visibleDrops = [];
    entries.forEach((_, index) => {
      const timer = setTimeout(() => {
        if (generation !== dropRevealGeneration) return;
        visibleDrops = entries.slice(0, index + 1);
        playRewardDropAudio();
      }, index * DROP_REVEAL_INTERVAL_MS);
      dropRevealTimers.push(timer);
    });
  }

  function snapshotDropSignature(entries) {
    if (!Array.isArray(entries) || entries.length === 0) {
      return [];
    }
    return entries.map((entry) => ({
      key: String(entry?.key ?? ''),
      count: Number.isFinite(entry?.count) ? entry.count : 0
    }));
  }

  function dropSignaturesEqual(a, b) {
    if (!Array.isArray(a) || !Array.isArray(b)) return false;
    if (a.length !== b.length) return false;
    for (let index = 0; index < a.length; index += 1) {
      const current = a[index];
      const other = b[index];
      if (!other || current.key !== other.key || current.count !== other.count) {
        return false;
      }
    }
    return true;
  }

  function formatCountdown(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric) || numeric <= 0) {
      return '00:00';
    }
    const clamped = Math.max(0, Math.floor(numeric));
    const minutes = Math.floor(clamped / 60);
    const seconds = clamped % 60;
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  }

  function computeAdvanceAvailability(current, target) {
    if (!current || !target) return false;
    if (advanceInFlight) return false;
    if (awaitingConfirmation) return false;
    switch (current) {
      case 'drops':
        return true;
      case 'cards':
        if (!Array.isArray(cardChoices)) return false;
        if (awaitingCard) return false;
        if (Array.isArray(cardChoices) && cardChoices.length > 0) return false;
        if (Array.isArray(stagedCardEntries) && stagedCardEntries.length > 0) return false;
        return true;
      case 'relics':
        if (!Array.isArray(relicChoices)) return false;
        if (awaitingRelic) return false;
        if (Array.isArray(relicChoices) && relicChoices.length > 0) return false;
        if (Array.isArray(stagedRelicEntries) && stagedRelicEntries.length > 0) return false;
        return true;
      default:
        return false;
    }
  }

  function ensureAdvanceCountdown(phase, target) {
    const context = `${phase}->${target}`;
    if (advanceCountdownTimer && advanceCountdownContext === context) {
      return;
    }
    resetAdvanceCountdown(false);
    advanceCountdownContext = context;
    advanceCountdownSeconds = ADVANCE_COUNTDOWN_SECONDS;
    advanceCountdownDeadline = Date.now() + ADVANCE_COUNTDOWN_SECONDS * 1000;
    advanceCountdownTimer = setInterval(syncAdvanceCountdown, 250);
    syncAdvanceCountdown();
  }

  function resetAdvanceCountdown(resetValue = true) {
    if (advanceCountdownTimer) {
      clearInterval(advanceCountdownTimer);
      advanceCountdownTimer = null;
    }
    advanceCountdownContext = null;
    advanceCountdownDeadline = 0;
    if (resetValue) {
      advanceCountdownSeconds = ADVANCE_COUNTDOWN_SECONDS;
    }
  }

  function syncAdvanceCountdown() {
    if (!advanceCountdownTimer) return;
    const remainingMs = Math.max(0, advanceCountdownDeadline - Date.now());
    const remainingSeconds = Math.max(0, Math.ceil(remainingMs / 1000));
    if (remainingSeconds !== advanceCountdownSeconds) {
      advanceCountdownSeconds = remainingSeconds;
    }
    if (remainingSeconds <= 0) {
      resetAdvanceCountdown(false);
      triggerAdvance('auto');
    }
  }

  function triggerAdvance(reason) {
    if (!phaseAdvanceAvailable || advanceInFlight || fallbackActive) return;
    const snapshot =
      typeof rewardPhaseController?.getSnapshot === 'function'
        ? rewardPhaseController.getSnapshot()
        : phaseSnapshot;
    const fromPhase = snapshot?.current ?? currentPhase;
    const targetPhase = snapshot?.next ?? nextPhase;
    if (!fromPhase || !targetPhase) return;

    advanceInFlight = true;
    resetAdvanceCountdown(false);
    advanceCountdownSeconds = ADVANCE_COUNTDOWN_SECONDS;

    let nextSnapshot = null;
    try {
      nextSnapshot = advanceRewardPhase();
    } finally {
      advanceInFlight = false;
    }

    dispatch('advance', {
      reason,
      from: fromPhase,
      to: nextSnapshot?.current ?? null,
      target: targetPhase,
      snapshot: nextSnapshot ?? null
    });

    if (reason === 'auto' && overlayRootEl) {
      queueMicrotask(() => {
        overlayRootEl?.focus?.();
      });
    }
  }

  function handleAdvanceClick() {
    if (!phaseAdvanceAvailable || advanceInFlight) return;
    triggerAdvance('manual');
  }

  function handleLayoutKeydown(event) {
    handleLootSfxGesture(event);
    if (event.defaultPrevented) return;
    if (!overlayRootEl || event.target !== overlayRootEl) return;
    if (!phaseAdvanceAvailable || advanceButtonDisabled) return;
    if (fallbackActive) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      triggerAdvance('keyboard');
    }
  }

  $: {
    const nextSignature = snapshotDropSignature(dropEntries);
    const unchangedSignature =
      Array.isArray(lastDropSignature) && dropSignaturesEqual(lastDropSignature, nextSignature);
    const motionUnchanged = lastReducedMotion === reducedMotion;
    if (!(unchangedSignature && motionUnchanged)) {
      updateDropSequence(dropEntries, reducedMotion);
      lastDropSignature = nextSignature;
      lastReducedMotion = reducedMotion;
    }
  }

  function normalizeRewardEntries(list) {
    if (!Array.isArray(list)) return [];
    return list
      .filter((entry) => entry != null)
      .map((entry) => (entry && typeof entry === 'object' ? { ...entry } : { id: entry }));
  }

  $: cardChoices = Array.isArray(cards) ? cards : [];
  $: cardChoiceEntries = cardChoices.map((card, index) => ({
    entry: card,
    key: rewardEntryKey(card, index, 'card')
  }));
  $: relicChoices = Array.isArray(relics) ? relics : [];
  $: relicChoiceEntries = relicChoices.map((relic, index) => ({
    entry: relic,
    key: rewardEntryKey(relic, index, 'relic')
  }));
  $: stagedCardEntries = normalizeRewardEntries(stagedCards);
  $: stagedRelicEntries = normalizeRewardEntries(stagedRelics);

  const PREVIEW_LIMIT = 3;
  $: stagedCardPreviewDetails = stagedCardEntries
    .slice(0, PREVIEW_LIMIT)
    .map((entry, index) => {
      const name = entry?.name || entry?.id || 'Card';
      const preview = formatRewardPreview(entry?.preview, {
        fallbackSummary: entry?.about || entry?.tooltip || ''
      });
      return {
        key: entry?.id ?? `staged-card-preview-${index}`,
        name,
        preview
      };
    })
    .filter((entry) => entry.preview?.hasContent);

  $: stagedRelicPreviewDetails = stagedRelicEntries
    .slice(0, PREVIEW_LIMIT)
    .map((entry, index) => {
      const name = entry?.name || entry?.id || 'Relic';
      const preview = formatRewardPreview(entry?.preview, {
        fallbackSummary: entry?.about || ''
      });
      return {
        key: entry?.id ?? `staged-relic-preview-${index}`,
        name,
        preview
      };
    })
    .filter((entry) => entry.preview?.hasContent);

  let pendingCardSelection = null;
  let pendingRelicSelection = null;
  let pendingCardConfirm = null;
  let pendingCardCancel = null;
  let pendingRelicConfirm = null;
  let pendingRelicCancel = null;
  let showNextButton = false;
  let highlightedCardKey = null;
  let highlightedRelicKey = null;
  let autoCardSelectionInFlight = false;
  let autoRelicSelectionInFlight = false;

  $: cardSelectionLocked = pendingCardSelection !== null;
  $: relicSelectionLocked =
    pendingRelicSelection !== null || pendingRelicConfirm !== null || stagedRelicEntries.length > 0;
  $: showCards = cardChoiceEntries.length > 0;
  $: showRelics = relicChoiceEntries.length > 0 && !awaitingCard && !relicSelectionLocked;

  $: pendingConfirmationCount =
    (awaitingCard && stagedCardEntries.length > 0 ? 1 : 0) +
    (awaitingRelic && stagedRelicEntries.length > 0 ? 1 : 0);

  $: awaitingConfirmation =
    pendingConfirmationCount > 0 ||
    pendingCardSelection !== null ||
    pendingRelicSelection !== null ||
    pendingCardConfirm !== null ||
    pendingCardCancel !== null ||
    pendingRelicConfirm !== null ||
    pendingRelicCancel !== null;

  $: remaining =
    (showCards ? cardChoiceEntries.length : 0) +
    (showRelics ? relicChoiceEntries.length : 0) +
    pendingConfirmationCount;

  $: cardActionsDisabled = pendingCardConfirm !== null || pendingCardCancel !== null || pendingCardSelection !== null;
  $: relicActionsDisabled = pendingRelicConfirm !== null || pendingRelicCancel !== null || pendingRelicSelection !== null;

  $: stagedCardKey =
    stagedCardEntries.length > 0 ? rewardEntryKey(stagedCardEntries[0], 0, 'staged-card') : null;
  $: confirmableCardKey = awaitingCard && stagedCardEntries.length > 0 ? stagedCardKey : null;
  $: {
    if (currentPhase === 'cards') {
      if (confirmableCardKey) {
        highlightedCardKey = confirmableCardKey;
      } else if (!highlightedCardKey && cardChoiceEntries.length > 0) {
        highlightedCardKey = cardChoiceEntries[0].key;
      }
    } else {
      highlightedCardKey = null;
    }
  }

  $: stagedRelicKey =
    stagedRelicEntries.length > 0 ? rewardEntryKey(stagedRelicEntries[0], 0, 'staged-relic') : null;
  $: confirmableRelicKey = awaitingRelic && stagedRelicEntries.length > 0 ? stagedRelicKey : null;
  $: {
    if (currentPhase === 'relics') {
      if (confirmableRelicKey) {
        highlightedRelicKey = confirmableRelicKey;
      } else if (!highlightedRelicKey && relicChoiceEntries.length > 0) {
        highlightedRelicKey = relicChoiceEntries[0].key;
      }
    } else {
      highlightedRelicKey = null;
    }
  }

  $: {
    if (
      highlightedRelicKey &&
      !confirmableRelicKey &&
      !relicChoiceEntries.some((choice) => choice.key === highlightedRelicKey)
    ) {
      highlightedRelicKey = relicChoiceEntries.length > 0 ? relicChoiceEntries[0].key : null;
    }
  }

  function dispatchWithResponse(eventName, type) {
    return new Promise((resolve) => {
      let responded = false;
      const respond = (value) => {
        if (responded) return;
        responded = true;
        resolve(value || { ok: false });
      };
      dispatch(eventName, { type, respond });
    });
  }

  async function performRewardSelection(detail) {
    const type = detail?.type;
    const isCard = type === 'card';
    const isRelic = type === 'relic';
    if (!isCard && !isRelic) return;

    let selectionToken = null;

    let responded = false;
    const responsePromise = new Promise((resolve) => {
      const respond = (value) => {
        if (responded) return;
        responded = true;
        resolve(value || { ok: false });
      };
      dispatch('select', { ...detail, respond });
    });

    if (isCard) {
      selectionToken = Symbol('cardSelection');
      pendingCardSelection = selectionToken;
    } else if (isRelic) {
      selectionToken = Symbol('relicSelection');
      pendingRelicSelection = selectionToken;
    }

    try {
      await responsePromise;
    } catch (error) {
      if (isCard && pendingCardSelection === selectionToken) {
        pendingCardSelection = null;
      }
      if (isRelic && pendingRelicSelection === selectionToken) {
        pendingRelicSelection = null;
      }
      return;
    }

    if (isCard && pendingCardSelection === selectionToken) {
      pendingCardSelection = null;
    }
    if (isRelic && pendingRelicSelection === selectionToken) {
      pendingRelicSelection = null;
    }
  }

  async function handleSelect(e) {
    const baseDetail = e?.detail && typeof e.detail === 'object' ? e.detail : {};
    const detail = { ...baseDetail };
    const type = detail.type;
    const isCard = type === 'card';
    const isRelic = type === 'relic';

    if (isCard) {
      const selectionKey = selectionKeyFromDetail(detail, 'card');
      if (selectionKey) {
        highlightedCardKey = selectionKey;
        if (
          confirmableCardKey &&
          selectionKey === confirmableCardKey &&
          awaitingCard &&
          stagedCardEntries.length > 0 &&
          !cardActionsDisabled
        ) {
          await handleConfirm('card');
          return;
        }
      }
    }

    if (isRelic) {
      const selectionKey = selectionKeyFromDetail(detail, 'relic');
      if (selectionKey) {
        highlightedRelicKey = selectionKey;
        if (
          confirmableRelicKey &&
          selectionKey === confirmableRelicKey &&
          awaitingRelic &&
          stagedRelicEntries.length > 0 &&
          !relicActionsDisabled
        ) {
          await handleConfirm('relic');
          return;
        }
      }
    }

    await performRewardSelection(detail);
  }

  async function handleCardConfirm(event) {
    if (cardActionsDisabled) return;
    const detail = event?.detail && typeof event.detail === 'object' ? event.detail : {};
    const selectionKey = selectionKeyFromDetail(detail, 'card');
    if (selectionKey) {
      highlightedCardKey = selectionKey;
    }
    await handleConfirm('card');
  }

  async function handleRelicConfirm(event) {
    if (relicActionsDisabled) return;
    const detail = event?.detail && typeof event.detail === 'object' ? event.detail : {};
    const selectionKey = selectionKeyFromDetail(detail, 'relic');
    if (selectionKey) {
      highlightedRelicKey = selectionKey;
    }
    await handleConfirm('relic');
  }

  $: if (
    currentPhase === 'cards' &&
    cardChoiceEntries.length > 0 &&
    !awaitingCard &&
    stagedCardEntries.length === 0 &&
    pendingCardSelection === null &&
    !autoCardSelectionInFlight
  ) {
    autoCardSelectionInFlight = true;
    const firstChoice = cardChoiceEntries[0];
    if (!highlightedCardKey) {
      highlightedCardKey = firstChoice.key;
    }
    (async () => {
      try {
        await performRewardSelection({
          type: 'card',
          id: firstChoice.entry?.id,
          entry: firstChoice.entry,
          key: firstChoice.key
        });
      } finally {
        autoCardSelectionInFlight = false;
      }
    })();
  } else if (currentPhase !== 'cards') {
    autoCardSelectionInFlight = false;
  }

  $: if (
    currentPhase === 'relics' &&
    relicChoiceEntries.length > 0 &&
    !awaitingRelic &&
    !awaitingCard &&
    stagedRelicEntries.length === 0 &&
    pendingRelicSelection === null &&
    !autoRelicSelectionInFlight
  ) {
    autoRelicSelectionInFlight = true;
    const firstChoice = relicChoiceEntries[0];
    if (!highlightedRelicKey) {
      highlightedRelicKey = firstChoice.key;
    }
    (async () => {
      try {
        await performRewardSelection({
          type: 'relic',
          id: firstChoice.entry?.id,
          entry: firstChoice.entry,
          key: firstChoice.key
        });
      } finally {
        autoRelicSelectionInFlight = false;
      }
    })();
  } else if (currentPhase !== 'relics') {
    autoRelicSelectionInFlight = false;
  }

  function focusRelicChoices() {
    queueMicrotask(() => {
      if (!overlayRootEl) return;
      const stagedButton = overlayRootEl.querySelector(
        '.staged button[data-reward-relic]'
      );
      if (stagedButton) {
        stagedButton.focus();
        return;
      }
      const choiceButton = overlayRootEl.querySelector(
        '.choices button[data-reward-relic]'
      );
      if (choiceButton) {
        choiceButton.focus();
        return;
      }
      overlayRootEl.focus?.();
    });
  }

  async function handleConfirm(type) {
    if (type === 'card') {
      if (pendingCardConfirm) return;
      const token = Symbol('cardConfirm');
      pendingCardConfirm = token;
      try {
        await dispatchWithResponse('confirm', 'card');
      } finally {
        if (pendingCardConfirm === token) {
          pendingCardConfirm = null;
        }
      }
    } else if (type === 'relic') {
      if (pendingRelicConfirm) return;
      const token = Symbol('relicConfirm');
      pendingRelicConfirm = token;
      try {
        await dispatchWithResponse('confirm', 'relic');
      } finally {
        if (pendingRelicConfirm === token) {
          pendingRelicConfirm = null;
        }
        focusRelicChoices();
      }
    }
  }

  async function handleCancel(type) {
    if (type === 'card') {
      if (pendingCardCancel) return;
      const token = Symbol('cardCancel');
      pendingCardCancel = token;
      try {
        await dispatchWithResponse('cancel', 'card');
      } finally {
        if (pendingCardCancel === token) {
          pendingCardCancel = null;
        }
      }
    } else if (type === 'relic') {
      if (pendingRelicCancel) return;
      const token = Symbol('relicCancel');
      pendingRelicCancel = token;
      try {
        await dispatchWithResponse('cancel', 'relic');
      } finally {
        if (pendingRelicCancel === token) {
          pendingRelicCancel = null;
        }
        focusRelicChoices();
      }
    }
  }

  // Auto-advance when there are no selectable rewards and no visible loot/gold.
  // This avoids showing an empty rewards popup in loot-consumed cases.
  let autoTimer;
  $: {
    clearTimeout(autoTimer);
    const noChoices = remaining === 0;
    const visibleLoot = (gold > 0) || hasLootItems || awaitingLoot;
    if (noChoices && !awaitingConfirmation && !visibleLoot) {
      autoTimer = setTimeout(() => dispatch('next'), 5000);
    }
  }
  // Cleanup timer on unmount
  onDestroy(() => {
    clearTimeout(autoTimer);
    clearDropRevealTimers();
    stopDropAudio(true);
    resetAdvanceCountdown(true);
    lastDropSignature = null;
    lastReducedMotion = null;
    lootSfxEnabled = false;
    lootSfxBlocked = false;
    lootSfxNoticeLogged = false;
    while (phaseListenerDisposers.length > 0) {
      const dispose = phaseListenerDisposers.pop();
      try {
        dispose?.();
      } catch {}
    }
  });

  // Show Next Room button when there's loot but no choices
  $: {
    const noChoices = remaining === 0;
    const visibleLoot = (gold > 0) || hasLootItems || awaitingLoot;
    const readyToAdvance = awaitingNext && !awaitingLoot;
    showNextButton = noChoices && !awaitingConfirmation && (visibleLoot || readyToAdvance);
  }

  function handleNextRoom() {
    dispatch('lootAcknowledge');
  }
</script>

<style>
  .layout {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    justify-content: center;
    gap: clamp(1rem, 2vw, 2.5rem);
    width: 100%;
  }

  .main-column {
    flex: 1 1 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    min-width: 0;
  }

  .phase-rail {
    flex: 0 0 280px;
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
    padding: clamp(0.9rem, 1.8vw, 1.4rem);
    border-radius: 20px;
    background: var(--glass-bg);
    border: var(--glass-border);
    box-shadow: var(--glass-shadow);
    backdrop-filter: var(--glass-filter);
    color: rgba(241, 245, 255, 0.92);
    min-height: 100%;
  }

  .phase-panel,
  .advance-panel {
    background: rgba(12, 18, 28, 0.72);
    border: 1px solid rgba(153, 201, 255, 0.2);
    border-radius: 16px;
    padding: clamp(0.75rem, 1.6vw, 1.3rem);
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.32);
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }

  .phase-heading {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .phase-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .phase-item { 
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.55rem 0.75rem;
    border-radius: 12px;
    background: rgba(12, 18, 28, 0.65);
    border: 1px solid rgba(153, 201, 255, 0.1);
    font-size: 0.95rem;
  }

  .phase-item.completed {
    background: rgba(58, 164, 108, 0.25);
    border-color: rgba(76, 175, 80, 0.35);
  }

  .phase-item.current {
    background: rgba(52, 120, 207, 0.3);
    border-color: rgba(90, 170, 255, 0.45);
    box-shadow: 0 0 0 1px rgba(90, 170, 255, 0.3);
  }

  .phase-index {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.8rem;
    height: 1.8rem;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.35);
    font-weight: 700;
  }

  .phase-item.completed .phase-index {
    background: rgba(76, 175, 80, 0.45);
  }

  .phase-item.current .phase-index {
    background: rgba(90, 170, 255, 0.45);
  }

  .phase-item.legacy {
    opacity: 0.55;
  }

  .phase-label {
    flex: 1 1 auto;
    font-weight: 600;
  }

  .phase-note {
    margin: 0;
    font-size: 0.85rem;
    color: rgba(241, 245, 255, 0.75);
  }

  .phase-note.warning {
    color: rgba(255, 214, 153, 0.92);
    font-weight: 600;
  }

  .advance-panel.locked {
    opacity: 0.65;
  }

  .advance-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.75rem;
  }

  .advance-header h4 {
    margin: 0;
    font-size: 0.95rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .advance-target {
    font-size: 0.9rem;
    font-weight: 600;
    color: rgba(158, 217, 255, 0.95);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .advance-status {
    margin: 0;
    font-size: 0.9rem;
    color: rgba(241, 245, 255, 0.8);
  }

  .advance-button {
    align-self: flex-start;
  }

  @media (max-width: 1100px) {
    .layout {
      flex-direction: column;
      align-items: stretch;
    }

    .phase-rail {
      width: 100%;
      flex: 0 0 auto;
    }
  }

  .section-title {
    margin: 0.25rem 0 0.5rem;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
  }

  .choices {
    display: grid;
    grid-template-columns: repeat(3, minmax(200px, 1fr));
    gap: 0.75rem;
    align-items: stretch;
    justify-items: center;
    width: 100%;
    max-width: 960px;
  }

  .choices.staged {
    pointer-events: none;
  }

  .staged-block {
    width: 100%;
    max-width: 960px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.6rem;
  }

  .actions-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  .preview-panel {
    width: 100%;
    background: rgba(11, 17, 27, 0.68);
    border: 1px solid rgba(153, 201, 255, 0.25);
    border-radius: 16px;
    padding: clamp(0.75rem, 1.8vw, 1.2rem);
    color: #f1f5ff;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
  }

  .preview-heading {
    margin: 0 0 0.4rem;
    font-size: 1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .preview-summary {
    margin: 0 0 0.6rem;
    font-size: 0.95rem;
    line-height: 1.4;
    color: rgba(241, 245, 255, 0.85);
  }

  .preview-stats {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .preview-stat {
    border-top: 1px solid rgba(153, 201, 255, 0.15);
    padding-top: 0.5rem;
  }

  .preview-stat:first-child {
    border-top: none;
    padding-top: 0;
  }

  .stat-row {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    font-size: 0.95rem;
  }

  .stat-name {
    font-weight: 600;
    letter-spacing: 0.03em;
  }

  .stat-change {
    font-variant-numeric: tabular-nums;
    color: #9ed9ff;
    font-weight: 600;
  }

  .stat-details {
    list-style: none;
    margin: 0.35rem 0 0 0;
    padding: 0 0 0 1.2rem;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    color: rgba(241, 245, 255, 0.8);
    font-size: 0.85rem;
  }

  .preview-triggers {
    margin-top: 0.75rem;
    padding-top: 0.6rem;
    border-top: 1px solid rgba(153, 201, 255, 0.15);
  }

  .preview-triggers h5 {
    margin: 0 0 0.3rem;
    font-size: 0.85rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(158, 217, 255, 0.9);
  }

  .preview-triggers ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    color: rgba(241, 245, 255, 0.85);
    font-size: 0.9rem;
  }

  .trigger-event {
    font-weight: 600;
  }

  .trigger-description {
    color: rgba(241, 245, 255, 0.82);
  }

  .preview-panel[data-type='relic'] .stat-change {
    color: #f9c97f;
  }

  .cancel-btn {
    min-width: 140px;
    padding: 0.65rem 1.75rem;
    border: none;
    border-radius: 999px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
    color: #fff;
  }

  .cancel-btn {
    background: linear-gradient(145deg, #d32f2f, #9a0007);
    box-shadow: 0 6px 16px rgba(211, 47, 47, 0.35);
  }

  .cancel-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 22px rgba(211, 47, 47, 0.45);
  }

  .cancel-btn:disabled {
    opacity: 0.55;
    cursor: default;
    transform: none;
    box-shadow: none;
  }

  .status {
    margin-top: 0.25rem;
    text-align: center;
    color: #ddd;
  }

  .drops-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: flex-start;
    gap: 0.75rem;
    width: 100%;
    max-width: 640px;
    padding: 0.35rem 0;
  }

  .drop-tile {
    position: relative;
    width: 64px;
    height: 64px;
    border-radius: 12px;
    /* Fallback for browsers that don't support color-mix */
    background: rgba(10, 12, 20, 0.92);
    /* Enhanced with accent color overlay for supporting browsers */
    background: linear-gradient(
      to bottom,
      rgba(255, 255, 255, 0.04),
      rgba(10, 12, 20, 0.92)
    );
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 10px 22px rgba(0, 0, 0, 0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px;
    overflow: hidden;
    transition: transform 160ms ease, box-shadow 160ms ease, opacity 160ms ease;
    will-change: transform, opacity;
  }

  .drop-tile:hover {
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 14px 26px rgba(0, 0, 0, 0.45);
  }

  .drop-icon {
    width: 100%;
    height: 100%;
    object-fit: contain;
    filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.4));
  }

  .drop-count {
    position: absolute;
    bottom: 6px;
    right: 8px;
    background: rgba(0, 0, 0, 0.78);
    color: #fff;
    border-radius: 6px;
    padding: 0 0.4rem;
    font-size: 0.75rem;
    font-weight: 700;
    line-height: 1.1rem;
    min-width: 1.5rem;
    text-align: right;
    font-variant-numeric: tabular-nums;
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
  /* CSS-based reveal: slide the whole card, twinkles appear first, then card fades in */
  @keyframes overlay-slide {
    0%   { transform: translateY(-40px); }
    100% { transform: translateY(0); }
  }
  /* Twinkles fade in early to "form" the card */
  @keyframes overlay-twinkle-fade {
    0%   { opacity: 0; }
    20%  { opacity: 0.6; }
    40%  { opacity: 1; }
    100% { opacity: 1; }
  }
  /* Card content fades in later than twinkles */
  @keyframes overlay-card-fade {
    0%   { opacity: 0; }
    30%  { opacity: 0; }
    100% { opacity: 1; }
  }
  .reveal {
    animation: overlay-slide 360ms cubic-bezier(0.22, 1, 0.36, 1) both;
    animation-delay: var(--delay, 0ms);
  }
  /* Target the CardArt twinkles layer only */
  .reveal :global(.twinkles) {
    opacity: 0;
    animation: overlay-twinkle-fade 520ms cubic-bezier(0.22, 1, 0.36, 1) both;
    animation-delay: var(--delay, 0ms);
  }
  /* Fade in the card content (including photo/box) slightly after twinkles */
  .reveal :global(.card-art) {
    opacity: 0;
    animation: overlay-card-fade 520ms cubic-bezier(0.22, 1, 0.36, 1) both;
    animation-delay: var(--delay, 0ms);
  }

  .next-button {
    margin-top: 1rem;
    padding: 0.75rem 2rem;
    background: linear-gradient(145deg, #4a90e2, #357abd);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    transition: all 0.2s ease;
  }

  .next-button:hover {
    background: linear-gradient(145deg, #5ba0f2, #4a90e2);
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.3);
  }

  .next-button:active {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }

  .next-room-overlay {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1500;
    animation: slideUp 0.3s ease-out;
  }

  .next-button.overlay {
    margin: 0;
    padding: 1rem 2.5rem;
    font-size: 1.1rem;
    font-weight: 700;
    border-radius: 2rem;
    background: linear-gradient(145deg, #4CAF50, #45a049);
    box-shadow: 0 6px 20px rgba(0,0,0,0.3), 0 2px 6px rgba(76, 175, 80, 0.4);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(255, 255, 255, 0.2);
  }

  .next-button.overlay:hover {
    background: linear-gradient(145deg, #5CBF60, #4CAF50);
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.4), 0 4px 10px rgba(76, 175, 80, 0.5);
  }

  .next-button.overlay:active {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.3), 0 2px 6px rgba(76, 175, 80, 0.4);
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateX(-50%) translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }

  @media (max-width: 768px) {
    .next-room-overlay {
      bottom: 1rem;
      left: 1rem;
      right: 1rem;
      transform: none;
      text-align: center;
    }

    .next-button.overlay {
      width: 100%;
      padding: 1rem;
    }
  }
  
</style>

<div
  class="layout"
  bind:this={overlayRootEl}
  tabindex="-1"
  data-reduced-motion={dataReducedMotion}
  data-sfx-volume={dataSfxVolume}
  on:pointerdown={handleLootSfxGesture}
  on:keydown={handleLayoutKeydown}
>
  <span class="sr-only" aria-live="assertive" aria-atomic="true">{phaseAnnouncement}</span>
  <span class="sr-only" aria-live="polite" aria-atomic="true">{countdownAnnouncement}</span>
  <div class="main-column">
    {#if showDropsSection}
      <h3 class="section-title">Drops</h3>
      {#if awaitingLoot && !hasLootItems}
        <div class="status" role="status">Processing loot…</div>
      {/if}
      {#if hasLootItems}
        <div class="drops-row" role="list">
          {#each visibleDrops as entry (entry.key)}
            <div
              class="drop-tile"
              role="listitem"
              style={`--accent: ${entry.accent}`}
              aria-label={`${entry.label}${entry.count > 1 ? ` x${entry.count}` : ''}`}
              in:scale={dropPopTransition}
            >
              <img
                class="drop-icon"
                src={entry.icon}
                alt=""
                aria-hidden="true"
                on:error={onMaterialIconError}
              />
              {#if entry.count > 1}
                <span class="drop-count">x{entry.count}</span>
              {/if}
              <span class="sr-only">{entry.label}{entry.count > 1 ? ` x${entry.count}` : ''}</span>
            </div>
          {/each}
        </div>
      {/if}
      {#if gold}
        <div class="status">Gold +{gold}</div>
      {/if}
      {#if !awaitingLoot && !hasLootItems && !gold}
        <div class="status">No drops this time.</div>
      {/if}
    {/if}

    {#if !nonDropContentHidden}
      {#if stagedCardEntries.length > 0}
        <div class="staged-block">
          <h3 class="section-title">Selected Card</h3>
          <div class="choices staged">
            {#each stagedCardEntries.slice(0,3) as card, i (rewardEntryKey(card, i, 'staged-card'))}
              {@const selectionKey = rewardEntryKey(card, i, 'staged-card')}
              <div class:reveal={!reducedMotion} style={`--delay: ${revealDelay(i)}ms`}>
                <RewardCard
                  entry={card}
                  type="card"
                  quiet={iconQuiet}
                  selectionKey={selectionKey}
                  selected={highlightedCardKey === selectionKey}
                  confirmable={true}
                  confirmDisabled={cardActionsDisabled}
                  confirmLabel="Confirm"
                  reducedMotion={reducedMotion}
                  on:confirm={handleCardConfirm}
                />
              </div>
            {/each}
          </div>
          <div class="actions-row">
            <button class="cancel-btn" type="button" on:click={() => handleCancel('card')} disabled={cardActionsDisabled}>Cancel</button>
          </div>
          {#each stagedCardPreviewDetails as detail (detail.key)}
            <div class="preview-panel" data-type="card">
              <h4 class="preview-heading">{detail.name} Preview</h4>
              {#if detail.preview.summary}
                <p class="preview-summary">{detail.preview.summary}</p>
              {/if}
              {#if detail.preview.stats.length > 0}
                <ul class="preview-stats" role="list">
                  {#each detail.preview.stats as stat (stat.id)}
                    <li class="preview-stat" role="listitem">
                      <div class="stat-row">
                        <span class="stat-name">{stat.label}</span>
                        <span class="stat-change">{stat.change}</span>
                      </div>
                      {#if stat.details.length > 0}
                        <ul class="stat-details" role="list">
                          {#each stat.details as item, index (`${stat.id}-detail-${index}`)}
                            <li role="listitem">{item}</li>
                          {/each}
                        </ul>
                      {/if}
                    </li>
                  {/each}
                </ul>
              {/if}
              {#if detail.preview.triggers.length > 0}
                <div class="preview-triggers" role="group" aria-label="Trigger effects">
                  <h5>Triggers</h5>
                  <ul role="list">
                    {#each detail.preview.triggers as trigger (trigger.id)}
                      <li role="listitem">
                        <span class="trigger-event">{trigger.event}</span>
                        {#if trigger.description}
                          <span class="trigger-description"> — {trigger.description}</span>
                        {/if}
                      </li>
                    {/each}
                  </ul>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}

      {#if showCards}
        <h3 class="section-title">Choose a Card</h3>
        <div class="choices">
          {#each cardChoiceEntries.slice(0,3) as choice, i (choice.key)}
            <div class:reveal={!reducedMotion} style={`--delay: ${revealDelay(i)}ms`}>
              <RewardCard
                entry={choice.entry}
                type="card"
                quiet={iconQuiet}
                selectionKey={choice.key}
                selected={highlightedCardKey === choice.key}
                confirmable={confirmableCardKey === choice.key}
                confirmDisabled={cardActionsDisabled}
                confirmLabel="Confirm"
                reducedMotion={reducedMotion}
                on:select={handleSelect}
                on:confirm={handleCardConfirm}
              />
            </div>
          {/each}
        </div>
      {/if}

      {#if stagedRelicEntries.length > 0}
        <div class="staged-block">
          <h3 class="section-title">Selected Relic</h3>
          <div class="choices staged">
            {#each stagedRelicEntries.slice(0,3) as relic, i (relic?.id ?? `staged-relic-${i}`)}
              {@const selectionKey = rewardEntryKey(relic, i, 'staged-relic')}
              <div class:reveal={!reducedMotion} style={`--delay: ${revealDelay(i)}ms`}>
                <CurioChoice
                  entry={relic}
                  quiet={iconQuiet}
                  selectionKey={selectionKey}
                  selected={highlightedRelicKey === selectionKey}
                  confirmable={true}
                  confirmDisabled={relicActionsDisabled}
                  confirmLabel="Confirm"
                  reducedMotion={reducedMotion}
                  on:confirm={handleRelicConfirm}
                />
              </div>
            {/each}
          </div>
          <div class="actions-row">
            <button class="cancel-btn" type="button" on:click={() => handleCancel('relic')} disabled={relicActionsDisabled}>Cancel</button>
          </div>
          {#each stagedRelicPreviewDetails as detail (detail.key)}
            <div class="preview-panel" data-type="relic">
              <h4 class="preview-heading">{detail.name} Preview</h4>
              {#if detail.preview.summary}
                <p class="preview-summary">{detail.preview.summary}</p>
              {/if}
              {#if detail.preview.stats.length > 0}
                <ul class="preview-stats" role="list">
                  {#each detail.preview.stats as stat (stat.id)}
                    <li class="preview-stat" role="listitem">
                      <div class="stat-row">
                        <span class="stat-name">{stat.label}</span>
                        <span class="stat-change">{stat.change}</span>
                      </div>
                      {#if stat.details.length > 0}
                        <ul class="stat-details" role="list">
                          {#each stat.details as item, index (`${stat.id}-detail-${index}`)}
                            <li role="listitem">{item}</li>
                          {/each}
                        </ul>
                      {/if}
                    </li>
                  {/each}
                </ul>
              {/if}
              {#if detail.preview.triggers.length > 0}
                <div class="preview-triggers" role="group" aria-label="Trigger effects">
                  <h5>Triggers</h5>
                  <ul role="list">
                    {#each detail.preview.triggers as trigger (trigger.id)}
                      <li role="listitem">
                        <span class="trigger-event">{trigger.event}</span>
                        {#if trigger.description}
                          <span class="trigger-description"> — {trigger.description}</span>
                        {/if}
                      </li>
                    {/each}
                  </ul>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}

      {#if showRelics}
        <h3 class="section-title">Choose a Relic</h3>
        <div class="choices">
          {#each relicChoiceEntries.slice(0,3) as relicChoice, i (relicChoice.key)}
            <div class:reveal={!reducedMotion} style={`--delay: ${revealDelay(i)}ms`}>
              <CurioChoice
                entry={relicChoice.entry}
                quiet={iconQuiet}
                selectionKey={relicChoice.key}
                selected={highlightedRelicKey === relicChoice.key}
                confirmable={confirmableRelicKey === relicChoice.key}
                confirmDisabled={relicActionsDisabled}
                confirmLabel="Confirm"
                reducedMotion={reducedMotion}
                on:select={handleSelect}
                on:confirm={handleRelicConfirm}
              />
            </div>
          {/each}
        </div>
      {/if}
    {/if}

    {#if showNextButton}
      <div class="next-room-overlay">
        <button class="next-button overlay" on:click={handleNextRoom}>Next Room</button>
      </div>
    {/if}
  </div>

  <aside class="phase-rail" aria-label="Reward flow">
    <div class="phase-panel">
      <h3 class="phase-heading">Reward Flow</h3>
      <ol class="phase-list" role="list">
        {#each phaseEntries as entry (entry.phase)}
          <li
            class={`phase-item ${entry.status}`}
            role="listitem"
            aria-current={entry.status === 'current' ? 'step' : undefined}
          >
            <span class="phase-index" aria-hidden="true">{entry.status === 'completed' ? '✓' : entry.index}</span>
            <span class="phase-label">{entry.label}</span>
          </li>
        {/each}
      </ol>
    </div>
    {#if fallbackPhaseMessage}
      <p class="phase-note warning" role="status">{fallbackPhaseMessage}</p>
    {:else if nextPhaseLabel && dropsPhaseActive}
      <p class="phase-note">Next: {nextPhaseLabel}</p>
    {/if}
    {#if showAdvancePanel}
      <div class={`advance-panel ${phaseAdvanceAvailable ? 'active' : 'locked'}`}>
        <div class="advance-header">
          <h4>Advance</h4>
          {#if nextPhaseLabel}
            <span class="advance-target">{nextPhaseLabel}</span>
          {/if}
        </div>
        <p class="advance-status" data-testid="advance-countdown" aria-live="polite">{advanceStatusMessage}</p>
        <button
          class="icon-btn advance-button"
          type="button"
          bind:this={advanceButtonEl}
          on:click={handleAdvanceClick}
          disabled={advanceButtonDisabled}
        >
          Advance
        </button>
      </div>
    {/if}
  </aside>
</div>
