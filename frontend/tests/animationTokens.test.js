import { describe, expect, test } from 'bun:test';
import {
  DURATIONS,
  EASINGS,
  EFFECT_TOKENS,
  deterministicVariation,
  deterministicDelay,
  scaleDuration,
  shouldReduceMotion,
  respectMotion,
  createAnimationToken,
  createOrbTokens,
  createFloaterTokens,
  createPortraitEffectTokens,
  createSpinnerTokens,
  createOverlayTokens,
} from '../src/lib/systems/animationTokens.js';

describe('Animation Tokens Module', () => {
  test('exports expected duration constants', () => {
    expect(DURATIONS.INSTANT).toBe(0);
    expect(DURATIONS.FAST.SM).toBe(150);
    expect(DURATIONS.NORMAL.MD).toBe(900);
    expect(DURATIONS.SLOW.LG).toBe(3000);
    expect(typeof DURATIONS.VERY_SLOW.LG).toBe('number');
  });

  test('exports standard easing curves', () => {
    expect(EASINGS.LINEAR).toBe('linear');
    expect(EASINGS.EASE_IN_OUT).toBe('ease-in-out');
    expect(EASINGS.SMOOTH_OUT).toContain('cubic-bezier');
    expect(EASINGS.BATTLE_FLOATER).toContain('cubic-bezier');
  });

  test('exports effect-specific token sets', () => {
    expect(EFFECT_TOKENS.BACKGROUND_AMBIANCE.ORB_DRIFT_BASE).toBeGreaterThan(0);
    expect(EFFECT_TOKENS.BATTLE_FLOATERS.FLOAT_DURATION).toBe(900);
    expect(EFFECT_TOKENS.PORTRAIT_EFFECTS.ELEMENT_CHANGE).toBe(300);
    expect(EFFECT_TOKENS.SPINNERS.TRIPLE_RING_PULSE).toBe(1200);
  });
});

describe('Deterministic Functions', () => {
  test('deterministicVariation produces consistent results', () => {
    const id = 'test-orb-1';
    const min = 50;
    const max = 100;
    
    const result1 = deterministicVariation(id, min, max);
    const result2 = deterministicVariation(id, min, max);
    
    expect(result1).toBe(result2);
    expect(result1).toBeGreaterThanOrEqual(min);
    expect(result1).toBeLessThanOrEqual(max);
  });

  test('deterministicVariation produces different results for different IDs', () => {
    const min = 0;
    const max = 100;
    
    const result1 = deterministicVariation('id1', min, max);
    const result2 = deterministicVariation('id2', min, max);
    
    expect(result1).not.toBe(result2);
  });

  test('deterministicDelay works correctly', () => {
    const id = 'test-entity';
    const maxDelay = 30;
    
    const delay1 = deterministicDelay(id, maxDelay);
    const delay2 = deterministicDelay(id, maxDelay);
    
    expect(delay1).toBe(delay2);
    expect(delay1).toBeGreaterThanOrEqual(0);
    expect(delay1).toBeLessThanOrEqual(maxDelay);
  });
});

describe('Duration Scaling', () => {
  test('scaleDuration scales correctly', () => {
    const baseDuration = 1000;
    
    expect(scaleDuration(baseDuration, 1)).toBe(1000);
    expect(scaleDuration(baseDuration, 2)).toBe(500);
    expect(scaleDuration(baseDuration, 0.5)).toBe(2000);
  });

  test('scaleDuration clamps speed to valid range', () => {
    const baseDuration = 1000;
    
    // Test clamping minimum
    expect(scaleDuration(baseDuration, 0.05)).toBe(10000); // Clamped to 0.1
    
    // Test clamping maximum  
    expect(scaleDuration(baseDuration, 5)).toBe(500); // Clamped to 2.0
  });

  test('scaleDuration handles invalid inputs', () => {
    const baseDuration = 1000;
    
    expect(scaleDuration(baseDuration, null)).toBe(1000);
    expect(scaleDuration(baseDuration, 'invalid')).toBe(1000);
    expect(scaleDuration(baseDuration, NaN)).toBe(1000);
  });
});

describe('Motion Detection', () => {
  test('shouldReduceMotion detects global setting', () => {
    const motionSettings = { globalReducedMotion: true };
    expect(shouldReduceMotion(motionSettings)).toBe(true);
    
    const normalSettings = { globalReducedMotion: false };
    expect(shouldReduceMotion(normalSettings)).toBe(false);
  });

  test('shouldReduceMotion detects effect-specific settings', () => {
    const motionSettings = {
      globalReducedMotion: false,
      disableFloatingDamage: true,
      disablePortraitGlows: false,
      simplifyOverlayTransitions: true,
      disableStarStorm: false,
    };
    
    expect(shouldReduceMotion(motionSettings, 'floatingDamage')).toBe(true);
    expect(shouldReduceMotion(motionSettings, 'portraitGlows')).toBe(false);
    expect(shouldReduceMotion(motionSettings, 'overlayTransitions')).toBe(true);
    expect(shouldReduceMotion(motionSettings, 'backgroundAmbiance')).toBe(false);
  });

  test('respectMotion returns correct duration', () => {
    const normalDuration = 1000;
    const reducedDuration = 100;
    
    const motionDisabled = { globalReducedMotion: true };
    const motionEnabled = { globalReducedMotion: false };
    
    expect(respectMotion(normalDuration, reducedDuration, motionDisabled)).toBe(reducedDuration);
    expect(respectMotion(normalDuration, reducedDuration, motionEnabled)).toBe(normalDuration);
  });
});

