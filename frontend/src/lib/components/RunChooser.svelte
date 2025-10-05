<script>
  import { browser } from '$app/environment';
  import { createEventDispatcher, onDestroy, onMount } from 'svelte';

  import MenuPanel from './MenuPanel.svelte';
  import PartyPicker from './PartyPicker.svelte';
  import Tooltip from './Tooltip.svelte';
  import { formatPercent } from '../utils/upgradeFormatting.js';
  import {
    getRunConfigurationMetadata,
    logMenuAction
  } from '../systems/uiApi.js';

  const STORAGE_KEY = 'run_wizard_defaults_v1';
  const PRESET_STORAGE_KEY = 'run_wizard_recent_presets_v1';
  const MAX_PRESETS_PER_RUN_TYPE = 3;
  const STEP_SEQUENCE = ['resume', 'party', 'run-type', 'modifiers', 'confirm'];

  export let runs = [];
  export let metadataHash = null;
  export let reducedMotion = false;

  const dispatch = createEventDispatcher();

  let step = 'resume';
  let metadataLoading = false;
  let metadataError = '';
  let metadata = null;
  let runTypes = [];
  let modifiers = [];
  let modifierMap = new Map();
  let runTypeId = '';
  let modifierValues = {};
  let modifierDirty = {};
  let partySelection = [];
  let damageType = '';
  let resumeIndex = -1;
  let submitting = false;
  let persistedDefaults = null;
  let visitedSteps = new Set();
  let wizardSessionId = '';
  let completed = false;
  let recentPresetCache = {};
  let quickStartPresets = [];
  let lastAppliedPresetFingerprint = null;
  let sanitizedMetadataHash = null;
  let currentMetadataHash = null;
  let lastRequestedMetadataHash = null;
  let needsMetadataRefresh = false;

  const hasOwn = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
  const EFFECT_LABEL_MAP = {
    encounter_bonus: 'Foe slots',
    defense_floor: 'DEF floor',
    elite_spawn_bonus_pct: 'Elite odds',
    shop_multiplier: 'Shop',
    mitigation: 'Mitigation',
    vitality: 'Vitality',
    atk: 'Attack',
    max_hp: 'Max HP',
    glitched_chance: 'Glitched odds',
    prime_chance: 'Prime odds'
  };

  let normalizedRuns = [];
  let visibleSteps = STEP_SEQUENCE;
  let currentStepIndex = 0;

  $: normalizedRuns = Array.isArray(runs) ? runs : [];
  $: if (normalizedRuns.length === 0 && step === 'resume') {
    step = 'party';
  }
  $: if (normalizedRuns.length > 0 && (resumeIndex < 0 || resumeIndex >= normalizedRuns.length)) {
    resumeIndex = 0;
  } else if (normalizedRuns.length === 0 && resumeIndex !== -1) {
    resumeIndex = -1;
  }

  $: hasRuns = normalizedRuns.length > 0;
  $: visibleSteps = STEP_SEQUENCE.filter((key) => !(key === 'resume' && !hasRuns));
  $: totalSteps = visibleSteps.length;
  $: currentStepIndex = Math.max(0, visibleSteps.indexOf(step));
  $: activeRunType = runTypes.find((rt) => rt.id === runTypeId) || runTypes[0] || null;
  $: selectedModifiers = modifiers.map((mod) => {
    const value = sanitizeStack(mod.id, modifierValues[mod.id]);
    return {
      ...mod,
      value,
      meta: describeModifier(mod)
    };
  });
  $: pressureValue = sanitizeStack('pressure', modifierValues.pressure);
  $: rewardPreview = computeRewardPreview(modifierValues, modifiers);
  $: stepTitle = deriveStepTitle(step);
  $: resumeDisabled = resumeIndex < 0 || resumeIndex >= normalizedRuns.length;
  $: partySummary = partySelection.slice(0, 5);
  $: quickStartPresets = deriveQuickStartPresets(runTypeId);
  $: sanitizedMetadataHash = normalizeMetadataHash(metadataHash);
  $: currentMetadataHash = normalizeMetadataHash(metadata?.metadata_hash ?? metadata?.version);
  $: needsMetadataRefresh =
    Boolean(sanitizedMetadataHash) &&
    sanitizedMetadataHash !== currentMetadataHash &&
    !metadataLoading;
  $: if (needsMetadataRefresh && sanitizedMetadataHash !== lastRequestedMetadataHash) {
    lastRequestedMetadataHash = sanitizedMetadataHash;
    void fetchMetadata({ metadataHash: sanitizedMetadataHash });
  }

  onMount(() => {
    resumeIndex = normalizedRuns.length > 0 ? 0 : -1;
    wizardSessionId = createSessionId();
    loadPersistedDefaults();
    initializeFromPersistence();
    loadRecentPresets();
    if (!hasRuns) {
      step = 'party';
    }
    const persistedHash = normalizeMetadataHash(
      persistedDefaults?.metadataSignature ?? persistedDefaults?.metadataVersion
    );
    const initialHash = sanitizedMetadataHash || persistedHash;
    lastRequestedMetadataHash = initialHash;
    void fetchMetadata({ metadataHash: initialHash });
    logStepImpression(step);
    logWizardEvent('opened', { run_count: normalizedRuns.length });
  });

  onDestroy(() => {
    if (!completed) {
      logWizardEvent('abandoned', { step, run_type: runTypeId });
    }
  });

  function createSessionId() {
    if (typeof crypto !== 'undefined' && crypto?.randomUUID) {
      return crypto.randomUUID();
    }
    return `wizard-${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
  }

  function deriveStepTitle(current) {
    switch (current) {
      case 'resume':
        return 'Resume or Start';
      case 'party':
        return 'Build Your Party';
      case 'run-type':
        return 'Choose Run Type';
      case 'modifiers':
        return 'Configure Modifiers';
      case 'confirm':
        return 'Review & Start';
      default:
        return 'Run Setup';
    }
  }

  function loadPersistedDefaults() {
    if (!browser) return;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === 'object') {
        persistedDefaults = parsed;
        if (Array.isArray(parsed.party)) {
          partySelection = [...parsed.party].slice(0, 5);
        }
        if (parsed.damageType) {
          damageType = String(parsed.damageType);
        }
      }
    } catch (err) {
      console.warn('Failed to load run wizard defaults', err);
    }
  }

  function initializeFromPersistence() {
    if (persistedDefaults?.runTypeId) {
      runTypeId = String(persistedDefaults.runTypeId);
    }
  }

  function loadRecentPresets() {
    if (!browser) return;
    try {
      const raw = localStorage.getItem(PRESET_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === 'object') {
        recentPresetCache = { ...parsed };
      }
    } catch (err) {
      console.warn('Failed to load run wizard presets', err);
      recentPresetCache = {};
    }
  }

  function persistRecentPresetCache(nextCache) {
    recentPresetCache = nextCache;
    if (!browser) return;
    try {
      localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify(nextCache));
    } catch (err) {
      console.warn('Failed to persist run wizard presets', err);
    }
  }

  function fingerprintPresetValues(values) {
    if (!values || typeof values !== 'object') {
      return '';
    }
    const entries = Object.entries(values).map(([key, value]) => {
      const numeric = Number(value);
      return [key, Number.isFinite(numeric) ? numeric : value];
    });
    entries.sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
    try {
      return JSON.stringify(entries);
    } catch {
      return entries.map(([key, value]) => `${key}:${value}`).join('|');
    }
  }

  function normalizeMetadataHash(value) {
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
    if (typeof value === 'number' && Number.isFinite(value)) {
      return String(value);
    }
    return null;
  }

  async function fetchMetadata({ forceRefresh = false, metadataHash: incomingHash = null } = {}) {
    metadataLoading = true;
    metadataError = '';
    const hashHint = normalizeMetadataHash(incomingHash);
    lastRequestedMetadataHash = hashHint;
    try {
      const payload = await getRunConfigurationMetadata({
        suppressOverlay: true,
        forceRefresh,
        metadataHash: hashHint
      });
      metadata = payload || {};
      runTypes = Array.isArray(payload?.run_types) ? payload.run_types : [];
      modifiers = Array.isArray(payload?.modifiers) ? payload.modifiers : [];
      modifierMap = new Map(modifiers.map((entry) => [entry.id, entry]));

      if (!runTypeId || !runTypes.some((rt) => rt.id === runTypeId)) {
        runTypeId = runTypes[0]?.id || 'standard';
      }

      const baseState = buildBaseModifierState();
      modifierValues = baseState.values;
      modifierDirty = baseState.dirty;

      applyRunTypeDefaults(runTypeId, { resetDirty: true });
      lastAppliedPresetFingerprint = null;

      if (persistedDefaults?.modifiers && typeof persistedDefaults.modifiers === 'object') {
        const overrides = persistedDefaults.modifiers;
        for (const [modId, raw] of Object.entries(overrides)) {
          if (!modifierMap.has(modId)) continue;
          const sanitized = sanitizeStack(modId, raw);
          modifierValues = { ...modifierValues, [modId]: sanitized };
          modifierDirty = { ...modifierDirty, [modId]: true };
        }
      }

      persistDefaults();
      logWizardEvent('metadata_loaded', {
        version: payload?.version || null,
        run_type: runTypeId
      });
    } catch (err) {
      metadataError = err?.message || 'Failed to load run configuration metadata.';
      logWizardEvent('metadata_error', { message: metadataError });
    } finally {
      metadataLoading = false;
    }
  }

  function buildBaseModifierState() {
    const values = {};
    const dirty = {};
    for (const entry of modifiers) {
      const def = entry?.stacking || {};
      const base = sanitizeStack(entry.id, hasOwn(def, 'default') ? def.default : def.minimum);
      values[entry.id] = base;
      dirty[entry.id] = false;
    }
    return { values, dirty };
  }

  function rememberPreset(modifierPayload) {
    if (!runTypeId || !Array.isArray(modifiers) || modifiers.length === 0) {
      return;
    }
    if (!modifierPayload || typeof modifierPayload !== 'object') {
      return;
    }
    const sanitized = {};
    for (const entry of modifiers) {
      sanitized[entry.id] = sanitizeStack(entry.id, modifierPayload[entry.id]);
    }
    storePresetForRunType(runTypeId, sanitized);
  }

  function storePresetForRunType(targetRunType, values) {
    if (!targetRunType || !values || typeof values !== 'object') {
      return;
    }
    const storedValues = {};
    for (const [key, value] of Object.entries(values)) {
      storedValues[key] = value;
    }
    const fingerprint = fingerprintPresetValues(storedValues);
    if (!fingerprint) {
      return;
    }
    const existing = Array.isArray(recentPresetCache[targetRunType])
      ? [...recentPresetCache[targetRunType]]
      : [];
    const filtered = existing.filter((entry) => entry?.fingerprint !== fingerprint);
    filtered.unshift({
      values: storedValues,
      fingerprint,
      metadataVersion: metadata?.version || null,
      metadataSignature: normalizeMetadataHash(metadata?.metadata_hash ?? metadata?.version),
      savedAt: Date.now()
    });
    if (filtered.length > MAX_PRESETS_PER_RUN_TYPE) {
      filtered.length = MAX_PRESETS_PER_RUN_TYPE;
    }
    persistRecentPresetCache({ ...recentPresetCache, [targetRunType]: filtered });
  }

  function deriveQuickStartPresets(targetRunType) {
    if (!targetRunType || !Array.isArray(modifiers) || modifiers.length === 0) {
      return [];
    }
    const stored = recentPresetCache?.[targetRunType];
    if (!Array.isArray(stored) || stored.length === 0) {
      return [];
    }
    const seen = new Set();
    const options = [];
    for (const entry of stored) {
      const source = entry?.values && typeof entry.values === 'object' ? entry.values : {};
      const normalized = {};
      for (const mod of modifiers) {
        normalized[mod.id] = sanitizeStack(mod.id, source[mod.id]);
      }
      const fingerprint = entry?.fingerprint || fingerprintPresetValues(normalized);
      if (!fingerprint || seen.has(fingerprint)) {
        continue;
      }
      seen.add(fingerprint);
      const stacks = buildPresetStackSummary(normalized);
      const reward = computeRewardPreview(normalized, modifiers);
      const metadataSignature = normalizeMetadataHash(
        entry?.metadataSignature ?? entry?.metadataVersion
      );
      options.push({
        values: normalized,
        stacks,
        reward,
        fingerprint,
        metadataVersion: entry?.metadataVersion || null,
        metadataSignature,
        savedAt: entry?.savedAt || 0
      });
      if (options.length >= MAX_PRESETS_PER_RUN_TYPE) {
        break;
      }
    }
    return options;
  }

  function buildPresetStackSummary(values) {
    if (!values || typeof values !== 'object') {
      return [];
    }
    const summary = [];
    for (const entry of modifiers) {
      const sanitized = sanitizeStack(entry.id, values[entry.id]);
      if (entry.id === 'pressure' || sanitized > (entry.stacking?.minimum ?? 0)) {
        summary.push(`${modifierLabel(entry)} ${sanitized}`);
      }
    }
    return summary.length ? summary : ['No modifiers'];
  }

  function getRunTypeDefault(modId) {
    const entry = modifierMap.get(modId);
    if (!entry) {
      return 0;
    }
    const runTypeDefault = activeRunType?.default_modifiers?.[modId];
    if (runTypeDefault !== undefined) {
      return sanitizeStack(modId, runTypeDefault);
    }
    const stacking = entry.stacking || {};
    return sanitizeStack(modId, stacking.default ?? stacking.minimum ?? 0);
  }

  function presetButtonLabel(preset, index) {
    if (!preset) {
      return `Apply preset ${index + 1}`;
    }
    const stackText = Array.isArray(preset.stacks) ? preset.stacks.join(', ') : 'No modifiers';
    const reward = preset.reward || {};
    const rewardSegments = [];
    if (Number.isFinite(reward.exp_bonus) && reward.exp_bonus !== 0) {
      rewardSegments.push(`EXP ${formatRewardBonus(reward.exp_bonus)}`);
    }
    if (Number.isFinite(reward.rdr_bonus) && reward.rdr_bonus !== 0) {
      rewardSegments.push(`RDR ${formatRewardBonus(reward.rdr_bonus)}`);
    }
    if (Number.isFinite(reward.foe_bonus) && reward.foe_bonus !== 0) {
      rewardSegments.push(`Foe ${formatRewardBonus(reward.foe_bonus)}`);
    }
    if (Number.isFinite(reward.player_bonus) && reward.player_bonus !== 0) {
      rewardSegments.push(`Player ${formatRewardBonus(reward.player_bonus)}`);
    }
    const rewardText = rewardSegments.length ? `. Reward preview ${rewardSegments.join(', ')}` : '';
    return `Apply preset ${index + 1}: ${stackText}${rewardText}`;
  }

  function applyPreset(preset, index) {
    if (!preset || !preset.values) {
      return;
    }
    const nextValues = { ...modifierValues };
    const nextDirty = { ...modifierDirty };
    for (const entry of modifiers) {
      const sanitized = sanitizeStack(entry.id, preset.values[entry.id]);
      nextValues[entry.id] = sanitized;
      nextDirty[entry.id] = sanitized !== getRunTypeDefault(entry.id);
    }
    modifierValues = nextValues;
    modifierDirty = nextDirty;
    lastAppliedPresetFingerprint = preset.fingerprint || fingerprintPresetValues(preset.values);
    persistDefaults();
    logWizardEvent('preset_applied', {
      run_type: runTypeId,
      preset_index: index,
      preset_fingerprint: lastAppliedPresetFingerprint,
      metadata_version: metadata?.version || null,
      modifiers: summarizeActiveModifiers()
    });
  }

  function describeModifier(mod) {
    const stacking = normaliseStacking(mod?.stacking);
    const rewards = buildRewardSummaries(mod?.reward_bonuses);
    const diminishing = buildDiminishingSummary(mod?.diminishing_returns);
    const effects = buildEffectsSummary(mod);
    const previewChips = buildPreviewChips(mod, stacking);
    const previewSentence = buildPreviewSentence(previewChips, stacking);
    const tooltipParts = [
      mod?.description?.trim() || '',
      stacking.sentence,
      effects.tooltip,
      rewards.tooltip,
      diminishing.tooltip,
      previewSentence
    ].filter(Boolean);
    const tooltipText = tooltipParts.join(' ');
    const tooltipLabel = `${modifierLabel(mod)} modifier details. ${tooltipText || 'No additional details available.'}`;

    return {
      stackSummary: stacking.inline,
      effectsSummary: effects.inline,
      rewardSummary: rewards.inline,
      diminishingSummary: diminishing.inline,
      tooltipText,
      tooltipLabel,
      previewChips
    };
  }

  function buildEffectsSummary(mod) {
    const effects = mod?.effects;
    if (!effects || typeof effects !== 'object') {
      return { inline: '', tooltip: '' };
    }

    if (hasOwn(effects, 'primary_penalty_per_stack')) {
      return summarizePlayerPenaltyEffects(effects);
    }

    if (hasOwn(effects, 'stat') && hasOwn(effects, 'per_stack')) {
      return summarizeStatScalingEffects(effects);
    }

    const entries = Object.entries(effects);
    const inlineSegments = [];
    const tooltipSegments = [];

    for (const [key, raw] of entries) {
      if (!raw) continue;
      if (typeof raw === 'object') {
        const inline = summarizeEffectEntry(key, raw);
        if (inline) inlineSegments.push(inline);
        if (raw.description) {
          tooltipSegments.push(String(raw.description).trim());
        }
        if (raw.tooltip) {
          tooltipSegments.push(String(raw.tooltip).trim());
        }
      } else if (typeof raw === 'string') {
        tooltipSegments.push(raw.trim());
      }
    }

    const inline = inlineSegments.length ? `Effects: ${inlineSegments.join(' • ')}` : '';
    const tooltip = tooltipSegments.join(' ').trim();
    return { inline, tooltip };
  }

  function summarizePlayerPenaltyEffects(effects) {
    const primary = toNumber(effects.primary_penalty_per_stack);
    const overflow = toNumber(effects.overflow_penalty_per_stack);
    const threshold = toNumber(effects.overflow_threshold);

    const inlineSegments = [];
    const tooltipSegments = [];

    if (Number.isFinite(primary) && primary > 0) {
      inlineSegments.push(`${formatPercentDetailed(-primary)} stats/stack`);
      const percent = stripLeadingPlus(formatPercentDetailed(primary));
      tooltipSegments.push(`Each stack reduces all player stats by ${percent}.`);
    }

    if (Number.isFinite(overflow) && overflow > 0 && Number.isFinite(threshold) && threshold > 0) {
      inlineSegments.push(
        `${stripLeadingPlus(formatPercentDetailed(-overflow))} stats past ${threshold}`
      );
      const percent = stripLeadingPlus(formatPercentDetailed(overflow));
      tooltipSegments.push(
        `Stacks beyond ${threshold} reduce stats by only ${percent} each.`
      );
    }

    const inline = inlineSegments.length ? `Effects: ${inlineSegments.join(' • ')}` : '';
    const tooltip = tooltipSegments.join(' ').trim();
    return { inline, tooltip };
  }

  function summarizeStatScalingEffects(effects) {
    const stat = formatEffectLabel(effects.stat);
    const perStack = toNumber(effects.per_stack);
    if (!Number.isFinite(perStack)) {
      return { inline: '', tooltip: '' };
    }

    const inlineValue = formatPerStackValue(perStack, stat, effects.scaling_type);
    const inline = inlineValue ? `Effects: ${inlineValue}` : '';
    const tooltipValue = inlineValue
      ?.replace(/\s*\(multiplicative\)$/, '')
      .replace(/\/?stack$/, '')
      .trim();
    const tooltip = tooltipValue
      ? `Each stack modifies ${stat.toLowerCase()} by ${tooltipValue}.`
      : '';
    return { inline, tooltip };
  }

  function summarizeEffectEntry(key, effect) {
    if (effect.type === 'step') {
      const amount = toNumber(effect.amount_per_step);
      const step = Math.max(1, toNumber(effect.step_size, 1));
      if (!Number.isFinite(amount)) return '';
      const label = formatEffectLabel(key);
      const value = key.endsWith('_pct')
        ? formatPercentPoints(amount)
        : formatSignedInteger(amount);
      return `${value} ${label}/${step} stacks`;
    }

    if (effect.type === 'linear') {
      const perStack = toNumber(effect.per_stack);
      if (!Number.isFinite(perStack)) return '';
      const label = formatEffectLabel(key);
      if (key.endsWith('_pct')) {
        return `${formatPercentPoints(perStack)} ${label}/stack`;
      }
      return `${formatPerStackValue(perStack, label)}`;
    }

    if (effect.type === 'exponential') {
      const base = toNumber(effect.base);
      if (!Number.isFinite(base) || base <= 0) return '';
      const label = formatEffectLabel(key);
      return `${label} ${formatMultiplier(base)}^stack`;
    }

    return '';
  }

  function formatPerStackValue(value, label, scalingType = 'additive') {
    if (!Number.isFinite(value)) return '';
    const formatted = Math.abs(value) < 1 ? formatPercentDetailed(value) : formatSignedInteger(value);
    const suffix = scalingType === 'multiplicative' ? ' (multiplicative)' : '';
    return `${formatted} ${label}/stack${suffix}`;
  }

  function formatEffectLabel(key) {
    if (!key) return 'value';
    if (EFFECT_LABEL_MAP[key]) return EFFECT_LABEL_MAP[key];
    return String(key).replace(/_/g, ' ').replace(/\b([a-z])/g, (match) => match.toUpperCase());
  }

  function formatSignedInteger(value) {
    if (!Number.isFinite(value)) return '0';
    const rounded = Math.round(value * 1000) / 1000;
    return `${rounded >= 0 ? '+' : ''}${rounded}`;
  }

  function stripLeadingPlus(value) {
    return typeof value === 'string' ? value.replace(/^\+/, '') : value;
  }

  function formatPercentDetailed(value) {
    if (!Number.isFinite(value)) return '0%';
    const num = Number(value) * 100;
    let digits = 2;
    const abs = Math.abs(num);
    if (abs >= 100) digits = 0;
    else if (abs >= 10) digits = 1;
    else if (abs < 1) digits = 4;
    let formatted = num.toFixed(digits);
    formatted = formatted.replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1');
    const sign = num >= 0 ? '+' : '';
    return `${sign}${formatted}%`;
  }

  function normaliseStacking(stacking) {
    const minimum = toNumber(stacking?.minimum, 0);
    const step = Math.max(1, toNumber(stacking?.step, 1));
    const maximumValue = toNumber(stacking?.maximum, null);
    const uncapped = maximumValue === null;
    const inlineParts = [`Min ${minimum}`, `Step ${step}`];
    inlineParts.push(uncapped ? 'Uncapped' : `Max ${maximumValue}`);
    const inline = inlineParts.join(' • ');
    const sentenceParts = [`Stacks start at ${minimum}.`, `Stacks increase by ${step} each time.`];
    sentenceParts.push(uncapped ? 'Stacks are uncapped by default.' : `Stacks cap at ${maximumValue}.`);
    return {
      minimum,
      step,
      maximum: maximumValue,
      uncapped,
      inline,
      sentence: sentenceParts.join(' ')
    };
  }

  function toNumber(value, fallback = null) {
    if (value == null) return fallback;
    const num = Number(value);
    return Number.isFinite(num) ? num : fallback;
  }

  function buildRewardSummaries(bonuses) {
    if (!bonuses || typeof bonuses !== 'object') {
      return { inline: '', tooltip: '' };
    }
    const inlineSegments = [];
    const tooltipSegments = [];

    const perStackExp = toNumber(bonuses.exp_bonus_per_stack);
    if (perStackExp) {
      inlineSegments.push(`${formatPercent(perStackExp)} EXP/stack`);
      tooltipSegments.push(`Each stack grants ${formatPercent(perStackExp)} EXP.`);
    }

    const perStackRdr = toNumber(bonuses.rdr_bonus_per_stack);
    if (perStackRdr) {
      inlineSegments.push(`${formatPercent(perStackRdr)} RDR/stack`);
      tooltipSegments.push(`Each stack grants ${formatPercent(perStackRdr)} RDR.`);
    }

    const firstExp = toNumber(bonuses.exp_bonus_first_stack);
    const additionalExp = toNumber(bonuses.exp_bonus_additional_stack);
    if (firstExp) {
      inlineSegments.push(
        `EXP: ${formatPercent(firstExp)} first${additionalExp ? `, ${formatPercent(additionalExp)} each extra` : ''}`
      );
      tooltipSegments.push(
        `The first stack adds ${formatPercent(firstExp)} EXP${
          additionalExp ? ` with ${formatPercent(additionalExp)} for each additional stack` : ''
        }.`
      );
    }

    const firstRdr = toNumber(bonuses.rdr_bonus_first_stack);
    const additionalRdr = toNumber(bonuses.rdr_bonus_additional_stack);
    if (firstRdr) {
      inlineSegments.push(
        `RDR: ${formatPercent(firstRdr)} first${additionalRdr ? `, ${formatPercent(additionalRdr)} each extra` : ''}`
      );
      tooltipSegments.push(
        `The first stack adds ${formatPercent(firstRdr)} RDR${
          additionalRdr ? ` with ${formatPercent(additionalRdr)} for each additional stack` : ''
        }.`
      );
    }

    const inline = inlineSegments.length ? `Rewards: ${inlineSegments.join(' • ')}` : '';
    const tooltip = tooltipSegments.length ? `Rewards: ${tooltipSegments.join(' ')}` : '';
    return { inline, tooltip };
  }

  function buildDiminishingSummary(diminishing) {
    if (!diminishing || typeof diminishing !== 'object' || !diminishing.applies) {
      return { inline: '', tooltip: '' };
    }
    const stat = (diminishing.stat || 'this modifier').replace(/_/g, ' ');
    const inline = `Diminishing: ${stat}`;
    const tooltip = `Diminishing returns apply to ${stat}.`;
    return { inline, tooltip };
  }

  function buildPreviewChips(mod, stacking) {
    const preview = Array.isArray(mod?.preview) ? mod.preview : [];
    return preview
      .map((entry) => ({
        stacks: toNumber(entry?.stacks, 0),
        rawStacks: entry?.stacks,
        label: formatStackLabel(entry?.stacks, stacking),
        detail: formatPreviewDetail(mod, entry || {})
      }))
      .filter((chip) => chip.detail)
      .sort((a, b) => a.stacks - b.stacks);
  }

  function buildPreviewSentence(chips, stacking) {
    if (!chips || chips.length === 0) return '';
    const highest = chips[chips.length - 1];
    if (!highest?.detail) return '';
    let sentence = `${highest.label} yields ${highest.detail}.`;
    if (stacking?.uncapped && Number.isFinite(highest.stacks)) {
      sentence += ' Stacks continue scaling beyond this preview because the modifier is uncapped.';
    }
    return sentence;
  }

  function formatStackLabel(value, stacking) {
    if (value == null || value === 'infinite' || value === Infinity) {
      if (stacking?.uncapped) {
        return '∞ stacks';
      }
      return 'Max stacks';
    }
    const stacks = toNumber(value, null);
    if (!Number.isFinite(stacks)) {
      return stacking?.uncapped ? '∞ stacks' : 'Stacks';
    }
    return `${stacks} stack${stacks === 1 ? '' : 's'}`;
  }

  function formatPreviewDetail(mod, entry) {
    if (!entry || typeof entry !== 'object') return '';
    if (entry.encounter_bonus != null || entry.defense_floor != null || entry.shop_multiplier != null) {
      const parts = [];
      if (entry.encounter_bonus != null) {
        const bonus = Number(entry.encounter_bonus) || 0;
        parts.push(`+${bonus} foe${bonus === 1 ? '' : 's'}`);
      }
      if (entry.defense_floor != null) {
        parts.push(`≥${Math.round(Number(entry.defense_floor) || 0)} DEF floor`);
      }
      if (entry.elite_spawn_bonus_pct != null) {
        parts.push(`+${formatPercentPoints(entry.elite_spawn_bonus_pct)} elite odds`);
      }
      if (entry.shop_multiplier != null) {
        parts.push(`Shop ${formatMultiplier(entry.shop_multiplier)}`);
      }
      return parts.join(' • ');
    }

    if (entry.effective_multiplier != null || entry.bonus_rdr != null || entry.bonus_exp != null) {
      const parts = [];
      if (entry.effective_multiplier != null) {
        parts.push(`Stats ${formatMultiplier(entry.effective_multiplier)}`);
      }
      if (entry.bonus_exp != null) {
        parts.push(`EXP ${formatPercent(entry.bonus_exp)}`);
      }
      if (entry.bonus_rdr != null) {
        parts.push(`RDR ${formatPercent(entry.bonus_rdr)}`);
      }
      return parts.join(' • ');
    }

    if (entry.effective_bonus != null || entry.raw_bonus != null) {
      const parts = [];
      if (entry.raw_bonus != null) {
        parts.push(`Raw ${formatPercent(entry.raw_bonus)}`);
      }
      if (entry.effective_bonus != null && entry.effective_bonus !== entry.raw_bonus) {
        parts.push(`Effective ${formatPercent(entry.effective_bonus)}`);
      }
      return parts.join(' • ');
    }

    if (entry.raw_bonus_pct != null) {
      return `Raw ${formatPercent(entry.raw_bonus_pct)}`;
    }

    return '';
  }

  function formatPercentPoints(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) return '0%';
    const abs = Math.abs(num);
    let digits = 2;
    if (abs >= 100) digits = 0;
    else if (abs >= 10) digits = 1;
    const formatted = num.toFixed(digits).replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1');
    return `${num >= 0 ? '+' : ''}${formatted}%`;
  }

  function formatMultiplier(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) return '×1';
    const abs = Math.abs(num);
    let digits = 2;
    if (abs >= 100) digits = 0;
    else if (abs >= 10) digits = 1;
    return `×${num.toFixed(digits).replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1')}`;
  }

  function sanitizeStack(modId, rawValue) {
    const definition = modifierMap.get(modId);
    if (!definition) {
      if (modId === 'pressure') {
        return Number.isFinite(Number(rawValue)) ? Math.max(0, Math.floor(Number(rawValue))) : 0;
      }
      return 0;
    }
    const stacking = definition.stacking || {};
    const minimum = Number.isFinite(Number(stacking.minimum)) ? Number(stacking.minimum) : 0;
    const maximum = Number.isFinite(Number(stacking.maximum)) ? Number(stacking.maximum) : null;
    const step = Number.isFinite(Number(stacking.step)) && Number(stacking.step) > 0 ? Number(stacking.step) : 1;
    let value = Number(rawValue);
    if (!Number.isFinite(value)) {
      value = Number(stacking.default ?? minimum ?? 0);
    }
    if (!Number.isFinite(value)) value = 0;
    value = Math.floor(value);
    if (value < minimum) value = minimum;
    if (maximum !== null && value > maximum) value = maximum;
    if (step > 1) {
      value = Math.round(value / step) * step;
      if (value < minimum) value = minimum;
      if (maximum !== null && value > maximum) value = maximum;
    }
    return value;
  }

  function applyRunTypeDefaults(targetId, { resetDirty = false } = {}) {
    const runType = runTypes.find((rt) => rt.id === targetId);
    if (!runType) return;
    const defaults = runType.default_modifiers || {};
    const nextValues = { ...modifierValues };
    const nextDirty = resetDirty ? { ...modifierDirty } : modifierDirty;

    // Reset non-dirty modifiers to their base defaults
    if (resetDirty) {
      for (const entry of modifiers) {
        if (!nextDirty[entry.id]) {
          nextValues[entry.id] = sanitizeStack(entry.id, entry.stacking?.default ?? entry.stacking?.minimum ?? 0);
        }
      }
    }

    for (const [modId, raw] of Object.entries(defaults)) {
      if (!modifierMap.has(modId)) continue;
      nextValues[modId] = sanitizeStack(modId, raw);
      if (resetDirty) {
        nextDirty[modId] = false;
      }
    }

    modifierValues = nextValues;
    if (resetDirty) {
      modifierDirty = nextDirty;
    }
  }

  function persistDefaults() {
    if (!browser) return;
    try {
      const metadataSignature = normalizeMetadataHash(metadata?.metadata_hash ?? metadata?.version);
      const payload = {
        runTypeId,
        modifiers: modifierValues,
        party: partySelection.slice(0, 5),
        damageType,
        metadataVersion: metadata?.version || null,
        metadataSignature
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (err) {
      console.warn('Failed to persist run wizard defaults', err);
    }
  }

  function logStepImpression(targetStep) {
    if (!targetStep || visitedSteps.has(targetStep)) return;
    visitedSteps = new Set(visitedSteps).add(targetStep);
    logWizardEvent('step_impression', { step: targetStep, run_type: runTypeId });
  }

  function logWizardEvent(event, detail = {}) {
    const payload = {
      session: wizardSessionId,
      step,
      run_type: runTypeId,
      metadata_version: metadata?.version || null,
      ...detail
    };
    logMenuAction('RunWizard', event, payload).catch(() => {});
  }

  function goToStep(target) {
    if (!STEP_SEQUENCE.includes(target)) return;
    if (target === 'resume' && !hasRuns) {
      step = 'party';
    } else {
      step = target;
    }
    logStepImpression(step);
    persistDefaults();
  }

  function handleResume() {
    if (resumeDisabled) return;
    const selected = normalizedRuns[resumeIndex];
    if (!selected) return;
    completed = true;
    logWizardEvent('resume_selected', { run_id: selected.run_id });
    dispatch('choose', { run: selected });
    dispatch('load', { run: selected });
  }

  function handlePartySave() {
    if (!partySelection.length) return;
    logWizardEvent('party_confirmed', { party_size: partySelection.length });
    goToStep('run-type');
  }

  function handlePartyCancel() {
    if (hasRuns) {
      goToStep('resume');
    } else {
      completed = true;
      dispatch('cancel');
    }
  }

  function handleRunTypeSelect(id) {
    if (!id || id === runTypeId) return;
    if (!runTypes.some((rt) => rt.id === id)) return;
    runTypeId = id;
    applyRunTypeDefaults(runTypeId, { resetDirty: true });
    persistDefaults();
    lastAppliedPresetFingerprint = null;
    logWizardEvent('run_type_selected', { run_type: runTypeId });
  }

  function handleModifierChange(modId, raw) {
    if (!modifierMap.has(modId)) return;
    if (raw === '') {
      modifierValues = { ...modifierValues, [modId]: '' };
      modifierDirty = { ...modifierDirty, [modId]: true };
      lastAppliedPresetFingerprint = null;
      return;
    }
    const sanitized = sanitizeStack(modId, raw);
    modifierValues = { ...modifierValues, [modId]: sanitized };
    modifierDirty = { ...modifierDirty, [modId]: true };
    persistDefaults();
    lastAppliedPresetFingerprint = null;
    logWizardEvent('modifier_adjusted', { modifier: modId, value: sanitized });
  }

  function resetModifiers() {
    for (const entry of modifiers) {
      modifierDirty[entry.id] = false;
    }
    modifierDirty = { ...modifierDirty };
    applyRunTypeDefaults(runTypeId, { resetDirty: true });
    persistDefaults();
    lastAppliedPresetFingerprint = null;
    logWizardEvent('modifiers_reset', { run_type: runTypeId });
  }

  function goToModifiers() {
    logWizardEvent('run_type_confirmed', { run_type: runTypeId });
    goToStep('modifiers');
  }

  function goToConfirm() {
    logWizardEvent('modifiers_confirmed', {
      run_type: runTypeId,
      modifiers: summarizeActiveModifiers()
    });
    goToStep('confirm');
  }

  function summarizeActiveModifiers() {
    const summary = {};
    for (const entry of modifiers) {
      const value = sanitizeStack(entry.id, modifierValues[entry.id]);
      if (value > (entry.stacking?.minimum ?? 0)) {
        summary[entry.id] = value;
      }
    }
    return summary;
  }

  function startRun() {
    if (submitting) return;
    submitting = true;
    const payload = {
      party: partySelection.slice(0, 5),
      damageType,
      pressure: pressureValue,
      runType: runTypeId,
      modifiers: normalizeModifierPayload(),
      metadataVersion: metadata?.version || null
    };
    completed = true;
    logWizardEvent('start_submitted', {
      run_type: runTypeId,
      modifiers: payload.modifiers,
      party_size: payload.party.length,
      pressure: payload.pressure,
      preset_fingerprint: lastAppliedPresetFingerprint,
      quick_start: Boolean(lastAppliedPresetFingerprint)
    });
    rememberPreset(payload.modifiers);
    lastAppliedPresetFingerprint = null;
    dispatch('startRun', payload);
    setTimeout(() => {
      submitting = false;
    }, 500);
  }

  function normalizeModifierPayload() {
    const payload = {};
    for (const entry of modifiers) {
      payload[entry.id] = sanitizeStack(entry.id, modifierValues[entry.id]);
    }
    return payload;
  }

  function handleCancel() {
    completed = true;
    logWizardEvent('cancelled', { step });
    dispatch('cancel');
  }

  function computeRewardPreview(values, availableModifiers = modifiers) {
    const result = {
      foe_bonus: 0,
      player_bonus: 0,
      exp_bonus: 0,
      rdr_bonus: 0
    };
    if (!Array.isArray(availableModifiers) || availableModifiers.length === 0) {
      return result;
    }
    for (const entry of availableModifiers) {
      const stacks = sanitizeStack(entry.id, values[entry.id]);
      const contribution = computeModifierRewardContribution(entry, stacks);
      result.foe_bonus += contribution.foe_bonus;
      result.player_bonus += contribution.player_bonus;
      result.exp_bonus += contribution.exp_bonus;
      result.rdr_bonus += contribution.rdr_bonus;
    }
    result.foe_bonus = Number(result.foe_bonus.toFixed(4));
    result.player_bonus = Number(result.player_bonus.toFixed(4));
    result.exp_bonus = Number(result.exp_bonus.toFixed(4));
    result.rdr_bonus = Number(result.rdr_bonus.toFixed(4));
    return result;
  }

  function computeModifierRewardContribution(mod, stacks) {
    const totals = {
      foe_bonus: 0,
      player_bonus: 0,
      exp_bonus: 0,
      rdr_bonus: 0
    };
    if (!mod || !mod.reward_bonuses || typeof mod.reward_bonuses !== 'object') {
      return totals;
    }

    const bonuses = mod.reward_bonuses;
    const perStackReward = toNumber(bonuses.exp_bonus_per_stack ?? bonuses.rdr_bonus_per_stack);
    if (perStackReward && mod.grants_reward_bonus) {
      totals.foe_bonus += stacks * perStackReward;
    }

    const perStackExp = toNumber(bonuses.exp_bonus_per_stack);
    if (perStackExp) {
      totals.exp_bonus += stacks * perStackExp;
    }

    const perStackRdr = toNumber(bonuses.rdr_bonus_per_stack);
    if (perStackRdr) {
      totals.rdr_bonus += stacks * perStackRdr;
    }

    const firstExp = toNumber(bonuses.exp_bonus_first_stack);
    if (firstExp && stacks > 0) {
      totals.exp_bonus += firstExp;
      const additionalExp = toNumber(bonuses.exp_bonus_additional_stack);
      if (additionalExp && stacks > 1) {
        totals.exp_bonus += (stacks - 1) * additionalExp;
      }
    }

    const firstRdr = toNumber(bonuses.rdr_bonus_first_stack);
    if (firstRdr && stacks > 0) {
      totals.rdr_bonus += firstRdr;
      const additionalRdr = toNumber(bonuses.rdr_bonus_additional_stack);
      if (additionalRdr && stacks > 1) {
        totals.rdr_bonus += (stacks - 1) * additionalRdr;
      }
      if (!mod.grants_reward_bonus) {
        totals.player_bonus += firstRdr;
        if (additionalRdr && stacks > 1) {
          totals.player_bonus += (stacks - 1) * additionalRdr;
        }
      }
    }

    if (!mod.grants_reward_bonus && mod.id === 'character_stat_down') {
      totals.player_bonus = totals.rdr_bonus;
    }

    return totals;
  }

  function modifierLabel(mod) {
    return mod?.label || mod?.id || 'Modifier';
  }

  function modifierDescription(mod) {
    return mod?.description || '';
  }

  function pressureTooltip() {
    return metadata?.pressure?.tooltip || '';
  }

  function isActiveModifier(mod) {
    const value = typeof mod?.value === 'number' ? mod.value : sanitizeStack(mod.id, modifierValues[mod.id]);
    return value > (mod.stacking?.minimum ?? 0);
  }

  function formatRewardBonus(value) {
    if (!Number.isFinite(value)) return '0%';
    return formatPercent(value);
  }
</script>

<svelte:window on:keydown={(event) => {
  if (event.key === 'Escape') {
    handleCancel();
  }
}} />

{#if step === 'party'}
  <div class="party-standalone" data-step={step}>
    <div class="party-step">
      <PartyPicker
        bind:selected={partySelection}
        allowElementChange={true}
        actionLabel="Continue"
        {reducedMotion}
        on:save={handlePartySave}
        on:cancel={handlePartyCancel}
        on:editorChange={(event) => {
          const detail = event.detail || {};
          if (detail?.damageType) {
            damageType = String(detail.damageType);
            persistDefaults();
          }
        }}
      />
    </div>
  </div>
{:else}
  <MenuPanel
    class={`run-wizard${step === 'modifiers' ? ' modifiers-stage' : ''}`}
    data-step={step}
    padding="var(--menu-panel-padding, clamp(0.65rem, 1.8vw, 1.1rem))"
    {reducedMotion}
  >
    <div class="wizard">
      <header class="wizard-header">
        <h2>{stepTitle}</h2>
        <div class="step-indicator" aria-hidden="true">
          {#each visibleSteps as key, index}
            <span class:selected={key === step} class:done={index < currentStepIndex}>
              {index + 1}
            </span>
          {/each}
        </div>
      </header>

      {#if step === 'resume'}
      <div class="resume-panel step-surface">
        {#if normalizedRuns.length > 0}
          <div class="runs" role="list">
            {#each normalizedRuns as run, i}
              <label class="run-item" role="listitem">
                <input
                  type="radio"
                  name="resume-run"
                  bind:group={resumeIndex}
                  value={i}
                />
                <div class="summary">
                  <div class="id">{run.run_id}</div>
                  <div class="details">
                    Floor {run?.map?.floor || 1}, Room {run?.map?.current || 1}, Pressure {run?.map?.rooms?.[0]?.pressure ?? 0}
                  </div>
                </div>
              </label>
            {/each}
          </div>
          <div class="actions">
            <button class="icon-btn" on:click={handleResume} disabled={resumeDisabled}>Resume Run</button>
            <button class="icon-btn primary" on:click={() => goToStep('party')}>Start Guided Setup</button>
          </div>
        {:else}
          <p>No active runs found.</p>
          <div class="actions">
            <button class="icon-btn primary" on:click={() => goToStep('party')}>Start Guided Setup</button>
          </div>
        {/if}
      </div>
    {:else if step === 'run-type'}
      <div class="run-type-panel step-surface">
        {#if metadataLoading}
          <p class="loading">Loading configuration...</p>
        {:else if metadataError}
          <div class="error">
            <p>{metadataError}</p>
            <button class="icon-btn" on:click={() => fetchMetadata({ forceRefresh: true })}>Retry</button>
          </div>
        {:else}
          <div class="run-types" role="list">
            {#each runTypes as rt}
              <button
                type="button"
                class="run-type-card"
                class:active={rt.id === runTypeId}
                on:click={() => handleRunTypeSelect(rt.id)}
                role="listitem"
              >
                <div class="card-title">{rt.label}</div>
                <p class="card-description">{rt.description}</p>
                {#if Object.keys(rt.default_modifiers || {}).length > 0}
                  <div class="card-defaults">
                    <strong>Defaults</strong>
                    <ul>
                      {#each Object.entries(rt.default_modifiers || {}) as [key, value]}
                        <li>{modifierMap.get(key)?.label || key}: {value}</li>
                      {/each}
                    </ul>
                  </div>
                {/if}
              </button>
            {/each}
          </div>
        {/if}
      </div>
      <div class="navigation">
        <button class="ghost" on:click={() => goToStep('party')}>Back</button>
        <button class="primary" on:click={goToModifiers} disabled={!runTypeId || metadataLoading || metadataError}>Next</button>
      </div>
    {:else if step === 'modifiers'}
      <div class="modifier-panel step-surface">
        {#if metadataLoading}
          <p class="loading">Loading configuration...</p>
        {:else if metadataError}
          <div class="error">
            <p>{metadataError}</p>
            <button class="icon-btn" on:click={() => fetchMetadata({ forceRefresh: true })}>Retry</button>
          </div>
        {:else}
          <div class="modifier-toolbar">
            <div>
              <strong>Pressure:</strong>
              <span class="pressure-value">{pressureValue}</span>
            </div>
            {#if pressureTooltip()}
              <p class="pressure-tooltip">{pressureTooltip()}</p>
            {/if}
            <button class="icon-btn" on:click={resetModifiers}>Reset to {activeRunType?.label || 'defaults'}</button>
          </div>
          {#if quickStartPresets.length > 0}
            <div class="recent-presets" role="region" aria-label="Recent modifier presets">
              <div class="recent-header">
                <strong>Recent Presets</strong>
                {#if metadata?.version}
                  <span class="metadata-hash">Metadata {metadata.version}</span>
                {/if}
              </div>
              <div class="preset-list" role="list">
                {#each quickStartPresets as preset, index}
                  <button
                    type="button"
                    class="preset-card"
                    role="listitem"
                    on:click={() => applyPreset(preset, index)}
                    aria-label={presetButtonLabel(preset, index)}
                  >
                    <div class="preset-title">Preset {index + 1}</div>
                    <div class="preset-stacks">{preset.stacks.join(' • ')}</div>
                    <div class="preset-reward-grid">
                      <div>
                        <span class="preview-label">EXP</span>
                        <span class="preview-value">{formatRewardBonus(preset.reward.exp_bonus)}</span>
                      </div>
                      <div>
                        <span class="preview-label">RDR</span>
                        <span class="preview-value">{formatRewardBonus(preset.reward.rdr_bonus)}</span>
                      </div>
                      <div>
                        <span class="preview-label">Foe</span>
                        <span class="preview-value">{formatRewardBonus(preset.reward.foe_bonus)}</span>
                      </div>
                      <div>
                        <span class="preview-label">Player</span>
                        <span class="preview-value">{formatRewardBonus(preset.reward.player_bonus)}</span>
                      </div>
                    </div>
                    {#if preset.metadataVersion}
                      <div
                        class="preset-metadata"
                        class:stale={
                          currentMetadataHash &&
                          preset.metadataSignature &&
                          preset.metadataSignature !== currentMetadataHash
                        }
                      >
                        Metadata {preset.metadataVersion}
                      </div>
                    {/if}
                  </button>
                {/each}
              </div>
            </div>
          {/if}
          <div class="modifiers" role="list">
            {#each selectedModifiers as mod}
              <div class="modifier" role="listitem">
                <div class="modifier-header">
                  <div class="modifier-title">
                    <span class="modifier-label">{modifierLabel(mod)}</span>
                    {#if mod.category}
                      <span class="modifier-category">{mod.category}</span>
                    {/if}
                  </div>
                  <div class="modifier-controls">
                    {#if mod.meta?.tooltipText}
                      <Tooltip text={mod.meta.tooltipText}>
                        <button
                          type="button"
                          class="info-trigger"
                          aria-label={mod.meta.tooltipLabel}
                          data-tooltip={mod.meta.tooltipText}
                        >
                          <span aria-hidden="true">i</span>
                        </button>
                      </Tooltip>
                    {/if}
                    <label>
                      <span class="sr-only">Stacks</span>
                      <input
                        type="number"
                        min={mod.stacking?.minimum ?? 0}
                        step={mod.stacking?.step ?? 1}
                        max={Number.isFinite(mod.stacking?.maximum) ? mod.stacking.maximum : undefined}
                        value={modifierValues[mod.id] ?? ''}
                        on:input={(event) => handleModifierChange(mod.id, event.target.value)}
                      />
                    </label>
                  </div>
                </div>
                {#if mod.meta?.stackSummary || mod.meta?.effectsSummary || mod.meta?.rewardSummary || mod.meta?.diminishingSummary}
                  <div class="modifier-meta">
                    {#if mod.meta?.stackSummary}
                      <span>{mod.meta.stackSummary}</span>
                    {/if}
                    {#if mod.meta?.effectsSummary}
                      <span>{mod.meta.effectsSummary}</span>
                    {/if}
                    {#if mod.meta?.rewardSummary}
                      <span>{mod.meta.rewardSummary}</span>
                    {/if}
                    {#if mod.meta?.diminishingSummary}
                      <span>{mod.meta.diminishingSummary}</span>
                    {/if}
                  </div>
                {/if}
                {#if modifierDescription(mod)}
                  <p class="modifier-description">{modifierDescription(mod)}</p>
                {/if}
                {#if mod.meta?.previewChips?.length}
                  <div class="modifier-preview" role="list">
                    {#each mod.meta.previewChips as chip}
                      <div class="preview-chip" role="listitem">
                        <span class="chip-stack">{chip.label}</span>
                        <span class="chip-detail">{chip.detail}</span>
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
          <div class="reward-preview">
            <div>
              <strong>Reward Preview</strong>
            </div>
            <div class="preview-grid">
              <div>
                <span class="preview-label">EXP Bonus</span>
                <span class="preview-value">{formatRewardBonus(rewardPreview.exp_bonus)}</span>
              </div>
              <div>
                <span class="preview-label">RDR Bonus</span>
                <span class="preview-value">{formatRewardBonus(rewardPreview.rdr_bonus)}</span>
              </div>
              <div>
                <span class="preview-label">Foe Bonus</span>
                <span class="preview-value">{formatRewardBonus(rewardPreview.foe_bonus)}</span>
              </div>
              <div>
                <span class="preview-label">Player Bonus</span>
                <span class="preview-value">{formatRewardBonus(rewardPreview.player_bonus)}</span>
              </div>
            </div>
          </div>
        {/if}
      </div>
      <div class="navigation">
        <button class="ghost" on:click={() => goToStep('run-type')}>Back</button>
        <button class="primary" on:click={goToConfirm} disabled={metadataLoading || metadataError}>Next</button>
      </div>
    {:else if step === 'confirm'}
      <div class="confirm-panel step-surface">
        <section>
          <h3>Party</h3>
          <ul>
            {#each partySummary as member}
              <li>{member}</li>
            {/each}
          </ul>
        </section>
        <section>
          <h3>Run Type</h3>
          <p>{activeRunType?.label || runTypeId}</p>
          <p class="card-description">{activeRunType?.description}</p>
        </section>
        <section>
          <h3>Modifiers</h3>
          {#if selectedModifiers.some(isActiveModifier)}
            <ul>
              {#each selectedModifiers.filter(isActiveModifier) as mod}
                <li>{modifierLabel(mod)}: {mod.value}</li>
              {/each}
            </ul>
          {:else}
            <p>No additional modifiers selected.</p>
          {/if}
        </section>
        <section>
          <h3>Reward Preview</h3>
          <div class="preview-grid">
            <div>
              <span class="preview-label">EXP Bonus</span>
              <span class="preview-value">{formatRewardBonus(rewardPreview.exp_bonus)}</span>
            </div>
            <div>
              <span class="preview-label">RDR Bonus</span>
              <span class="preview-value">{formatRewardBonus(rewardPreview.rdr_bonus)}</span>
            </div>
            <div>
              <span class="preview-label">Foe Bonus</span>
              <span class="preview-value">{formatRewardBonus(rewardPreview.foe_bonus)}</span>
            </div>
            <div>
              <span class="preview-label">Player Bonus</span>
              <span class="preview-value">{formatRewardBonus(rewardPreview.player_bonus)}</span>
            </div>
          </div>
        </section>
      </div>
      <div class="navigation">
        <button class="ghost" on:click={() => goToStep('modifiers')}>Back</button>
        <button class="primary" on:click={startRun} disabled={submitting}>Start Run</button>
      </div>
    {/if}
    </div>
  </MenuPanel>
{/if}

<style>
  .wizard {
    --wizard-max-width: 100%;
    --wizard-inner-max-width: 100%;
    --wizard-section-gap: clamp(0.65rem, 1.8vw, 1.1rem);
    --wizard-item-gap: clamp(0.45rem, 1.4vw, 0.8rem);
    --wizard-action-gap: clamp(0.55rem, 1.6vw, 0.95rem);
    display: flex;
    flex-direction: column;
    gap: var(--wizard-section-gap);
    width: var(--wizard-max-width);
    max-width: var(--wizard-max-width);
    flex: 1 1 auto;
    align-self: stretch;
    margin: 0;
    min-height: 0;
    height: 100%;
  }

  .wizard > * {
    min-width: 0;
  }

  .wizard-header,
  .step-surface,
  .navigation {
    width: min(100%, var(--wizard-inner-max-width));
    margin-left: auto;
    margin-right: auto;
  }

  .wizard-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: clamp(0.6rem, 1.6vw, 1rem);
    flex-wrap: wrap;
  }

  .wizard-header h2 {
    margin: 0;
    font-size: clamp(1.25rem, 2.2vw, 1.6rem);
    font-weight: 600;
    flex: 1 1 auto;
    min-width: min(12rem, 100%);
  }

  .step-indicator {
    display: inline-flex;
    flex-wrap: wrap;
    gap: clamp(0.35rem, 1vw, 0.55rem);
    justify-content: flex-end;
  }

  .step-indicator span {
    width: 1.75rem;
    height: 1.75rem;
    border-radius: 50%;
    border: 1px solid rgba(255, 255, 255, 0.3);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    opacity: 0.5;
  }

  .step-indicator span.selected {
    background: rgba(120, 180, 255, 0.3);
    opacity: 1;
  }

  .step-indicator span.done {
    background: rgba(120, 180, 255, 0.16);
    opacity: 0.85;
  }

  .step-surface {
    width: 100%;
    box-sizing: border-box;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: clamp(0.65rem, 1.8vw, 1.1rem);
    display: flex;
    flex-direction: column;
    gap: var(--wizard-section-gap);
    flex: 1 1 auto;
    min-height: 0;
  }

  .resume-panel {
    padding: clamp(0.55rem, 1.6vw, 0.9rem);
  }

  .runs {
    display: flex;
    flex-direction: column;
    gap: var(--wizard-item-gap);
    margin: 0;
  }

  .run-item {
    display: flex;
    gap: clamp(0.55rem, 1.4vw, 0.9rem);
    align-items: flex-start;
    background: rgba(255, 255, 255, 0.06);
    padding: clamp(0.5rem, 1.5vw, 0.85rem);
    min-width: 0;
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .run-item input {
    margin-top: 0.25rem;
  }

  .summary {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    flex: 1 1 auto;
    min-width: 0;
  }

  .id {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.8rem;
    opacity: 0.9;
    word-break: break-word;
  }

  .details {
    font-size: 0.85rem;
    opacity: 0.85;
    line-height: 1.35;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
    gap: var(--wizard-action-gap);
    margin-top: clamp(0.35rem, 1vw, 0.6rem);
    flex-wrap: wrap;
  }

  .icon-btn {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 0;
    padding: clamp(0.45rem, 1.4vw, 0.75rem) clamp(0.75rem, 2vw, 1.2rem);
    cursor: pointer;
    color: inherit;
    transition: background 0.18s ease;
  }

  .actions .icon-btn {
    flex: 1 1 160px;
    min-width: min(220px, 100%);
  }

  .icon-btn:hover {
    background: rgba(120, 180, 255, 0.22);
  }

  .icon-btn.primary {
    background: rgba(120, 180, 255, 0.28);
  }

  .icon-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .party-standalone {
    --wizard-section-gap: clamp(0.65rem, 1.8vw, 1.1rem);
    display: flex;
    flex: 1 1 auto;
    width: 100%;
    min-height: 0;
  }

  .party-step {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    gap: var(--wizard-section-gap, clamp(0.65rem, 1.8vw, 1.1rem));
    width: 100%;
    min-height: 0;
  }

  .party-step :global(.panel) {
    flex: 1 1 auto;
    min-height: 100%;
  }

  .navigation {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: var(--wizard-action-gap);
    flex-wrap: wrap;
    margin-top: clamp(0.35rem, 1vw, 0.6rem);
  }

  .navigation button {
    padding: clamp(0.5rem, 1.5vw, 0.85rem) clamp(1rem, 2.6vw, 1.6rem);
    border: none;
    cursor: pointer;
    border-radius: 0;
    font-size: 0.95rem;
    flex: 1 1 160px;
    min-width: min(220px, 100%);
  }

  .navigation .ghost {
    background: transparent;
    color: inherit;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .navigation .primary {
    background: rgba(120, 180, 255, 0.35);
    color: inherit;
  }

  .navigation button:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .run-types {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: var(--wizard-item-gap);
  }

  .run-type-card {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid transparent;
    padding: clamp(0.65rem, 1.6vw, 1rem);
    text-align: left;
    cursor: pointer;
    color: inherit;
    display: flex;
    flex-direction: column;
    gap: clamp(0.35rem, 1vw, 0.6rem);
    min-width: 0;
  }

  .run-type-card:hover,
  .run-type-card.active {
    border-color: rgba(120, 180, 255, 0.5);
    background: rgba(120, 180, 255, 0.12);
  }

  .card-title {
    font-weight: 600;
    margin: 0;
  }

  .card-description {
    font-size: 0.9rem;
    opacity: 0.85;
    margin: 0;
    line-height: 1.45;
  }

  .card-defaults {
    margin: 0;
    font-size: 0.85rem;
    opacity: 0.85;
    line-height: 1.35;
  }

  .card-defaults ul {
    margin: 0.25rem 0 0;
    padding-left: 1rem;
  }

  .modifier-panel {
    display: flex;
    flex-direction: column;
    gap: var(--wizard-section-gap);
    flex: 1 1 auto;
    min-height: 0;
  }

  .modifier-toolbar {
    display: flex;
    flex-direction: column;
    gap: clamp(0.35rem, 1vw, 0.6rem);
    background: rgba(255, 255, 255, 0.05);
    padding: clamp(0.55rem, 1.6vw, 0.9rem) clamp(0.7rem, 2vw, 1.2rem);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .recent-presets {
    display: flex;
    flex-direction: column;
    gap: clamp(0.45rem, 1vw, 0.75rem);
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: clamp(0.55rem, 1.6vw, 0.9rem) clamp(0.7rem, 2vw, 1.2rem);
  }

  .recent-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .metadata-hash {
    font-size: 0.75rem;
    opacity: 0.6;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .preset-list {
    display: grid;
    gap: clamp(0.45rem, 1.2vw, 0.75rem);
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .preset-card {
    text-align: left;
    display: flex;
    flex-direction: column;
    gap: clamp(0.35rem, 1vw, 0.55rem);
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: clamp(0.5rem, 1.6vw, 0.85rem);
    color: inherit;
    cursor: pointer;
  }

  .preset-card:hover,
  .preset-card:focus-visible {
    border-color: rgba(120, 180, 255, 0.5);
    background: rgba(120, 180, 255, 0.12);
    outline: none;
  }

  .preset-title {
    font-weight: 600;
    font-size: 0.95rem;
  }

  .preset-stacks {
    font-size: 0.85rem;
    opacity: 0.85;
  }

  .preset-reward-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.35rem;
  }

  .preset-reward-grid .preview-label {
    font-size: 0.7rem;
    opacity: 0.65;
  }

  .preset-reward-grid .preview-value {
    font-size: 0.85rem;
  }

  .preset-metadata {
    font-size: 0.7rem;
    opacity: 0.65;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .preset-metadata.stale {
    color: #f7ba61;
    opacity: 0.95;
  }

  :global(.panel.run-wizard.modifiers-stage) {
    overflow: hidden;
  }

  :global(.panel.run-wizard.modifiers-stage .panel-content) {
    height: 100%;
  }

  .pressure-value {
    font-weight: 600;
    margin-left: 0.35rem;
  }

  .pressure-tooltip {
    font-size: 0.85rem;
    opacity: 0.8;
    margin: 0;
  }

  .modifiers {
    display: flex;
    flex-direction: column;
    gap: var(--wizard-item-gap);
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    padding-right: 0.35rem;
  }

  .modifier {
    background: rgba(255, 255, 255, 0.05);
    padding: clamp(0.6rem, 1.6vw, 1rem);
    display: flex;
    flex-direction: column;
    gap: clamp(0.35rem, 1vw, 0.55rem);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .modifier-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: clamp(0.45rem, 1.2vw, 0.75rem);
    flex-wrap: wrap;
  }

  .modifier-title {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.35rem;
  }

  .modifier-label {
    font-weight: 600;
  }

  .modifier-category {
    font-size: 0.75rem;
    opacity: 0.7;
    margin-left: 0.4rem;
    text-transform: uppercase;
  }

  .modifier-controls {
    display: flex;
    flex-wrap: wrap;
    gap: clamp(0.35rem, 1vw, 0.6rem);
    align-items: center;
  }

  .modifier-controls input {
    width: 5rem;
    padding: 0.35rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: inherit;
  }

  .info-trigger {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.8rem;
    height: 1.8rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.06);
    color: inherit;
    cursor: pointer;
    font-size: 0.9rem;
    line-height: 1;
  }

  .info-trigger:hover,
  .info-trigger:focus-visible {
    background: rgba(120, 180, 255, 0.22);
    outline: none;
  }

  .modifier-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    font-size: 0.75rem;
    opacity: 0.85;
  }

  .modifier-meta span {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 0.2rem 0.45rem;
  }

  .modifier-description {
    font-size: 0.85rem;
    opacity: 0.82;
    margin: 0;
    line-height: 1.4;
  }

  .modifier-preview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: clamp(0.35rem, 1vw, 0.6rem);
  }

  .preview-chip {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: clamp(0.4rem, 1.2vw, 0.65rem);
  }

  .chip-stack {
    font-size: 0.75rem;
    opacity: 0.7;
    text-transform: uppercase;
  }

  .chip-detail {
    font-size: 0.85rem;
    font-weight: 600;
  }

  .reward-preview {
    display: flex;
    flex-direction: column;
    gap: clamp(0.4rem, 1.2vw, 0.7rem);
  }

  .preview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: var(--wizard-item-gap);
  }

  .preview-label {
    font-size: 0.75rem;
    opacity: 0.75;
    display: block;
  }

  .preview-value {
    font-size: 1rem;
    font-weight: 600;
  }

  .confirm-panel {
    display: grid;
    gap: var(--wizard-section-gap);
  }

  .confirm-panel section {
    background: rgba(255, 255, 255, 0.05);
    padding: clamp(0.65rem, 1.6vw, 1rem);
    display: flex;
    flex-direction: column;
    gap: clamp(0.35rem, 1vw, 0.6rem);
  }

  .confirm-panel h3 {
    margin: 0;
  }

  .confirm-panel ul,
  .confirm-panel p {
    margin: 0;
  }

  .loading {
    opacity: 0.8;
  }

  .error {
    display: flex;
    flex-direction: column;
    gap: clamp(0.45rem, 1.2vw, 0.7rem);
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

  @media (min-width: 768px) {
    .actions .icon-btn,
    .navigation button {
      flex: 0 0 auto;
      min-width: 0;
    }
  }

  @media (max-width: 720px) {
    .wizard {
      --wizard-inner-max-width: 100%;
    }

    .wizard-header {
      align-items: flex-start;
    }

    .step-indicator {
      justify-content: flex-start;
    }

    .actions,
    .navigation {
      justify-content: stretch;
    }

    .actions .icon-btn,
    .navigation button {
      flex: 1 1 120px;
    }
  }

  @media (max-width: 480px) {
    .step-indicator span {
      width: 1.5rem;
      height: 1.5rem;
      font-size: 0.8rem;
    }

    .run-types {
      grid-template-columns: minmax(0, 1fr);
    }

    .modifier-controls input {
      width: min(100%, 5.5rem);
    }
  }
</style>
