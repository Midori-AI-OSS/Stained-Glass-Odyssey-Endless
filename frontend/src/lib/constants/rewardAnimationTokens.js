export const rewardSelectionAnimationTokens = Object.freeze({
  wiggleDurationMs: 1600,
  wiggleRotationDeg: 1.6,
  wiggleScaleMin: 0.97,
  wiggleScaleMax: 1.03,
  wiggleRestHoldMs: 260
});

export function selectionAnimationCssVariables(tokens = rewardSelectionAnimationTokens) {
  const config = tokens || rewardSelectionAnimationTokens;
  return {
    '--reward-selection-wiggle-duration': `${config.wiggleDurationMs}ms`,
    '--reward-selection-wiggle-rotation': `${config.wiggleRotationDeg}deg`,
    '--reward-selection-wiggle-scale-min': String(config.wiggleScaleMin),
    '--reward-selection-wiggle-scale-max': String(config.wiggleScaleMax),
    '--reward-selection-wiggle-rest': `${config.wiggleRestHoldMs}ms`
  };
}
