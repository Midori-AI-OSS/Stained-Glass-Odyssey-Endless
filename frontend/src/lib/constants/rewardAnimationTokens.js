export const rewardSelectionAnimationTokens = Object.freeze({
  wiggleDurationMs: 900,
  wiggleRotationDeg: 0.8,
  wiggleTranslatePx: 3,
  wiggleRestHoldMs: 220
});

export function selectionAnimationCssVariables(tokens = rewardSelectionAnimationTokens) {
  const config = tokens || rewardSelectionAnimationTokens;
  return {
    '--reward-selection-wiggle-duration': `${config.wiggleDurationMs}ms`,
    '--reward-selection-wiggle-rotation': `${config.wiggleRotationDeg}deg`,
    '--reward-selection-wiggle-translate': `${config.wiggleTranslatePx}px`,
    '--reward-selection-wiggle-rest': `${config.wiggleRestHoldMs}ms`
  };
}
