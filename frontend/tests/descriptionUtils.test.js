import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  getDescription,
  getCardDescription,
  getRelicDescription,
  getPlayerDescription,
  getDescriptionPair
} from '../src/lib/systems/descriptionUtils.js';

// Mock the settingsStorage module
vi.mock('../src/lib/systems/settingsStorage.js', () => ({
  getUISettings: vi.fn()
}));

import { getUISettings } from '../src/lib/systems/settingsStorage.js';

describe('descriptionUtils', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getDescriptionPair', () => {
    it('returns trimmed full and concise descriptions', () => {
      const item = { full_about: ' Full text ', summarized_about: ' Short text ' };
      expect(getDescriptionPair(item)).toEqual({
        fullDescription: 'Full text',
        conciseDescription: 'Short text'
      });
    });

    it('falls back to about when full_about is missing', () => {
      const item = { about: 'Legacy description' };
      expect(getDescriptionPair(item)).toEqual({
        fullDescription: 'Legacy description',
        conciseDescription: ''
      });
    });

    it('returns empty strings for null input', () => {
      expect(getDescriptionPair(null)).toEqual({ fullDescription: '', conciseDescription: '' });
    });
  });

  describe('getDescription', () => {
    it('should return empty string for null item', () => {
      expect(getDescription(null)).toBe('');
    });

    it('should return full_about when concise is false', () => {
      getUISettings.mockReturnValue({ conciseDescriptions: false });
      const item = {
        full_about: 'Full description',
        summarized_about: 'Short description'
      };
      expect(getDescription(item)).toBe('Full description');
    });

    it('should return summarized_about when concise is true', () => {
      getUISettings.mockReturnValue({ conciseDescriptions: true });
      const item = {
        full_about: 'Full description',
        summarized_about: 'Short description'
      };
      expect(getDescription(item)).toBe('Short description');
    });

    it('should fallback to full_about if summarized_about is missing in concise mode', () => {
      getUISettings.mockReturnValue({ conciseDescriptions: true });
      const item = {
        full_about: 'Full description'
      };
      expect(getDescription(item)).toBe('Full description');
    });

    it('should fallback to summarized_about if full_about is missing', () => {
      getUISettings.mockReturnValue({ conciseDescriptions: false });
      const item = {
        summarized_about: 'Short description'
      };
      expect(getDescription(item)).toBe('Short description');
    });

    it('should return empty string if both new fields are missing', () => {
      getUISettings.mockReturnValue({ conciseDescriptions: false });
      const item = {
        about: 'Legacy description'
      };
      expect(getDescription(item)).toBe('');
    });

    it('should handle missing UI settings', () => {
      getUISettings.mockReturnValue(null);
      const item = {
        full_about: 'Full description',
        summarized_about: 'Short description'
      };
      // Should default to full mode when settings are missing
      expect(getDescription(item)).toBe('Full description');
    });
  });

  describe('getCardDescription', () => {
    it('should return card description from metadata', () => {
      getUISettings.mockReturnValue({ conciseDescriptions: false });
      const cardMeta = {
        'fire_card': {
          full_about: 'Deals fire damage',
          summarized_about: 'Fire attack'
        }
      };
      expect(getCardDescription('fire_card', cardMeta)).toBe('Deals fire damage');
    });

    it('should return fallback message for missing card', () => {
      getUISettings.mockReturnValue({ conciseDescriptions: false });
      const cardMeta = {};
      expect(getCardDescription('missing_card', cardMeta)).toBe('No description available.');
    });
  });

  describe('getRelicDescription', () => {
    it('should return relic description from metadata', () => {
      getUISettings.mockReturnValue({ conciseDescriptions: false });
      const relicMeta = {
        'lucky_charm': {
          full_about: 'Increases luck by 10%',
          summarized_about: 'Boosts luck'
        }
      };
      expect(getRelicDescription('lucky_charm', relicMeta)).toBe('Increases luck by 10%');
    });

    it('should return fallback message for missing relic', () => {
      getUISettings.mockReturnValue({ conciseDescriptions: false });
      const relicMeta = {};
      expect(getRelicDescription('missing_relic', relicMeta)).toBe('No description available.');
    });
  });

  describe('getPlayerDescription', () => {
    it('should return player description from metadata', () => {
      getUISettings.mockReturnValue({ conciseDescriptions: false });
      const playerMeta = {
        'player': {
          full_about: 'The main character',
          summarized_about: 'Hero'
        }
      };
      expect(getPlayerDescription('player', playerMeta)).toBe('The main character');
    });

    it('should return fallback message for missing player', () => {
      getUISettings.mockReturnValue({ conciseDescriptions: false });
      const playerMeta = {};
      expect(getPlayerDescription('missing_player', playerMeta)).toBe('No description available.');
    });
  });

  describe('concise mode switching', () => {
    it('should switch descriptions when concise setting changes', () => {
      const item = {
        full_about: 'Full description',
        summarized_about: 'Short description'
      };

      // First call with concise false
      getUISettings.mockReturnValue({ conciseDescriptions: false });
      expect(getDescription(item)).toBe('Full description');

      // Second call with concise true
      getUISettings.mockReturnValue({ conciseDescriptions: true });
      expect(getDescription(item)).toBe('Short description');

      // Third call back to concise false
      getUISettings.mockReturnValue({ conciseDescriptions: false });
      expect(getDescription(item)).toBe('Full description');
    });
  });
});
