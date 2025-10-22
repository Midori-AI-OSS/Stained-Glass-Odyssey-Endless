<script>
  import { createEventDispatcher, onDestroy, onMount } from 'svelte';
  import { cubicOut } from 'svelte/easing';
  import { scale } from 'svelte/transition';
  import RewardCard from './RewardCard.svelte';
  import CurioChoice from './CurioChoice.svelte';
  import { getMaterialIcon, onMaterialIconError } from '../systems/assetLoader.js';
  import { createRewardDropSfx } from '../systems/sfx.js';
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
  export let advanceBusy = false;

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
  let selectionAnnouncement = '';
  let lastCardHighlightKey = null;
  let lastRelicHighlightKey = null;
  let lastSelectionMessage = '';
  let stagedCardEntryMap = new Map();
  let cardChoiceEntryMap = new Map();
  let stagedRelicEntryMap = new Map();
  let relicChoiceEntryMap = new Map();

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
  $: advanceButtonDisabled = !phaseAdvanceAvailable || advanceInFlight || fallbackActive || advanceBusy;
  $: advanceCountdownActive = Boolean(advanceCountdownTimer) && phaseAdvanceAvailable && !advanceBusy;
  $: advanceStatusMessage = (() => {
    if (!showAdvancePanel) return '';
    if (!phaseAdvanceAvailable) {
      return 'Advance locked until this phase is complete.';
    }
    if (advanceBusy) {
      return 'Advancing to the next room…';
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
    if (
      showAdvancePanel &&
      phaseAdvanceAvailable &&
      currentPhase &&
      nextPhase &&
      !advanceInFlight &&
      !advanceBusy
    ) {
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

  function labelForRewardEntry(entry, fallbackType = 'reward') {
    const baseFallback =
      fallbackType === 'card'
        ? 'card selection'
        : fallbackType === 'relic'
          ? 'relic selection'
          : 'reward selection';
    if (!entry || typeof entry !== 'object') {
      return baseFallback;
    }
    const source =
      entry.entry && typeof entry.entry === 'object'
        ? entry.entry
        : entry;
    if (!source || typeof source !== 'object') {
      return baseFallback;
    }
    const uiMeta = source.ui && typeof source.ui === 'object' ? source.ui : null;
    const candidates = [
      uiMeta?.label,
      uiMeta?.title,
      source.name,
      source.title,
      source.id,
      source.slug,
      source.key
    ];
    for (const value of candidates) {
      if (value == null) continue;
      const normalized = String(value).trim();
      if (normalized !== '') {
        return normalized;
      }
    }
    return baseFallback;
  }

  function describeRewardLabel(type, label) {
    const prefix = type === 'relic' ? 'Relic' : 'Card';
    const normalized = typeof label === 'string' ? label.trim() : '';
    if (!normalized) {
      return `${prefix} selection`;
    }
    const lower = normalized.toLowerCase();
    if (lower.startsWith(prefix.toLowerCase())) {
      return normalized;
    }
    return `${prefix} ${normalized}`;
  }

  function sendSelectionAnnouncement(message) {
    const trimmed = typeof message === 'string' ? message.trim() : '';
    if (!trimmed) return;
    if (trimmed === lastSelectionMessage) {
      selectionAnnouncement = '';
      queueMicrotask(() => {
        selectionAnnouncement = trimmed;
      });
      return;
    }
    lastSelectionMessage = trimmed;
    selectionAnnouncement = trimmed;
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
    if (selectionInFlight || awaitingResolution) return false;
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
    if (advanceBusy) return;
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
    if (!phaseAdvanceAvailable || advanceInFlight || fallbackActive || advanceBusy) return;
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
    if (!phaseAdvanceAvailable || advanceInFlight || advanceBusy) return;
    triggerAdvance('manual');
  }

  function handleLayoutKeydown(event) {
    handleLootSfxGesture(event);
    if (event.defaultPrevented) return;
    if (!overlayRootEl || event.target !== overlayRootEl) return;
    if (!phaseAdvanceAvailable || advanceButtonDisabled) return;
    if (fallbackActive) return;
    if (advanceBusy) return;
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
  $: stagedCardEntryMap = new Map(
    stagedCardEntries.map((entry, index) => [rewardEntryKey(entry, index, 'staged-card'), entry])
  );
  $: cardChoiceEntryMap = new Map(cardChoiceEntries.map((choice) => [choice.key, choice.entry]));
  $: stagedRelicEntryMap = new Map(
    stagedRelicEntries.map((entry, index) => [rewardEntryKey(entry, index, 'staged-relic'), entry])
  );
  $: relicChoiceEntryMap = new Map(relicChoiceEntries.map((choice) => [choice.key, choice.entry]));

  let pendingCardSelection = null;
  let pendingRelicSelection = null;
  let showNextButton = false;
  let highlightedCardKey = null;
  let highlightedRelicKey = null;
  let autoCardSelectionInFlight = false;
  let autoRelicSelectionInFlight = false;

  $: cardSelectionLocked = pendingCardSelection !== null;
  $: relicSelectionLocked = pendingRelicSelection !== null || stagedRelicEntries.length > 0;
  $: showCards = cardChoiceEntries.length > 0;
  $: showRelics = relicChoiceEntries.length > 0 && !awaitingCard && !relicSelectionLocked;

  $: selectionInFlight = pendingCardSelection !== null || pendingRelicSelection !== null;

  $: awaitingResolution =
    (awaitingCard && stagedCardEntries.length > 0) || (awaitingRelic && stagedRelicEntries.length > 0);

  $: remaining =
    (showCards ? cardChoiceEntries.length : 0) +
    (showRelics ? relicChoiceEntries.length : 0) +
    (awaitingCard ? stagedCardEntries.length : 0) +
    (awaitingRelic ? stagedRelicEntries.length : 0);

  $: if (currentPhase !== 'cards' && highlightedCardKey !== null) {
    highlightedCardKey = null;
  }

  $: if (
    currentPhase === 'cards' &&
    highlightedCardKey &&
    !cardChoiceEntryMap.has(highlightedCardKey) &&
    !stagedCardEntryMap.has(highlightedCardKey)
  ) {
    highlightedCardKey = null;
  }

  $: highlightedCardLabel = highlightedCardKey
    ? labelForRewardEntry(
        stagedCardEntryMap.get(highlightedCardKey) ?? cardChoiceEntryMap.get(highlightedCardKey),
        'card'
      )
    : '';

  $: if (currentPhase !== 'relics' && highlightedRelicKey !== null) {
    highlightedRelicKey = null;
  }

  $: if (
    currentPhase === 'relics' &&
    highlightedRelicKey &&
    !relicChoiceEntryMap.has(highlightedRelicKey) &&
    !stagedRelicEntryMap.has(highlightedRelicKey)
  ) {
    highlightedRelicKey = null;
  }

  $: highlightedRelicLabel = highlightedRelicKey
    ? labelForRewardEntry(
        stagedRelicEntryMap.get(highlightedRelicKey) ?? relicChoiceEntryMap.get(highlightedRelicKey),
        'relic'
      )
    : '';

  $: {
    if (fallbackActive) {
      if (selectionAnnouncement) {
        selectionAnnouncement = '';
      }
      lastSelectionMessage = '';
    }

    if (!fallbackActive && currentPhase === 'cards') {
      if (highlightedCardKey && highlightedCardKey !== lastCardHighlightKey) {
        const label = describeRewardLabel('card', highlightedCardLabel);
        sendSelectionAnnouncement(`${label} selected.`);
      } else if (!highlightedCardKey && lastCardHighlightKey) {
        sendSelectionAnnouncement('Card selection cleared.');
      }
      lastCardHighlightKey = highlightedCardKey;
    } else {
      lastCardHighlightKey = null;
    }

    if (!fallbackActive && currentPhase === 'relics') {
      if (highlightedRelicKey && highlightedRelicKey !== lastRelicHighlightKey) {
        const label = describeRewardLabel('relic', highlightedRelicLabel);
        sendSelectionAnnouncement(`${label} selected.`);
      } else if (!highlightedRelicKey && lastRelicHighlightKey) {
        sendSelectionAnnouncement('Relic selection cleared.');
      }
      lastRelicHighlightKey = highlightedRelicKey;
    } else {
      lastRelicHighlightKey = null;
    }
  }

  $: {
    if (
      highlightedRelicKey &&
      !stagedRelicEntries.some(
        (entry, index) => rewardEntryKey(entry, index, 'staged-relic') === highlightedRelicKey
      ) &&
      !relicChoiceEntries.some((choice) => choice.key === highlightedRelicKey)
    ) {
      highlightedRelicKey = relicChoiceEntries.length > 0 ? relicChoiceEntries[0].key : null;
    }
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

    if (!isCard && !isRelic) {
      return;
    }

    const selectionKey = selectionKeyFromDetail(detail, isCard ? 'card' : 'relic');
    if (!selectionKey) {
      return;
    }

    const isDoubleClick = isCard
      ? highlightedCardKey === selectionKey
      : highlightedRelicKey === selectionKey;

    if (!isDoubleClick) {
      if (isCard) {
        highlightedCardKey = selectionKey;
      } else {
        highlightedRelicKey = selectionKey;
      }
      if (detail.key == null) {
        detail.key = selectionKey;
      }
      return;
    }

    if (detail.key == null) {
      detail.key = selectionKey;
    }

    await performRewardSelection(detail);
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

  // Auto-advance when there are no selectable rewards and no visible loot/gold.
  // This avoids showing an empty rewards popup in loot-consumed cases.
  let autoTimer;
  $: {
    clearTimeout(autoTimer);
    const noChoices = remaining === 0;
    const visibleLoot = (gold > 0) || hasLootItems || awaitingLoot;
    if (noChoices && !selectionInFlight && !awaitingResolution && !visibleLoot && !advanceBusy) {
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
    showNextButton = noChoices && !selectionInFlight && !awaitingResolution && (visibleLoot || readyToAdvance);
  }

  function handleNextRoom() {
    if (advanceBusy) return;
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
    min-height: clamp(620px, 68vh, 880px);
    padding: clamp(1rem, 1.75vh, 1.9rem) 0;
    /* Overlay theme tokens */
    --overlay-warm-accent: var(--reward-overlay-warm-accent, #f7b267);
    --overlay-text-primary: color-mix(in srgb, #f8fbff 90%, rgba(0, 0, 0, 0.12));
    --overlay-text-muted: color-mix(in srgb, #f1f5ff 72%, rgba(0, 0, 0, 0.35));
    --overlay-text-warm: color-mix(in srgb, var(--overlay-warm-accent) 60%, #fff 40%);
    --overlay-panel-bg:
      linear-gradient(186deg, rgba(10, 14, 24, 0.94), rgba(4, 6, 12, 0.96)),
      var(--glass-bg);
    --overlay-panel-border: var(--glass-border);
    --overlay-panel-shadow: var(--glass-shadow), 0 18px 34px rgba(0, 0, 0, 0.46);
    --overlay-chip-bg: color-mix(in srgb, rgba(255, 255, 255, 0.08) 55%, rgba(6, 10, 18, 0.92) 45%);
    --overlay-chip-border: 1px solid color-mix(in srgb, rgba(118, 178, 248, 0.68) 60%, rgba(255, 255, 255, 0.08));
    --overlay-chip-border-active: 1px solid color-mix(in srgb, var(--accent, #7ec8ff) 65%, rgba(255, 255, 255, 0.12));
    --overlay-button-bg:
      linear-gradient(184deg, rgba(16, 22, 34, 0.92), rgba(6, 10, 18, 0.96)),
      var(--glass-bg);
    --overlay-button-border: 1px solid color-mix(in srgb, var(--accent, #7ec8ff) 55%, rgba(255, 255, 255, 0.14));
    --overlay-button-shadow: 0 12px 26px rgba(0, 0, 0, 0.52);
    --overlay-divider-color: color-mix(in srgb, rgba(126, 200, 255, 0.6) 28%, rgba(255, 255, 255, 0.08));
  }

  .main-column {
    flex: 1 1 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    min-width: 0;
    min-height: 100%;
  }

  .phase-rail {
    flex: 0 0 280px;
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
    padding: clamp(0.9rem, 1.8vw, 1.4rem);
    border-radius: 0;
    background: var(--overlay-panel-bg);
    border: var(--overlay-panel-border);
    box-shadow: var(--overlay-panel-shadow);
    backdrop-filter: var(--glass-filter);
    color: var(--overlay-text-primary);
    min-height: 100%;
  }

  .phase-panel,
  .advance-panel {
    background: var(--overlay-panel-bg);
    border-radius: 0;
    padding: clamp(0.75rem, 1.6vw, 1.3rem);
    border: var(--overlay-panel-border);
    box-shadow: var(--overlay-panel-shadow);
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
    color: var(--overlay-text-warm);
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
    gap: 0.6rem;
    padding: 0.55rem 0.75rem;
    border-radius: 0;
    background: var(--overlay-chip-bg);
    border: var(--overlay-chip-border);
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.05) inset;
    font-size: 0.95rem;
    color: var(--overlay-text-primary);
  }

  .phase-item.completed {
    background: color-mix(in srgb, var(--overlay-chip-bg) 50%, rgba(20, 26, 40, 0.82) 50%);
    border: var(--overlay-chip-border-active);
    box-shadow: 0 0 0 1px color-mix(in srgb, var(--overlay-warm-accent) 32%, transparent) inset;
  }

  .phase-item.current {
    background: color-mix(in srgb, rgba(16, 24, 38, 0.92) 55%, var(--accent, #7ec8ff) 45%);
    border: var(--overlay-chip-border-active);
    box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent, #7ec8ff) 38%, transparent) inset;
  }

  .phase-index {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.9rem;
    height: 1.9rem;
    border-radius: 0;
    background: color-mix(in srgb, rgba(8, 12, 22, 0.85) 70%, var(--overlay-warm-accent) 30%);
    font-weight: 700;
    color: var(--overlay-text-primary);
  }

  .phase-item.completed .phase-index {
    background: color-mix(in srgb, var(--overlay-warm-accent) 60%, rgba(8, 12, 20, 0.65));
  }

  .phase-item.current .phase-index {
    background: color-mix(in srgb, var(--accent, #7ec8ff) 60%, rgba(8, 12, 20, 0.65));
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
    color: var(--overlay-text-muted);
  }

  .phase-note.warning {
    color: var(--overlay-text-warm);
    font-weight: 600;
  }

  .advance-panel.locked {
    opacity: 0.65;
    filter: saturate(0.85);
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
    color: var(--overlay-text-warm);
  }

  .advance-target {
    font-size: 0.9rem;
    font-weight: 600;
    color: color-mix(in srgb, var(--accent, #7ec8ff) 75%, #fff 25%);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .advance-status {
    margin: 0;
    font-size: 0.9rem;
    color: var(--overlay-text-muted);
  }

  .advance-button {
    align-self: flex-start;
    padding: 0.55rem 1.1rem;
    border-radius: 0;
    border: var(--overlay-button-border);
    background: var(--overlay-button-bg);
    color: var(--overlay-text-primary);
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    box-shadow: var(--overlay-button-shadow);
    transition: background 160ms ease, box-shadow 160ms ease, transform 160ms ease;
    cursor: pointer;
  }

  .advance-button:hover,
  .advance-button:focus-visible {
    transform: translateY(-1px);
    background: color-mix(in srgb, rgba(20, 28, 42, 0.92) 60%, var(--accent, #7ec8ff) 40%);
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.52);
    outline: none;
  }

  .advance-button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  @media (max-width: 1100px) {
    .layout {
      flex-direction: column;
      align-items: stretch;
      min-height: unset;
      padding: clamp(1rem, 3vh, 1.5rem) 0;
    }

    .phase-rail {
      width: 100%;
      flex: 0 0 auto;
    }

    .main-column {
      min-height: unset;
    }
  }

  .section-title {
    margin: 0.25rem 0 0.5rem;
    color: var(--overlay-text-warm);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .choices {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.75rem;
    align-items: stretch;
    justify-items: center;
    width: 100%;
    max-width: 1320px;
  }

  .status {
    margin-top: 0.25rem;
    text-align: center;
    color: var(--overlay-text-muted);
  }

  .drops-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: flex-start;
    gap: 0.75rem;
    width: 100%;
    max-width: 880px;
    padding: 0.35rem 0;
  }

  .drop-tile {
    position: relative;
    width: 64px;
    height: 64px;
    border-radius: 0;
    background: var(--overlay-chip-bg);
    border: var(--overlay-chip-border);
    box-shadow:
      0 1px 0 rgba(255, 255, 255, 0.06) inset,
      0 12px 24px rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px;
    overflow: hidden;
    transition: transform 160ms ease, box-shadow 160ms ease, opacity 160ms ease;
    will-change: transform, opacity;
  }

  .drop-tile:hover,
  .drop-tile:focus-visible {
    transform: translateY(-2px) scale(1.03);
    box-shadow:
      0 2px 0 rgba(255, 255, 255, 0.08) inset,
      0 14px 26px rgba(6, 10, 18, 0.52);
    outline: none;
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
    background: color-mix(in srgb, rgba(8, 12, 22, 0.9) 70%, var(--accent, #7ec8ff) 30%);
    color: #fff;
    border-radius: 0;
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
    border-radius: 0;
    border: var(--overlay-button-border);
    background: var(--overlay-button-bg);
    color: var(--overlay-text-primary);
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow:
      0 1px 0 rgba(255, 255, 255, 0.06) inset,
      0 14px 28px rgba(0, 0, 0, 0.48);
    transition: background 180ms ease, box-shadow 180ms ease, transform 180ms ease;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .next-button:hover,
  .next-button:focus-visible {
    transform: translateY(-1px);
    background: color-mix(in srgb, rgba(22, 30, 44, 0.94) 55%, var(--accent, #7ec8ff) 45%);
    box-shadow:
      0 2px 0 rgba(255, 255, 255, 0.06) inset,
      0 18px 34px rgba(0, 0, 0, 0.54);
    outline: none;
  }

  .next-button:active {
    transform: translateY(0);
    box-shadow: 0 8px 18px rgba(5, 8, 16, 0.45);
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
    border-radius: 0;
    border: var(--overlay-button-border);
    background: var(--overlay-button-bg);
    box-shadow:
      0 1px 0 rgba(255, 255, 255, 0.06) inset,
      0 22px 44px rgba(0, 0, 0, 0.52);
    color: var(--overlay-text-primary);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .next-button.overlay:hover,
  .next-button.overlay:focus-visible {
    transform: translateY(-2px);
    background: color-mix(in srgb, rgba(22, 30, 44, 0.94) 55%, var(--accent, #7ec8ff) 45%);
    box-shadow:
      0 2px 0 rgba(255, 255, 255, 0.06) inset,
      0 26px 50px rgba(0, 0, 0, 0.55);
    outline: none;
  }

  .next-button.overlay:active {
    transform: translateY(-1px);
    box-shadow:
      0 1px 0 rgba(255, 255, 255, 0.08) inset,
      0 16px 32px rgba(32, 14, 6, 0.48);
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
  <span class="sr-only" aria-live="polite" aria-atomic="true">{selectionAnnouncement}</span>
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
                reducedMotion={reducedMotion}
                on:select={handleSelect}
              />
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
                reducedMotion={reducedMotion}
                on:select={handleSelect}
              />
            </div>
          {/each}
        </div>
      {/if}
    {/if}

    {#if showNextButton}
      <div class="next-room-overlay">
        <button class="next-button overlay" on:click={handleNextRoom} disabled={advanceBusy}>Next Room</button>
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