describe('Animation Token Creation', () => {
  test('createAnimationToken creates complete token object', () => {
    const token = createAnimationToken({
      duration: 1000,
      easing: EASINGS.EASE_IN_OUT,
      animationSpeed: 1,
      motionSettings: { globalReducedMotion: false },
    });
    
    expect(token.duration).toBe(1000);
    expect(token.durationMs).toBe('1000ms');
    expect(token.durationS).toBe('1.00s');
    expect(token.easing).toBe(EASINGS.EASE_IN_OUT);
    expect(token.isReduced).toBe(false);
    expect(token.cssAnimation).toBe('1000ms ease-in-out');
  });

  test('createAnimationToken respects motion settings', () => {
    const token = createAnimationToken({
      duration: 1000,
      easing: EASINGS.EASE,
      motionSettings: { globalReducedMotion: true },
      reducedDuration: 0,
    });
    
    expect(token.duration).toBe(0);
    expect(token.isReduced).toBe(true);
    expect(token.cssAnimation).toBe('0ms ease');
  });
});

describe('Effect-Specific Token Factories', () => {
  test('createOrbTokens generates consistent orb properties', () => {
    const orbId = 'zenith';
    const options = { animationSpeed: 1, motionSettings: { globalReducedMotion: false } };
    
    const tokens1 = createOrbTokens(orbId, options);
    const tokens2 = createOrbTokens(orbId, options);
    
    expect(tokens1.delay).toBe(tokens2.delay);
    expect(tokens1.driftDuration).toBe(tokens2.driftDuration);
    expect(tokens1.isStatic).toBe(false);
    expect(typeof tokens1.delayS).toBe('string');
    expect(tokens1.delayS).toContain('s');
  });

  test('createOrbTokens respects motion settings', () => {
    const orbId = 'aurora';
    const options = { 
      animationSpeed: 1, 
      motionSettings: { disableStarStorm: true } 
    };
    
    const tokens = createOrbTokens(orbId, options);
    expect(tokens.isStatic).toBe(true);
  });

  test('createFloaterTokens works with custom pacing', () => {
    const options = {
      animationSpeed: 2,
      motionSettings: { globalReducedMotion: false },
      pacingMs: 1200,
    };
    
    const tokens = createFloaterTokens(options);
    expect(tokens.duration).toBe(600); // 1200ms / 2x speed
    expect(tokens.easing).toBe(EFFECT_TOKENS.BATTLE_FLOATERS.EASING);
  });

  test('createPortraitEffectTokens creates deterministic timing', () => {
    const entityId = 'player-1';
    const options = { animationSpeed: 1, motionSettings: {} };
    
    const rankTokens1 = createPortraitEffectTokens(entityId, 'rank', options);
    const rankTokens2 = createPortraitEffectTokens(entityId, 'rank', options);
    
    expect(rankTokens1.delay).toBe(rankTokens2.delay);
    expect(rankTokens1.duration).toBe(rankTokens2.duration);
    expect(typeof rankTokens1.delayS).toBe('string');
  });

  test('createPortraitEffectTokens handles different effect types', () => {
    const entityId = 'test';
    const options = { animationSpeed: 1, motionSettings: {} };
    
    const rankTokens = createPortraitEffectTokens(entityId, 'rank', options);
    const ultTokens = createPortraitEffectTokens(entityId, 'ult', options);
    const glowTokens = createPortraitEffectTokens(entityId, 'glow', options);
    const changeTokens = createPortraitEffectTokens(entityId, 'elementChange', options);
    
    expect(rankTokens.duration).toBeGreaterThan(ultTokens.duration);
    expect(ultTokens.duration).toBeGreaterThan(glowTokens.duration);
    expect(changeTokens.duration).toBeLessThan(glowTokens.duration);
  });

  test('createSpinnerTokens provides spinner configuration', () => {
    const tokens = createSpinnerTokens({
      animationSpeed: 1.5,
      motionSettings: { globalReducedMotion: false },
    });
    
    expect(tokens.duration).toBe(800); // 1200ms / 1.5x speed
    expect(tokens.easing).toBe(EFFECT_TOKENS.SPINNERS.EASING);
    expect(tokens.isReduced).toBe(false);
  });

  test('createOverlayTokens handles different transition types', () => {
    const options = { animationSpeed: 1, motionSettings: {} };
    
    const modalTokens = createOverlayTokens({ ...options, transitionType: 'modal' });
    const surfaceTokens = createOverlayTokens({ ...options, transitionType: 'surface' });
    const exitTokens = createOverlayTokens({ ...options, transitionType: 'exit' });
    
    expect(modalTokens.duration).toBe(EFFECT_TOKENS.OVERLAY_TRANSITIONS.MODAL_ENTER);
    expect(surfaceTokens.duration).toBe(EFFECT_TOKENS.OVERLAY_TRANSITIONS.SURFACE_FADE);
    expect(exitTokens.duration).toBe(EFFECT_TOKENS.OVERLAY_TRANSITIONS.MODAL_EXIT);
  });

  test('createOverlayTokens respects simplified transitions', () => {
    const tokens = createOverlayTokens({
      animationSpeed: 1,
      motionSettings: { simplifyOverlayTransitions: true },
      transitionType: 'modal',
    });
    
    expect(tokens.duration).toBe(EFFECT_TOKENS.OVERLAY_TRANSITIONS.SIMPLIFIED_DURATION);
    expect(tokens.isReduced).toBe(true);
  });
});