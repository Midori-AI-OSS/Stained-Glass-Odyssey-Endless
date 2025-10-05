import { beforeEach, describe, expect, test, vi } from 'vitest';

vi.mock('../src/lib/systems/httpClient.js', () => ({
  httpGet: vi.fn(),
  httpPost: vi.fn()
}));

import { getRunConfigurationMetadata, resetRunConfigurationMetadataCache } from '../src/lib/systems/uiApi.js';
import { httpGet } from '../src/lib/systems/httpClient.js';

const STORAGE_KEY = 'run_config_metadata_v1';

function createMetadata(version) {
  return { version, run_types: [], modifiers: [] };
}

describe('run configuration metadata caching', () => {
  beforeEach(() => {
    resetRunConfigurationMetadataCache();
    httpGet.mockReset();
    if (typeof window !== 'undefined') {
      window.sessionStorage.clear();
    }
  });

  test('returns cached metadata on subsequent calls', async () => {
    httpGet.mockResolvedValueOnce(createMetadata('2025.02'));

    const first = await getRunConfigurationMetadata();
    expect(httpGet).toHaveBeenCalledTimes(1);
    expect(first.version).toBe('2025.02');

    const second = await getRunConfigurationMetadata();
    expect(httpGet).toHaveBeenCalledTimes(1);
    expect(second.version).toBe('2025.02');
  });

  test('refetches when requested hash differs from cache', async () => {
    httpGet.mockResolvedValueOnce(createMetadata('2025.02'));
    await getRunConfigurationMetadata();

    httpGet.mockResolvedValueOnce(createMetadata('2025.03'));
    const refreshed = await getRunConfigurationMetadata({ metadataHash: '2025.03' });
    expect(httpGet).toHaveBeenCalledTimes(2);
    expect(refreshed.version).toBe('2025.03');
  });

  test('hydrates from sessionStorage without fetching', async () => {
    const stored = { hash: '2025.04', payload: createMetadata('2025.04'), savedAt: Date.now() };
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(stored));

    const metadata = await getRunConfigurationMetadata();
    expect(httpGet).not.toHaveBeenCalled();
    expect(metadata.version).toBe('2025.04');
  });

  test('reset clears cache and storage', async () => {
    httpGet.mockResolvedValueOnce(createMetadata('2025.05'));
    await getRunConfigurationMetadata();
    expect(window.sessionStorage.getItem(STORAGE_KEY)).not.toBeNull();

    resetRunConfigurationMetadataCache();
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull();

    httpGet.mockResolvedValueOnce(createMetadata('2025.06'));
    await getRunConfigurationMetadata();
    expect(httpGet).toHaveBeenCalledTimes(1);
  });
});
