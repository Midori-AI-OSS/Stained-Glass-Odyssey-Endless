/**
 * Animation Tokens System
 * 
 * Provides standardized animation durations, easings, and utilities for consistent,
 * deterministic animations that respect user motion preferences.
 */

// =============================================================================
// CORE DURATION CONSTANTS
// =============================================================================

// Base duration scales (in milliseconds)
export const DURATIONS = {
  INSTANT: 0,
  FAST: {
    XS: 100,
    SM: 150,
    MD: 200,
    LG: 300,
  },
  NORMAL: {
    XS: 400,
    SM: 600,
    MD: 900,
    LG: 1200,
  },
  SLOW: {
    XS: 1500,
    SM: 1800,
    MD: 2400,
    LG: 3000,
  },
  VERY_SLOW: {
    SM: 60000,  // 1 minute
    MD: 90000,  // 1.5 minutes  
    LG: 150000, // 2.5 minutes
  }
};

// =============================================================================
// EASING CURVES
// =============================================================================

export const EASINGS = {
  // Standard easing
  LINEAR: 'linear',
  EASE: 'ease',
  EASE_IN: 'ease-in',
  EASE_OUT: 'ease-out',
  EASE_IN_OUT: 'ease-in-out',
  
  // Custom cubic-bezier curves for specific effects
  SMOOTH_OUT: 'cubic-bezier(0.2, 0.8, 0.2, 1)',      // Used in floaters
  BOUNCE_OUT: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  BACK_OUT: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  ELASTIC_OUT: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
  
  // Element-specific easings
  ORB_FLOAT: 'ease-in-out',
  PORTRAIT_GLOW: 'ease-in-out', 
  BATTLE_FLOATER: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
  OVERLAY_TRANSITION: 'ease',
};

// =============================================================================
// EFFECT-SPECIFIC TOKEN SETS
// =============================================================================

