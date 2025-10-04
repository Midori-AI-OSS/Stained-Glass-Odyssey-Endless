import { beforeEach, describe, expect, test } from 'vitest';
import { cleanup, render, screen } from '@testing-library/svelte';
import OverlayHost from '../src/lib/components/OverlayHost.svelte';
import { overlayView, overlayData, homeOverlay } from '../src/lib/systems/OverlayController.js';

const baseProps = {
  selected: [],
  runId: '',
  roomData: null,
  shopProcessing: false,
  battleSnapshot: null,
  editorState: {},
  sfxVolume: 5,
  musicVolume: 5,
  voiceVolume: 5,
  framerate: 60,
  reducedMotion: false,
  showActionValues: false,
  showTurnCounter: true,
  flashEnrageCounter: true,
  fullIdleMode: false,
  skipBattleReview: false,
  animationSpeed: 1,
  selectedParty: [],
  battleActive: false,
  backendFlavor: ''
};

describe('run-ended overlay view', () => {
  beforeEach(() => {
    cleanup();
    homeOverlay();
    overlayData.set({});
  });

  test('renders run ended confirmation copy', () => {
    overlayView.set('run-ended');
    render(OverlayHost, { props: baseProps });

    expect(screen.getByText('Run Ended')).toBeTruthy();
    expect(screen.getByText(/ended this run manually/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /return/i })).toBeTruthy();
  });
});
