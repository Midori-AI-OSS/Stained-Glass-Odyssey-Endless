# Animation Tokens System

The animation tokens system provides standardized, deterministic animation timing and behavior across all UI components. It replaces hardcoded duration constants and random animation timing with a centralized, motion-aware system.

## Overview

The animation tokens module (`frontend/src/lib/systems/animationTokens.js`) provides:

- **Standardized Durations**: Organized into INSTANT, FAST, NORMAL, SLOW, and VERY_SLOW categories
- **Common Easing Curves**: Predefined CSS easing functions for different animation types
- **Deterministic Variation**: Consistent "random" values derived from entity IDs or seeds
- **Motion Awareness**: Automatic integration with granular motion settings and browser preferences
- **Effect-Specific Tokens**: Preconfigured animation sets for different UI effect types

## Core Components

### Duration Constants

```javascript
DURATIONS = {
  INSTANT: 0,
  FAST: { XS: 100, SM: 150, MD: 200, LG: 300 },
  NORMAL: { XS: 400, SM: 600, MD: 900, LG: 1200 },
  SLOW: { XS: 1500, SM: 1800, MD: 2400, LG: 3000 },
  VERY_SLOW: { SM: 60000, MD: 90000, LG: 150000 }
}
```

### Easing Curves

Predefined easing functions include standard CSS easings plus custom cubic-bezier curves:
- `SMOOTH_OUT`: `cubic-bezier(0.2, 0.8, 0.2, 1)` for battle floaters
- `BOUNCE_OUT`, `BACK_OUT`, `ELASTIC_OUT`: Specialized effect easings
- Effect-specific easings for orb floating, portrait glows, etc.

### Effect-Specific Token Sets

The system provides preconfigured animation sets for:

- **Background Ambiance** (ElementOrbs): 2.5-minute drift cycles with deterministic delays
- **Battle Floaters**: 900ms float duration with 150ms stagger steps
- **Portrait Effects**: Rank outline pulses, ultimate icon timing, element change animations
- **Spinners**: Triple ring pulse timing with delay staggering
- **Overlay Transitions**: Modal enter/exit with simplified reduced-motion alternatives

## Key Functions

### Deterministic Animation

```javascript
// Always returns the same value for the same ID
deterministicVariation('orb-zenith', 50, 100); // Consistent result
deterministicDelay('entity-123', 30); // Consistent 0-30s delay
```

### Motion-Aware Duration Scaling

```javascript
// Automatically scales duration by animation speed
scaleDuration(1000, 2.0); // Returns 500ms (2x faster)

// Respects motion preferences
respectMotion(1000, 0, motionSettings, 'floatingDamage');
// Returns 0 if floating damage is disabled
```

### Complete Animation Tokens

```javascript
const token = createAnimationToken({
  duration: 1000,
  easing: EASINGS.EASE_IN_OUT,
  animationSpeed: 1.5,
  motionSettings: { globalReducedMotion: false },
  effectType: 'portraitGlows',
  reducedDuration: 100
});

// Returns: { duration: 667, durationMs: '667ms', durationS: '0.67s', 
//           easing: 'ease-in-out', isReduced: false, cssAnimation: '667ms ease-in-out' }
```

## Component Integration

### Before (Random/Hardcoded)

```javascript
// Old approach - inconsistent and motion-unaware
const BASE_DURATION = 900;
let animDur = `${(150 * (0.88 + Math.random() * 0.24)).toFixed(2)}s`;
let delay = `${(Math.random() * 150).toFixed(2)}s`;
```

### After (Tokens-Based)

```javascript
// New approach - deterministic and motion-aware
import { createPortraitEffectTokens } from '../systems/animationTokens.js';

$: rankTokens = createPortraitEffectTokens(entityId, 'rank', { 
  animationSpeed, 
  motionSettings 
});

// Use: rankTokens.durationS, rankTokens.delayS, rankTokens.isReduced
```

## Refactored Components

The following components have been updated to use animation tokens:

### ElementOrbs (formerly StarStorm)
- Deterministic orb drift timing based on orb IDs
- Proper animation speed scaling
- Motion settings integration for disableStarStorm/disableElementOrbs

### BattleEventFloaters
- Standardized float duration and stagger timing
- Deterministic horizontal offset based on event content
- Respects disableFloatingDamage setting

### BattleFighterCard
- Deterministic rank outline and ultimate icon pulse timing
- Element change animation duration from tokens
- Respects disablePortraitGlows setting

### TripleRingSpinner
- Consistent pulse timing across all instances
- Motion-aware duration scaling
- Proper reduced motion handling

## Motion Integration

The animation tokens system fully integrates with the granular motion settings:

- **globalReducedMotion**: Master switch affecting all animations
- **disableFloatingDamage**: Specifically controls BattleEventFloaters
- **disablePortraitGlows**: Controls BattleFighterCard glow effects
- **simplifyOverlayTransitions**: Uses shorter durations for overlay animations
- **disableStarStorm**: Controls ElementOrbs background animations

Components automatically check both legacy `reducedMotion` props and the new granular settings, ensuring backward compatibility while providing fine-grained control.

## Browser Preference Support

The system automatically detects and respects the browser's `prefers-reduced-motion` setting:

```javascript
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  // Automatically reduce or disable animations
}
```

## Testing

The animation tokens module includes comprehensive unit tests covering:

- Deterministic function consistency
- Duration scaling and clamping
- Motion detection and respect
- Token factory functions
- Effect-specific configurations

Tests ensure that animations remain consistent across sessions and properly respect user motion preferences.

## Migration Guide

To update existing components to use animation tokens:

1. Import required functions from `animationTokens.js`
2. Replace hardcoded durations with token-based durations
3. Replace `Math.random()` calls with `deterministicVariation()`
4. Add motion settings props and reactive statements
5. Use token properties in templates (`.durationMs`, `.delayS`, etc.)
6. Update CSS animations to use CSS custom properties when needed

## Performance Considerations

- Token creation is lightweight and suitable for reactive statements
- Deterministic functions use simple string hashing
- CSS animations continue to use GPU acceleration
- Motion detection uses browser APIs efficiently
- Token objects are small and can be cached in component state