export const EFFECT_TOKENS = {
  // Background ambiance (ElementOrbs)
  BACKGROUND_AMBIANCE: {
    ORB_DRIFT_BASE: DURATIONS.VERY_SLOW.LG, // ~2.5 minutes base
    ORB_OPACITY_TRANSITION: DURATIONS.SLOW.MD,
    ORB_GLOW_TRANSITION: DURATIONS.SLOW.SM,
    EASING: EASINGS.ORB_FLOAT,
  },
  
  // Battle event floaters
  BATTLE_FLOATERS: {
    FLOAT_DURATION: DURATIONS.NORMAL.MD,  // 900ms base
    STAGGER_STEP: DURATIONS.FAST.SM,      // 150ms between items
    OFFSET_RANGE: 120,                    // px, for horizontal spread
    EASING: EASINGS.BATTLE_FLOATER,
  },
  
  // Portrait effects
  PORTRAIT_EFFECTS: {
    ELEMENT_CHANGE: DURATIONS.FAST.LG,    // 300ms
    RANK_OUTLINE_PULSE: DURATIONS.VERY_SLOW.LG,  // ~2.5 minutes
    ULT_ICON_PULSE_BASE: DURATIONS.SLOW.LG,      // 3s base
    ULT_GLOW_PULSE: DURATIONS.SLOW.SM,           // 1.8s
    EASING: EASINGS.PORTRAIT_GLOW,
  },
  
  // Loading spinners
  SPINNERS: {
    TRIPLE_RING_PULSE: DURATIONS.NORMAL.LG,  // 1.2s * 2 = 2.4s
    RING_DELAY_STEP: 0.33,                   // fraction of total duration
    EASING: EASINGS.EASE_IN_OUT,
  },
  
  // Overlay transitions
  OVERLAY_TRANSITIONS: {
    MODAL_ENTER: DURATIONS.FAST.MD,      // 200ms
    MODAL_EXIT: DURATIONS.FAST.SM,       // 150ms  
    SURFACE_FADE: DURATIONS.FAST.LG,     // 300ms
    SIMPLIFIED_DURATION: DURATIONS.FAST.XS, // 100ms for reduced motion
    EASING: EASINGS.OVERLAY_TRANSITION,
  },
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Generates a deterministic hash from a string
 * @param {string} str - Input string to hash
 * @returns {number} - Positive integer hash
 */
function hashString(str) {
  let hash = 0;
  const input = String(str);
  for (let i = 0; i < input.length; i++) {
    const char = input.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

/**
 * Creates deterministic variation based on an ID
 * @param {string|number} id - Unique identifier
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value  
 * @returns {number} - Consistent value between min and max
 */
export function deterministicVariation(id, min, max) {
  const hash = hashString(String(id));
  const normalized = (hash % 1000) / 1000; // 0-1 range
  return min + normalized * (max - min);
}

/**
 * Creates deterministic delay based on an ID
 * @param {string|number} id - Unique identifier
 * @param {number} maxDelay - Maximum delay value
 * @returns {number} - Consistent delay value
 */
export function deterministicDelay(id, maxDelay) {
  return deterministicVariation(id, 0, maxDelay);
}

/**
 * Scales duration by animation speed setting
 * @param {number} baseDuration - Base duration in ms
 * @param {number} animationSpeed - Speed multiplier (0.1 to 2.0)
 * @returns {number} - Scaled duration
 */
export function scaleDuration(baseDuration, animationSpeed = 1) {
  const speed = Math.max(0.1, Math.min(2.0, Number(animationSpeed) || 1));
  return Math.round(baseDuration / speed);
}

/**
 * Checks if motion should be reduced based on motion settings
 * @param {Object} motionSettings - Motion preference object
 * @param {string} effectType - Type of effect to check (optional)
 * @returns {boolean} - True if motion should be reduced
 */
export function shouldReduceMotion(motionSettings = {}, effectType = null) {
  // Check global reduced motion first
  if (motionSettings.globalReducedMotion) return true;
  
  // Check browser preference
  if (typeof window !== 'undefined') {
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) return true;
  }
  
  // Check effect-specific settings
  if (effectType) {
    switch (effectType) {
      case 'floatingDamage':
        return Boolean(motionSettings.disableFloatingDamage);
      case 'portraitGlows':
        return Boolean(motionSettings.disablePortraitGlows);
      case 'overlayTransitions':
        return Boolean(motionSettings.simplifyOverlayTransitions);
      case 'starStorm':
      case 'backgroundAmbiance':
        return Boolean(motionSettings.disableStarStorm);
      default:
        return false;
    }
  }
  
  return false;
}

/**
 * Returns appropriate duration respecting motion preferences
 * @param {number} normalDuration - Normal duration in ms
 * @param {number} reducedDuration - Reduced motion duration (default: 0)
 * @param {Object} motionSettings - Motion preference object
 * @param {string} effectType - Type of effect 
 * @returns {number} - Final duration to use
 */
export function respectMotion(normalDuration, reducedDuration = 0, motionSettings = {}, effectType = null) {
  if (shouldReduceMotion(motionSettings, effectType)) {
    return reducedDuration;
  }
  return normalDuration;
}

/**
 * Creates a complete animation token for a specific effect
 * @param {Object} config - Configuration object
 * @param {number} config.duration - Base duration
 * @param {string} config.easing - Easing curve
 * @param {number} config.animationSpeed - Speed multiplier
 * @param {Object} config.motionSettings - Motion preferences
 * @param {string} config.effectType - Effect type for motion checking
 * @param {number} config.reducedDuration - Fallback duration for reduced motion
 * @returns {Object} - Complete animation token
 */
export function createAnimationToken({
  duration,
  easing = EASINGS.EASE,
  animationSpeed = 1,
  motionSettings = {},
  effectType = null,
  reducedDuration = 0
}) {
  const scaledDuration = scaleDuration(duration, animationSpeed);
  const finalDuration = respectMotion(scaledDuration, reducedDuration, motionSettings, effectType);
  
  return {
    duration: finalDuration,
    durationMs: `${finalDuration}ms`,
    durationS: `${(finalDuration / 1000).toFixed(2)}s`,
    easing,
    isReduced: shouldReduceMotion(motionSettings, effectType),
    cssAnimation: `${finalDuration}ms ${easing}`,
  };
}

// =============================================================================
// EFFECT-SPECIFIC FACTORIES
// =============================================================================

/**
 * Creates orb floating animation tokens for ElementOrbs
 * @param {string} orbId - Unique orb identifier
 * @param {Object} options - Animation options
 * @returns {Object} - Orb animation configuration
 */
export function createOrbTokens(orbId, { animationSpeed = 1, motionSettings = {} } = {}) {
  const baseDelay = deterministicDelay(orbId, 30); // 0-30s spread
  const driftVariation = deterministicVariation(orbId, 0.85, 1.15); // ±15% variation
  const baseDrift = EFFECT_TOKENS.BACKGROUND_AMBIANCE.ORB_DRIFT_BASE;
  
  return {
    driftDuration: scaleDuration(baseDrift * driftVariation, animationSpeed),
    delay: baseDelay,
    delayS: `${baseDelay.toFixed(2)}s`,
    easing: EFFECT_TOKENS.BACKGROUND_AMBIANCE.EASING,
    isStatic: shouldReduceMotion(motionSettings, 'backgroundAmbiance'),
  };
}

/**
 * Creates battle floater animation tokens
 * @param {Object} options - Animation options  
 * @returns {Object} - Floater animation configuration
 */
export function createFloaterTokens({ 
  animationSpeed = 1, 
  motionSettings = {},
  pacingMs = null 
} = {}) {
  const tokens = EFFECT_TOKENS.BATTLE_FLOATERS;
  const baseDuration = pacingMs || tokens.FLOAT_DURATION;
  
  return createAnimationToken({
    duration: baseDuration,
    easing: tokens.EASING,
    animationSpeed,
    motionSettings,
    effectType: 'floatingDamage',
    reducedDuration: 0, // Floaters are hidden entirely when disabled
  });
}

/**
 * Creates portrait effect animation tokens  
 * @param {string} entityId - Entity identifier for deterministic timing
 * @param {string} effectName - Name of the effect (rank, ult, glow)
 * @param {Object} options - Animation options
 * @returns {Object} - Portrait effect configuration
 */
export function createPortraitEffectTokens(entityId, effectName, { 
  animationSpeed = 1, 
  motionSettings = {} 
} = {}) {
  const tokens = EFFECT_TOKENS.PORTRAIT_EFFECTS;
  let baseDuration;
  
  switch (effectName) {
    case 'rank':
      baseDuration = tokens.RANK_OUTLINE_PULSE;
      break;
    case 'ult':
      baseDuration = tokens.ULT_ICON_PULSE_BASE;
      break;
    case 'glow':
      baseDuration = tokens.ULT_GLOW_PULSE;
      break;
    case 'elementChange':
      baseDuration = tokens.ELEMENT_CHANGE;
      break;
    default:
      baseDuration = DURATIONS.NORMAL.MD;
  }
  
  // Add deterministic variation for rank and ult effects
  if (effectName === 'rank' || effectName === 'ult') {
    const variation = deterministicVariation(entityId, 0.88, 1.24);
    baseDuration = Math.round(baseDuration * variation);
  }
  
  const delay = effectName === 'rank' || effectName === 'ult' 
    ? deterministicDelay(entityId, baseDuration) 
    : 0;
  
  const token = createAnimationToken({
    duration: baseDuration,
    easing: tokens.EASING,
    animationSpeed,
    motionSettings,
    effectType: 'portraitGlows',
    reducedDuration: effectName === 'elementChange' ? DURATIONS.FAST.XS : 0,
  });
  
  return {
    ...token,
    delay,
    delayS: `${(delay / 1000).toFixed(2)}s`,
  };
}

/**
 * Creates spinner animation tokens
 * @param {Object} options - Animation options
 * @returns {Object} - Spinner animation configuration  
 */
export function createSpinnerTokens({ animationSpeed = 1, motionSettings = {} } = {}) {
  const tokens = EFFECT_TOKENS.SPINNERS;
  
  return createAnimationToken({
    duration: tokens.TRIPLE_RING_PULSE,
    easing: tokens.EASING,
    animationSpeed,
    motionSettings,
    effectType: null, // Spinners always animate unless globally disabled
    reducedDuration: DURATIONS.INSTANT,
  });
}

/**
 * Creates overlay transition animation tokens
 * @param {Object} options - Animation options
 * @returns {Object} - Overlay transition configuration
 */
export function createOverlayTokens({ 
  animationSpeed = 1, 
  motionSettings = {},
  transitionType = 'modal'
} = {}) {
  const tokens = EFFECT_TOKENS.OVERLAY_TRANSITIONS;
  let baseDuration;
  
  switch (transitionType) {
    case 'modal':
      baseDuration = tokens.MODAL_ENTER;
      break;
    case 'surface':
      baseDuration = tokens.SURFACE_FADE;
      break;
    case 'exit':
      baseDuration = tokens.MODAL_EXIT;
      break;
    default:
      baseDuration = tokens.MODAL_ENTER;
  }
  
  const reducedDuration = shouldReduceMotion(motionSettings, 'overlayTransitions') 
    ? tokens.SIMPLIFIED_DURATION 
    : baseDuration;
  
  return createAnimationToken({
    duration: baseDuration,
    easing: tokens.EASING,
    animationSpeed,
    motionSettings,
    effectType: 'overlayTransitions',
    reducedDuration,
  });
}