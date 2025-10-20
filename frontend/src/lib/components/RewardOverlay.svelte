<script>
  import { createEventDispatcher, onDestroy } from 'svelte';
  import { cubicOut } from 'svelte/easing';
  import { scale } from 'svelte/transition';
  import RewardCard from './RewardCard.svelte';
  import CurioChoice from './CurioChoice.svelte';
  import { getMaterialIcon, onMaterialIconError } from '../systems/assetLoader.js';
  import { createRewardDropSfx } from '../systems/sfx.js';
  import { formatRewardPreview } from '../utils/rewardPreviewFormatter.js';

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
  export let rewardProgression = null;

  const dispatch = createEventDispatcher();

  // Phase-based flow support
  $: hasProgression = Boolean(rewardProgression && typeof rewardProgression === 'object');
  $: currentPhase = hasProgression ? String(rewardProgression.current_step || '') : '';
  $: availablePhases = hasProgression && Array.isArray(rewardProgression.available) ? rewardProgression.available : [];
  $: completedPhases = hasProgression && Array.isArray(rewardProgression.completed) ? rewardProgression.completed : [];
  $: isDropsPhase = hasProgression && currentPhase === 'drops';
  $: isCardsPhase = hasProgression && currentPhase === 'cards';
  $: isRelicsPhase = hasProgression && currentPhase === 'relics';
  $: isBattleReviewPhase = hasProgression && currentPhase === 'battle_review';

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
  $: relicChoices = Array.isArray(relics) ? relics : [];
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

  // Card/Relic highlight state for new phase-based flow
  let highlightedCardId = null;
  let highlightedRelicId = null;

  // Drops phase countdown timer
  const DROPS_ADVANCE_DELAY_S = 10;
  let dropsTimeRemaining = DROPS_ADVANCE_DELAY_S;
  let dropsCountdownTimer = null;
  let dropsAdvanceInProgress = false;

  $: cardSelectionLocked = pendingCardSelection !== null || stagedCardEntries.length > 0;
  $: relicSelectionLocked = pendingRelicSelection !== null || stagedRelicEntries.length > 0;
  $: showCards = hasProgression 
    ? (isCardsPhase && cardChoices.length > 0 && !cardSelectionLocked)
    : (cardChoices.length > 0 && !cardSelectionLocked);
  $: showRelics = hasProgression
    ? (isRelicsPhase && relicChoices.length > 0 && !relicSelectionLocked)
    : (relicChoices.length > 0 && !awaitingCard && !relicSelectionLocked);
  $: showDrops = hasProgression
    ? (isDropsPhase && hasLootItems)
    : hasLootItems;
  $: showGold = hasProgression
    ? (isDropsPhase && gold > 0)
    : (gold > 0);

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
    (showCards ? cardChoices.length : 0) +
    (showRelics ? relicChoices.length : 0) +
    pendingConfirmationCount;

  $: cardActionsDisabled = pendingCardConfirm !== null || pendingCardCancel !== null || pendingCardSelection !== null;
  $: relicActionsDisabled = pendingRelicConfirm !== null || pendingRelicCancel !== null || pendingRelicSelection !== null;

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

  async function handleSelect(e) {
    const baseDetail = e?.detail && typeof e.detail === 'object' ? e.detail : {};
    const detail = { ...baseDetail };
    const type = detail.type;
    const isCard = type === 'card';
    const isRelic = type === 'relic';
    let selectionToken = null;

    // New phase-based flow: first click highlights, no immediate selection
    if (hasProgression && (isCardsPhase || isRelicsPhase)) {
      const itemId = detail.id;
      if (isCard && isCardsPhase) {
        if (highlightedCardId === itemId) {
          // Second click on same card = confirm
          await handlePhaseConfirm('card', itemId);
          return;
        }
        highlightedCardId = itemId;
        return;
      }
      if (isRelic && isRelicsPhase) {
        if (highlightedRelicId === itemId) {
          // Second click on same relic = confirm
          await handlePhaseConfirm('relic', itemId);
          return;
        }
        highlightedRelicId = itemId;
        return;
      }
    }

    // Legacy flow: dispatch select event immediately
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

    let response;
    try {
      response = await responsePromise;
    } catch (error) {
      response = { ok: false, error };
    }

    if (isCard && pendingCardSelection === selectionToken) {
      pendingCardSelection = null;
    }
    if (isRelic && pendingRelicSelection === selectionToken) {
      pendingRelicSelection = null;
    }
  }

  async function handlePhaseConfirm(type, itemId) {
    // Dispatch select event for phase-based flow
    let responded = false;
    const responsePromise = new Promise((resolve) => {
      const respond = (value) => {
        if (responded) return;
        responded = true;
        resolve(value || { ok: false });
      };
      dispatch('select', { type, id: itemId, respond });
    });

    let response;
    try {
      response = await responsePromise;
    } catch (error) {
      response = { ok: false, error };
    }

    // Clear highlight if successful
    if (response && response.ok) {
      if (type === 'card') {
        highlightedCardId = null;
      } else if (type === 'relic') {
        highlightedRelicId = null;
      }
    }
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
    if (dropsCountdownTimer) {
      clearInterval(dropsCountdownTimer);
      dropsCountdownTimer = null;
    }
    lastDropSignature = null;
    lastReducedMotion = null;
    lootSfxEnabled = false;
    lootSfxBlocked = false;
    lootSfxNoticeLogged = false;
  });

  // Show Next Room button when there's loot but no choices
  $: {
    const noChoices = remaining === 0;
    const visibleLoot = (gold > 0) || hasLootItems || awaitingLoot;
    const readyToAdvance = awaitingNext && !awaitingLoot;
    showNextButton = noChoices && !awaitingConfirmation && (visibleLoot || readyToAdvance);
  }

  // Drops phase countdown timer
  $: {
    if (isDropsPhase && hasLootItems) {
      // Start countdown when entering drops phase
      if (!dropsCountdownTimer) {
        dropsTimeRemaining = DROPS_ADVANCE_DELAY_S;
        dropsCountdownTimer = setInterval(() => {
          dropsTimeRemaining -= 1;
          if (dropsTimeRemaining <= 0) {
            clearInterval(dropsCountdownTimer);
            dropsCountdownTimer = null;
            if (isDropsPhase && !dropsAdvanceInProgress) {
              handleDropsAdvance();
            }
          }
        }, 1000);
      }
    } else {
      // Clear timer when leaving drops phase
      if (dropsCountdownTimer) {
        clearInterval(dropsCountdownTimer);
        dropsCountdownTimer = null;
      }
      dropsTimeRemaining = DROPS_ADVANCE_DELAY_S;
    }
  }

  function handleDropsAdvance() {
    if (dropsAdvanceInProgress) return;
    dropsAdvanceInProgress = true;
    dispatch('advancePhase', { from: 'drops' });
    // Reset after dispatch
    setTimeout(() => {
      dropsAdvanceInProgress = false;
    }, 100);
  }

  function handleNextRoom() {
    dispatch('lootAcknowledge');
  }

