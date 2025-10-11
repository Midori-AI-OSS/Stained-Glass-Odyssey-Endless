<script>
  import { browser } from '$app/environment';
  import { createEventDispatcher, onDestroy, onMount } from 'svelte';

import MenuPanel from './MenuPanel.svelte';
import PartyPicker from './PartyPicker.svelte';
import ModifierList from './ModifierList.svelte';
import RewardPreviewCard from './RewardPreviewCard.svelte';
import RunTypeGrid from './RunTypeGrid.svelte';
import RunWizardHeader from './RunWizardHeader.svelte';
import WizardNavigation from './WizardNavigation.svelte';
  import { formatPercent } from '../utils/upgradeFormatting.js';
  import { computeRewardPreview as calculateRewardPreview } from '../utils/rewardPreview.js';
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

      // Preserve user modifications when metadata loads/reloads
      const userModifiedKeys = new Set(
        Object.entries(modifierDirty)
          .filter(([_, isDirty]) => isDirty)
          .map(([modId]) => modId)
      );
      
      const baseState = buildBaseModifierState();
      
      // Start with base state
      const nextValues = baseState.values;
      const nextDirty = baseState.dirty;
      
      // Restore user-modified values
      for (const modId of userModifiedKeys) {
        if (modifierValues[modId] !== undefined) {
          nextValues[modId] = sanitizeStack(modId, modifierValues[modId]);
          nextDirty[modId] = true;
        }
      }
      
      modifierValues = nextValues;
      modifierDirty = nextDirty;
      
      // Apply run type defaults, but don't reset dirty flags that are already set
      applyRunTypeDefaults(runTypeId, { resetDirty: false });
      
      // Now mark user-modified values as dirty again
      for (const modId of userModifiedKeys) {
        modifierDirty[modId] = true;
      }
      
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
    let maximum = null;
    if (typeof stacking.maximum === 'number' && Number.isFinite(stacking.maximum)) {
      maximum = stacking.maximum;
    } else if (
      stacking.maximum !== null &&
      stacking.maximum !== undefined &&
      Number.isFinite(Number(stacking.maximum))
    ) {
      maximum = Number(stacking.maximum);
    }
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
      const clonedModifiers = {};
      if (modifierValues && typeof modifierValues === 'object') {
        for (const [key, value] of Object.entries(modifierValues)) {
          clonedModifiers[key] = value;
        }
      }
      const clonedParty = partySelection.slice(0, 5);
      const payload = {
        runTypeId,
        modifiers: clonedModifiers,
        party: clonedParty,
        damageType,
        metadataVersion: metadata?.version || null,
        metadataSignature
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
      persistedDefaults = {
        ...payload,
        modifiers: { ...clonedModifiers },
        party: [...clonedParty]
      };
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
    if (!modifierMap.has(modId) && modId !== 'pressure') return;
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
    return calculateRewardPreview(values, availableModifiers, {
      sanitizeStack: (modId, rawValue) => sanitizeStack(modId, rawValue)
    });
  }

  function modifierLabel(mod) {
    return mod?.label || mod?.id || 'Modifier';
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
      <RunWizardHeader
        title={stepTitle}
        steps={visibleSteps}
        activeStep={step}
        currentIndex={currentStepIndex}
      />

      {#if step === 'resume'}
        <section class="resume-panel step-surface">
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
              <button class="wizard-button ghost" on:click={handleResume} disabled={resumeDisabled}>Resume Run</button>
              <button class="wizard-button primary" on:click={() => goToStep('party')}>Start Guided Setup</button>
            </div>
          {:else}
            <p class="empty">No active runs found.</p>
            <div class="actions">
              <button class="wizard-button primary" on:click={() => goToStep('party')}>Start Guided Setup</button>
            </div>
          {/if}
        </section>
      {:else if step === 'run-type'}
        <section class="run-type-panel step-surface">
          <RunTypeGrid
            {runTypes}
            activeId={runTypeId}
            loading={metadataLoading}
            error={metadataError}
            onRetry={() => fetchMetadata({ forceRefresh: true })}
            onSelect={handleRunTypeSelect}
            getModifierLabel={(key) => modifierMap.get(key)?.label || key}
          />
        </section>
        <WizardNavigation
          backLabel="Back"
          onBack={() => goToStep('party')}
          onNext={goToModifiers}
          nextDisabled={!runTypeId || metadataLoading || metadataError}
        />
      {:else if step === 'modifiers'}
        <section class="modifier-panel step-surface">
          {#if metadataLoading}
            <p class="loading">Loading configuration...</p>
          {:else if metadataError}
            <div class="error">
              <p>{metadataError}</p>
              <button class="summary-button ghost" type="button" on:click={() => fetchMetadata({ forceRefresh: true })}>
                Retry
              </button>
            </div>
          {:else}
            <div class="modifier-layout">
              <div class="modifier-column">
                <ModifierList modifiers={selectedModifiers} values={modifierValues} onChange={handleModifierChange} />
              </div>
              <aside class="summary-column">
                <section class="summary-card metadata-card">
                  <header>
                    <h3>Run Defaults</h3>
                    {#if metadata?.version}
                      <span class="metadata-badge">Metadata {metadata.version}</span>
                    {/if}
                  </header>
                  <div class="pressure-row">
                    <span>Pressure</span>
                    <span class="pressure-value">{pressureValue}</span>
                  </div>
                  {#if pressureTooltip()}
                    <p class="pressure-tooltip">{pressureTooltip()}</p>
                  {/if}
                  <button
                    type="button"
                    class="summary-button ghost"
                    on:click={resetModifiers}
                  >
                    Reset to {activeRunType?.label || 'defaults'}
                  </button>
                </section>
                {#if quickStartPresets.length > 0}
                  <section class="summary-card presets-card" role="region" aria-label="Recent modifier presets">
                    <header>
                      <h3>Recent Presets</h3>
                      {#if currentMetadataHash}
                        <span class="metadata-badge">Signature {currentMetadataHash}</span>
                      {/if}
                    </header>
                    <div class="preset-list" role="list">
                      {#each quickStartPresets as preset, index}
                        <button
                          type="button"
                          class="preset-card"
                          role="listitem"
                          on:click={() => applyPreset(preset, index)}
                          aria-label={presetButtonLabel(preset, index)}
                        >
                          <div class="preset-header">
                            <span class="preset-title">Preset {index + 1}</span>
                            {#if preset.metadataVersion}
                              <span
                                class="preset-metadata"
                                class:stale={
                                  currentMetadataHash &&
                                  preset.metadataSignature &&
                                  preset.metadataSignature !== currentMetadataHash
                                }
                              >
                                Metadata {preset.metadataVersion}
                              </span>
                            {/if}
                          </div>
                          <div class="preset-stacks">{preset.stacks.join(' • ')}</div>
                          <div class="preset-preview-grid">
                            <div>
                              <span class="preview-label">EXP</span>
                              <span class="preview-value">{formatRewardBonus(preset.reward.exp_bonus)}</span>
                            </div>
                            <div>
                              <span class="preview-label">RDR</span>
                              <span class="preview-value">{formatRewardBonus(preset.reward.rdr_bonus)}</span>
                            </div>
                          </div>
                        </button>
                      {/each}
                    </div>
                  </section>
                {/if}
                <RewardPreviewCard preview={rewardPreview} formatValue={formatRewardBonus} />
                <WizardNavigation
                  backLabel="Back"
                  onBack={() => goToStep('run-type')}
                  onNext={goToConfirm}
                  nextDisabled={metadataLoading || metadataError}
                />
              </aside>
            </div>
          {/if}
        </section>
        {#if metadataLoading || metadataError}
          <WizardNavigation
            backLabel="Back"
            onBack={() => goToStep('run-type')}
            onNext={goToConfirm}
            nextDisabled={metadataLoading || metadataError}
          />
        {/if}
      {:else if step === 'confirm'}
        <section class="confirm-panel step-surface">
          {#if metadataLoading}
            <p class="loading">Loading configuration...</p>
          {:else if metadataError}
            <div class="error">
              <p>{metadataError}</p>
              <button class="summary-button ghost" type="button" on:click={() => fetchMetadata({ forceRefresh: true })}>
                Retry
              </button>
            </div>
          {:else}
            <div class="confirm-grid">
              <section class="confirm-card">
                <h3>Party</h3>
                <ul class="stacked-list">
                  {#each partySummary as member}
                    <li>{member}</li>
                  {/each}
                </ul>
              </section>
              <section class="confirm-card">
                <h3>Run Type</h3>
                <p class="confirm-primary">{activeRunType?.label || runTypeId}</p>
                <p class="confirm-secondary">{activeRunType?.description}</p>
              </section>
              <section class="confirm-card">
                <h3>Modifiers</h3>
                {#if selectedModifiers.some(isActiveModifier)}
                  <ul class="stacked-list">
                    {#each selectedModifiers.filter(isActiveModifier) as mod}
                      <li>{modifierLabel(mod)}: {mod.value}</li>
                    {/each}
                  </ul>
                {:else}
                  <p class="confirm-secondary">No additional modifiers selected.</p>
                {/if}
              </section>
              <RewardPreviewCard preview={rewardPreview} formatValue={formatRewardBonus} />
            </div>
          {/if}
        </section>
        <WizardNavigation
          backLabel="Back"
          nextLabel="Start Run"
          onBack={() => goToStep('modifiers')}
          onNext={startRun}
          nextDisabled={submitting || metadataLoading || metadataError}
        />
      {/if}
    </div>
  </MenuPanel>
{/if}

<style>
  .run-wizard {
    --wizard-surface-bg: rgba(10, 16, 28, 0.82);
    --wizard-surface-border: rgba(153, 201, 255, 0.18);
    --wizard-card-bg: rgba(17, 23, 38, 0.74);
    --wizard-card-border: rgba(153, 201, 255, 0.2);
    --wizard-summary-bg: rgba(17, 23, 38, 0.82);
    --wizard-summary-border: rgba(173, 211, 255, 0.26);
    --wizard-border-muted: rgba(255, 255, 255, 0.28);
    --wizard-border-accent: rgba(173, 211, 255, 0.65);
    --wizard-focus-outline: rgba(180, 220, 255, 0.8);
    --wizard-text-muted: rgba(255, 255, 255, 0.72);
    display: flex;
    flex-direction: column;
    gap: clamp(0.75rem, 1.9vw, 1.2rem);
    width: 100%;
  }

  .wizard {
    display: flex;
    flex-direction: column;
    gap: clamp(0.75rem, 1.9vw, 1.2rem);
    width: 100%;
  }

  .wizard > * {
    min-width: 0;
  }

  .step-surface {
    background: var(--wizard-surface-bg);
    border: 1px solid var(--wizard-surface-border);
    padding: clamp(0.75rem, 1.9vw, 1.2rem);
    display: flex;
    flex-direction: column;
    gap: clamp(0.65rem, 1.5vw, 0.95rem);
  }

  .party-standalone {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .party-step {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
  }

  .wizard-button,
  .summary-button {
    appearance: none;
    border: 1px solid var(--wizard-border-muted);
    background: rgba(255, 255, 255, 0.03);
    color: inherit;
    padding: clamp(0.55rem, 1.5vw, 0.85rem) clamp(1rem, 2.5vw, 1.5rem);
    font-size: 0.95rem;
    font-weight: 550;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    cursor: pointer;
    border-radius: 0;
    transition: background 160ms ease, border-color 160ms ease, transform 120ms ease;
  }

  .wizard-button:focus-visible,
  .summary-button:focus-visible {
    outline: 2px solid var(--wizard-focus-outline);
    outline-offset: 2px;
  }

  .wizard-button.primary {
    background: linear-gradient(120deg, rgba(153, 201, 255, 0.55), rgba(113, 169, 240, 0.55));
    border-color: rgba(153, 201, 255, 0.7);
    color: #0b0f19;
  }

  .wizard-button.primary:not(:disabled):hover {
    transform: translateY(-1px);
    background: linear-gradient(120deg, rgba(173, 211, 255, 0.75), rgba(133, 189, 250, 0.75));
    border-color: rgba(173, 211, 255, 0.85);
  }

  .wizard-button.ghost,
  .summary-button.ghost {
    background: rgba(255, 255, 255, 0.03);
  }

  .wizard-button.ghost:not(:disabled):hover,
  .summary-button.ghost:not(:disabled):hover {
    border-color: var(--wizard-border-accent);
    background: rgba(173, 211, 255, 0.12);
  }

  .wizard-button:disabled,
  .summary-button:disabled {
    opacity: 0.55;
    cursor: default;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: clamp(0.55rem, 1.6vw, 0.95rem);
  }

  .runs {
    display: flex;
    flex-direction: column;
    gap: clamp(0.55rem, 1.5vw, 0.9rem);
  }

  .run-item {
    display: flex;
    gap: clamp(0.6rem, 1.4vw, 0.9rem);
    align-items: flex-start;
    background: var(--wizard-card-bg);
    border: 1px solid var(--wizard-card-border);
    padding: clamp(0.6rem, 1.6vw, 0.95rem);
  }

  .run-item input {
    margin-top: 0.25rem;
  }

  .summary {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .id {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.02em;
  }

  .details {
    font-size: 0.85rem;
    line-height: 1.35;
    color: var(--wizard-text-muted);
  }

  .empty {
    margin: 0;
    color: var(--wizard-text-muted);
  }

  .modifier-panel {
    display: flex;
    flex-direction: column;
    gap: clamp(0.75rem, 1.8vw, 1.15rem);
  }

  .modifier-layout {
    display: grid;
    gap: clamp(0.8rem, 2vw, 1.4rem);
  }

  .modifier-column,
  .summary-column {
    display: flex;
    flex-direction: column;
    gap: clamp(0.75rem, 1.8vw, 1.2rem);
  }

  .summary-column :global(.wizard-navigation) {
    margin-top: clamp(0.65rem, 1.6vw, 0.95rem);
    justify-content: flex-end;
  }

  .summary-card {
    background: var(--wizard-summary-bg);
    border: 1px solid var(--wizard-summary-border);
    padding: clamp(0.7rem, 1.6vw, 1rem);
    display: flex;
    flex-direction: column;
    gap: clamp(0.45rem, 1vw, 0.7rem);
  }

  .summary-card header,
  .preset-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .summary-card h3 {
    margin: 0;
    font-size: 0.95rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .metadata-badge {
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--wizard-text-muted);
  }

  .pressure-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.95rem;
    font-weight: 600;
    letter-spacing: 0.04em;
  }

  .pressure-tooltip {
    margin: 0;
    font-size: 0.85rem;
    line-height: 1.35;
    color: var(--wizard-text-muted);
  }

  .pressure-value {
    font-variant-numeric: tabular-nums;
  }

  .preset-list {
    display: grid;
    gap: clamp(0.55rem, 1.6vw, 0.95rem);
  }

  .preset-card {
    display: flex;
    flex-direction: column;
    gap: clamp(0.4rem, 1vw, 0.6rem);
    background: var(--wizard-card-bg);
    border: 1px solid var(--wizard-card-border);
    padding: clamp(0.55rem, 1.5vw, 0.9rem);
    text-align: left;
    cursor: pointer;
    color: inherit;
    transition: border-color 160ms ease, background 160ms ease, transform 120ms ease;
  }

  .preset-card:hover,
  .preset-card:focus-visible {
    outline: none;
    border-color: var(--wizard-border-accent);
    background: rgba(27, 37, 58, 0.85);
  }

  .preset-title {
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  .preset-stacks {
    font-size: 0.85rem;
    color: var(--wizard-text-muted);
  }

  .preset-preview-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: clamp(0.35rem, 1vw, 0.6rem);
  }

  .preview-label {
    display: block;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--wizard-text-muted);
  }

  .preview-value {
    font-size: 0.95rem;
    font-variant-numeric: tabular-nums;
  }

  .preset-metadata {
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--wizard-text-muted);
  }

  .preset-metadata.stale {
    color: #ffb3c1;
  }

  .confirm-panel {
    display: flex;
    flex-direction: column;
    gap: clamp(0.75rem, 1.9vw, 1.2rem);
  }

  .confirm-grid {
    display: grid;
    gap: clamp(0.75rem, 1.9vw, 1.2rem);
  }

  .confirm-card {
    background: var(--wizard-summary-bg);
    border: 1px solid var(--wizard-summary-border);
    padding: clamp(0.65rem, 1.6vw, 1rem);
    display: flex;
    flex-direction: column;
    gap: clamp(0.4rem, 1vw, 0.6rem);
  }

  .confirm-grid :global(.reward-card) {
    background: var(--wizard-summary-bg);
    border: 1px solid var(--wizard-summary-border);
    padding: clamp(0.65rem, 1.6vw, 1rem);
    display: flex;
    flex-direction: column;
    gap: clamp(0.4rem, 1vw, 0.6rem);
  }

  .confirm-card h3 {
    margin: 0;
    font-size: 0.95rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .confirm-primary {
    margin: 0;
    font-weight: 600;
    font-size: 1rem;
  }

  .confirm-secondary {
    margin: 0;
    font-size: 0.9rem;
    line-height: 1.4;
    color: var(--wizard-text-muted);
  }

  .stacked-list {
    margin: 0;
    padding-left: 1.1rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    font-size: 0.9rem;
  }

  .stacked-list li {
    line-height: 1.4;
  }

  .loading {
    margin: 0;
    font-size: 0.95rem;
    color: var(--wizard-text-muted);
  }

  .error {
    display: flex;
    flex-direction: column;
    gap: clamp(0.45rem, 1vw, 0.65rem);
    background: rgba(46, 12, 20, 0.78);
    border: 1px solid rgba(255, 117, 133, 0.45);
    padding: clamp(0.7rem, 1.6vw, 1rem);
  }

  .error p {
    margin: 0;
    font-weight: 600;
  }

  @media (min-width: 900px) {
    .modifier-layout {
      grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
    }

    .preset-list {
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    }

    .confirm-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .confirm-grid :global(.reward-card) {
      grid-column: span 2;
    }
  }

  @media (max-width: 720px) {
    .wizard-button,
    .summary-button {
      flex: 1 1 100%;
    }
  }
</style>
