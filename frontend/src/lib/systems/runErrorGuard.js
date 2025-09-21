// Helper utilities for deciding when battle polling should treat an error as run termination.

/**
 * Determine whether a polling error implies the current run has ended.
 * @param {unknown} error - Error thrown by snapshot polling.
 * @returns {boolean} True if the UI should tear down the active run state.
 */
export function shouldHandleRunEndError(error) {
  if (!error) {
    return false;
  }

  const statusNumber = Number(error?.status);
  const status = Number.isFinite(statusNumber) ? statusNumber : undefined;

  const codeCandidates = new Set();
  if (typeof error?.code === 'string') {
    codeCandidates.add(error.code.toUpperCase());
  }
  if (typeof error?.error === 'string') {
    codeCandidates.add(error.error.toUpperCase());
  }
  if (typeof error?.body?.code === 'string') {
    codeCandidates.add(String(error.body.code).toUpperCase());
  }
  if (typeof error?.response?.code === 'string') {
    codeCandidates.add(String(error.response.code).toUpperCase());
  }

  const messageCandidates = [];
  if (typeof error === 'string') {
    messageCandidates.push(error);
  }
  if (typeof error?.message === 'string') {
    messageCandidates.push(error.message);
  }
  if (typeof error?.error === 'string') {
    messageCandidates.push(error.error);
  }
  if (typeof error?.body?.message === 'string') {
    messageCandidates.push(error.body.message);
  }
  if (typeof error?.response?.message === 'string') {
    messageCandidates.push(error.response.message);
  }

  const normalizedMessages = messageCandidates
    .map((msg) => (typeof msg === 'string' ? msg.trim().toLowerCase() : ''))
    .filter((msg) => msg.length > 0);

  if (status === 404) {
    return true;
  }

  if (normalizedMessages.some((msg) => msg.includes('run ended'))) {
    return true;
  }

  if (status === 400 && normalizedMessages.some((msg) => msg.includes('no active run'))) {
    return true;
  }

  if ([...codeCandidates].some((code) => code === 'ERR_NO_ACTIVE_RUN')) {
    return true;
  }

  return false;
}
