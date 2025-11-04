import { getUISettings } from './settingsStorage.js';

/**
 * Get the appropriate description text based on user's concise description setting.
 * 
 * @param {Object} item - The item object (card, relic, or player)
 * @param {string} item.full_about - The full description text
 * @param {string} item.summarized_about - The summarized description text
 * @param {string} [item.about] - Legacy description field (fallback)
 * @returns {string} The appropriate description text
 */
export function getDescription(item) {
  if (!item) return '';
  
  const uiSettings = getUISettings();
  const useConcise = uiSettings?.conciseDescriptions ?? false;
  
  // If concise mode is enabled, prefer summarized_about
  if (useConcise) {
    return item.summarized_about || item.full_about || item.about || '';
  }
  
  // Otherwise, prefer full_about
  return item.full_about || item.summarized_about || item.about || '';
}

/**
 * Get description for a card by ID from the card metadata.
 * 
 * @param {string} id - The card ID
 * @param {Object} cardMeta - The card metadata object
 * @returns {string} The appropriate description text
 */
export function getCardDescription(id, cardMeta) {
  const card = cardMeta?.[id];
  return getDescription(card) || 'No description available.';
}

/**
 * Get description for a relic by ID from the relic metadata.
 * 
 * @param {string} id - The relic ID
 * @param {Object} relicMeta - The relic metadata object
 * @returns {string} The appropriate description text
 */
export function getRelicDescription(id, relicMeta) {
  const relic = relicMeta?.[id];
  return getDescription(relic) || 'No description available.';
}

/**
 * Get description for a player by ID from the player metadata.
 * 
 * @param {string} id - The player ID
 * @param {Object} playerMeta - The player metadata object
 * @returns {string} The appropriate description text
 */
export function getPlayerDescription(id, playerMeta) {
  const player = playerMeta?.[id];
  return getDescription(player) || 'No description available.';
}
