const rawIconModules = import.meta.glob('../assets/items/*/*.png', {
  eager: true,
  import: 'default',
  query: '?url'
});

const iconModules = Object.fromEntries(
  Object.entries(rawIconModules).map(([path, src]) => [path, new URL(src, import.meta.url).href])
);

const fallbackIcon = new URL('../assets/items/generic/generic1.png', import.meta.url).href;

export function onIconError(event) {
  event.target.src = fallbackIcon;
}

export function getMaterialIcon(key) {
  const [rawElement, rawRank] = String(key).split('_');
  const element = String(rawElement || '').toLowerCase();
  const rank = String(rawRank || '').replace(/[^0-9]/g, '') || '1';
  const rankPath = `../assets/items/${element}/${rank}.png`;
  if (iconModules[rankPath]) return iconModules[rankPath];
  const elementPrefix = `../assets/items/${element}/`;
  const elementKeys = Object.keys(iconModules).filter((p) => p.startsWith(elementPrefix));
  const genericRankPath = `${elementPrefix}generic${rank}.png`;
  if (iconModules[genericRankPath]) return iconModules[genericRankPath];
  if (elementKeys.length > 0) return iconModules[elementKeys[0]];
  const genericPath = `../assets/items/generic/generic${rank}.png`;
  return iconModules[genericPath] || fallbackIcon;
}
