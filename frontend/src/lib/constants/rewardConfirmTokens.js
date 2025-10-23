export const rewardConfirmButtonTokens = Object.freeze({
  borderRadius: '999px',
  paddingY: '0.55rem',
  paddingX: '1.5rem',
  fontSize: '0.95rem',
  fontWeight: 600,
  letterSpacing: '0.08em',
  textColor: '#f3f8ff',
  backgroundPrimary: 'rgba(33, 54, 92, 0.92)',
  backgroundSecondary: 'rgba(19, 36, 64, 0.92)',
  glintPrimary: 'rgba(148, 192, 255, 0.38)',
  glintSecondary: 'rgba(75, 126, 218, 0.18)',
  borderColor: 'rgba(152, 206, 255, 0.45)',
  shadow: '0 12px 26px rgba(0, 0, 0, 0.42)',
  innerGlow: '0 0 0 1px rgba(115, 174, 255, 0.18) inset',
  hoverShadow: '0 18px 32px rgba(0, 0, 0, 0.45)',
  hoverInnerGlow: '0 0 0 1px rgba(153, 210, 255, 0.32) inset',
  disabledOpacity: 0.58,
  transitionDurationMs: 140
});

export function rewardConfirmCssVariables(tokens = rewardConfirmButtonTokens) {
  const config = tokens || rewardConfirmButtonTokens;
  return {
    '--reward-confirm-border-radius': config.borderRadius,
    '--reward-confirm-padding-y': config.paddingY,
    '--reward-confirm-padding-x': config.paddingX,
    '--reward-confirm-font-size': config.fontSize,
    '--reward-confirm-font-weight': String(config.fontWeight),
    '--reward-confirm-letter-spacing': config.letterSpacing,
    '--reward-confirm-text-color': config.textColor,
    '--reward-confirm-bg-layer-primary': config.backgroundPrimary,
    '--reward-confirm-bg-layer-secondary': config.backgroundSecondary,
    '--reward-confirm-glint-layer-primary': config.glintPrimary,
    '--reward-confirm-glint-layer-secondary': config.glintSecondary,
    '--reward-confirm-border-color': config.borderColor,
    '--reward-confirm-shadow': config.shadow,
    '--reward-confirm-inner-glow': config.innerGlow,
    '--reward-confirm-hover-shadow': config.hoverShadow,
    '--reward-confirm-hover-inner': config.hoverInnerGlow,
    '--reward-confirm-disabled-opacity': String(config.disabledOpacity),
    '--reward-confirm-transition-duration': `${config.transitionDurationMs}ms`
  };
}