</script>

<style>
  .layout {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
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

  .confirm-btn,
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

  .confirm-btn {
    background: linear-gradient(145deg, #4caf50, #2e7d32);
    box-shadow: 0 6px 16px rgba(46, 125, 50, 0.35);
  }

  .confirm-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 22px rgba(46, 125, 50, 0.45);
  }

  .cancel-btn {
    background: linear-gradient(145deg, #d32f2f, #9a0007);
    box-shadow: 0 6px 16px rgba(211, 47, 47, 0.35);
  }

  .cancel-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 22px rgba(211, 47, 47, 0.45);
  }

  .confirm-btn:disabled,
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

  /* Wiggle animation for highlighted cards/relics */
  @keyframes wiggle {
    0% { transform: rotate(0deg) scale(1); }
    10% { transform: rotate(-1.5deg) scale(1.02); }
    20% { transform: rotate(1.5deg) scale(1.02); }
    30% { transform: rotate(-1deg) scale(1.01); }
    40% { transform: rotate(1deg) scale(1.01); }
    50% { transform: rotate(0deg) scale(1); }
    100% { transform: rotate(0deg) scale(1); }
  }

  .highlight-wiggle {
    animation: wiggle 2.2s ease-in-out infinite;
    animation-delay: var(--wiggle-delay, 0ms);
  }

  /* Confirm button that appears beneath highlighted card/relic */
  .inline-confirm-wrapper {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
  }

  .inline-confirm-btn {
    background: var(--glass-bg);
    border: var(--glass-border);
    box-shadow: var(--glass-shadow);
    backdrop-filter: var(--glass-filter);
    padding: 0.5rem 1.5rem;
    border-radius: 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: #fff;
    cursor: pointer;
    transition: background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 120px;
  }

  .inline-confirm-btn:hover {
    background: rgba(120, 180, 255, 0.22);
    box-shadow: 0 2px 8px 0 rgba(0, 40, 120, 0.18);
    transform: translateY(-2px);
  }

  .inline-confirm-btn:active {
    transform: translateY(0);
  }

  .inline-confirm-btn:disabled {
    opacity: 0.55;
    cursor: not-allowed;
    transform: none;
  }

  /* Drops advance button with countdown */
  .drops-advance-wrapper {
    margin-top: 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .drops-advance-btn {
    background: var(--glass-bg);
    border: var(--glass-border);
    box-shadow: var(--glass-shadow);
    backdrop-filter: var(--glass-filter);
    padding: 0.6rem 2rem;
    border-radius: 0;
    font-size: 1rem;
    font-weight: 600;
    color: #fff;
    cursor: pointer;
    transition: background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
  }

  .drops-advance-btn:hover {
    background: rgba(120, 180, 255, 0.22);
    box-shadow: 0 2px 8px 0 rgba(0, 40, 120, 0.18);
    transform: translateY(-2px);
  }

  .drops-advance-btn:active {
    transform: translateY(0);
  }

  .drops-advance-btn:disabled {
    opacity: 0.55;
    cursor: not-allowed;
    transform: none;
  }

  .countdown-display {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.75);
    font-variant-numeric: tabular-nums;
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
  data-reduced-motion={dataReducedMotion}
  data-sfx-volume={dataSfxVolume}
  on:pointerdown={handleLootSfxGesture}
  on:keydown={handleLootSfxGesture}
>
  {#if stagedCardEntries.length > 0}
    <div class="staged-block">
      <h3 class="section-title">Selected Card</h3>
      <div class="choices staged">
        {#each stagedCardEntries.slice(0,3) as card, i (card?.id ?? `staged-card-${i}`)}
          <div class:reveal={!reducedMotion} style={`--delay: ${revealDelay(i)}ms`}>
            <RewardCard entry={card} type="card" quiet={iconQuiet} disabled={true} />
          </div>
        {/each}
      </div>
      {#if !hasProgression}
        <div class="actions-row">
          <button class="confirm-btn" type="button" on:click={() => handleConfirm('card')} disabled={cardActionsDisabled}>Confirm</button>
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
      {/if}
    </div>
  {/if}

  {#if showCards}
    <h3 class="section-title">Choose a Card</h3>
    <div class="choices">
      {#each cardChoices.slice(0,3) as card, i (card?.id ?? `card-${i}`)}
        <div 
          class:reveal={!reducedMotion} 
          style={`--delay: ${revealDelay(i)}ms`}
          class:inline-confirm-wrapper={hasProgression && highlightedCardId === card?.id}
        >
          <div 
            class:highlight-wiggle={hasProgression && highlightedCardId === card?.id}
            style={hasProgression && highlightedCardId === card?.id ? `--wiggle-delay: ${i * 100}ms` : ''}
          >
            <RewardCard entry={card} type="card" quiet={iconQuiet} on:select={handleSelect} />
          </div>
          {#if hasProgression && highlightedCardId === card?.id}
            <button 
              class="inline-confirm-btn" 
              on:click={() => handlePhaseConfirm('card', card?.id)}
              aria-label="Confirm card selection"
            >
              Confirm
            </button>
          {/if}
        </div>
      {/each}
    </div>
  {/if}

  {#if stagedRelicEntries.length > 0}
    <div class="staged-block">
      <h3 class="section-title">Selected Relic</h3>
      <div class="choices staged">
        {#each stagedRelicEntries.slice(0,3) as relic, i (relic?.id ?? `staged-relic-${i}`)}
          <div class:reveal={!reducedMotion} style={`--delay: ${revealDelay(i)}ms`}>
            <CurioChoice entry={relic} quiet={iconQuiet} disabled={true} />
          </div>
        {/each}
      </div>
      {#if !hasProgression}
        <div class="actions-row">
          <button class="confirm-btn" type="button" on:click={() => handleConfirm('relic')} disabled={relicActionsDisabled}>Confirm</button>
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
      {/if}
    </div>
  {/if}

  {#if showRelics}
    <h3 class="section-title">Choose a Relic</h3>
    <div class="choices">
      {#each relicChoices.slice(0,3) as relic, i (relic?.id ?? `relic-${i}`)}
        <div 
          class:reveal={!reducedMotion} 
          style={`--delay: ${revealDelay(i)}ms`}
          class:inline-confirm-wrapper={hasProgression && highlightedRelicId === relic?.id}
        >
          <div 
            class:highlight-wiggle={hasProgression && highlightedRelicId === relic?.id}
            style={hasProgression && highlightedRelicId === relic?.id ? `--wiggle-delay: ${i * 100}ms` : ''}
          >
            <CurioChoice entry={relic} quiet={iconQuiet} on:select={handleSelect} />
          </div>
          {#if hasProgression && highlightedRelicId === relic?.id}
            <button 
              class="inline-confirm-btn" 
              on:click={() => handlePhaseConfirm('relic', relic?.id)}
              aria-label="Confirm relic selection"
            >
              Confirm
            </button>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
  
  {#if showDrops}
    <h3 class="section-title">Drops</h3>
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
    {#if isDropsPhase}
      <div class="drops-advance-wrapper">
        <button 
          class="drops-advance-btn" 
          on:click={handleDropsAdvance} 
          disabled={dropsAdvanceInProgress}
        >
          Advance
          <span class="countdown-display">({dropsTimeRemaining}s)</span>
        </button>
      </div>
    {/if}
  {/if}
  {#if showGold}
    <div class="status">Gold +{gold}</div>
  {/if}
  
  {#if showNextButton}
    <div class="next-room-overlay">
      <button class="next-button overlay" on:click={handleNextRoom}>Next Room</button>
    </div>
  {/if}
  <!-- Auto-advance remains when no choices/loot -->
</div>
