import { describe, expect, it } from 'bun:test';
import { shouldHandleRunEndError } from '../src/lib/systems/runErrorGuard.js';

describe('shouldHandleRunEndError', () => {
  it('returns true for 404 status errors', () => {
    expect(shouldHandleRunEndError({ status: 404 })).toBe(true);
  });

  it('returns true when message indicates the run ended', () => {
    expect(shouldHandleRunEndError({ message: 'Run ended remotely' })).toBe(true);
  });

  it('returns true for 400 status with "No active run" message', () => {
    expect(shouldHandleRunEndError({ status: 400, message: 'No active run' })).toBe(true);
  });

  it('returns true for mixed-case "No active run" message', () => {
    expect(shouldHandleRunEndError({ status: '400', error: 'NO ACTIVE RUN' })).toBe(true);
  });

  it('returns true when backend error code indicates no active run', () => {
    expect(shouldHandleRunEndError({ code: 'ERR_NO_ACTIVE_RUN' })).toBe(true);
    expect(shouldHandleRunEndError({ body: { code: 'ERR_NO_ACTIVE_RUN' } })).toBe(true);
  });

  it('returns false for unrelated 400 errors', () => {
    expect(shouldHandleRunEndError({ status: 400, message: 'Bad request' })).toBe(false);
  });

  it('returns false for other errors', () => {
    expect(shouldHandleRunEndError({ status: 500, message: 'Server error' })).toBe(false);
    expect(shouldHandleRunEndError(null)).toBe(false);
  });
});
