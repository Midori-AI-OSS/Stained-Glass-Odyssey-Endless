import { beforeEach, describe, expect, test } from 'vitest';
import { cleanup, render, screen } from '@testing-library/svelte';
import OverlayHost from '../src/lib/components/OverlayHost.svelte';
import { overlayView, overlayData, homeOverlay } from '../src/lib/systems/OverlayController.js';

const baseProps = {
  selected: [],
  runId: 'run-123',
  roomData: { result: 'defeat', ended: true },
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

describe('defeat overlay', () => {
  beforeEach(() => {
    cleanup();
    homeOverlay();
    overlayData.set({});
  });

  test('renders Run Lost messaging', () => {
    overlayView.set('defeat');
    render(OverlayHost, { props: baseProps });

    expect(screen.getByText('Run Lost')).toBeTruthy();
    expect(screen.getByText(/the run has come to an end/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /return/i })).toBeTruthy();
  });
});
