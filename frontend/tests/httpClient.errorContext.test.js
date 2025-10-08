import { afterEach, beforeEach, describe, expect, test } from 'bun:test';

import { httpGet, resetApiBase, __setHttpClientTestOverrides } from '../src/lib/systems/httpClient.js';

describe('httpClient error context handling', () => {
  const overlayCalls = [];

  function overlayMock(type, payload) {
    overlayCalls.push({ type, payload });
  }

  beforeEach(() => {
    overlayCalls.length = 0;
    resetApiBase();
  });

  afterEach(() => {
    __setHttpClientTestOverrides({});
  });

  test('propagates backend context data to overlays and thrown errors', async () => {
    const contextPayload = {
      file: 'backend/routes/ui.py',
      line: 123,
      function: 'explode',
      source: [
        { line: 121, code: 'def explode():', highlight: false },
        { line: 122, code: '    pass', highlight: false },
        { line: 123, code: "    raise RuntimeError('boom')", highlight: true }
      ]
    };

    const fetchMock = async () => ({
      ok: false,
      status: 500,
      text: async () => JSON.stringify({
        error: 'Boom',
        traceback: 'Traceback...',
        context: contextPayload
      })
    });

    __setHttpClientTestOverrides({
      openOverlay: overlayMock,
      getApiBase: async () => 'http://api.test',
      fetch: fetchMock
    });

    await expect(httpGet('/explode')).rejects.toMatchObject({
      message: 'Boom',
      context: contextPayload
    });

    expect(overlayCalls.length).toBe(1);
    expect(overlayCalls[0].type).toBe('backend-shutdown');
    expect(overlayCalls[0].payload.message).toBe('Boom');
    const overlayContext = overlayCalls[0].payload.context;
    expect(overlayContext.file).toBe(contextPayload.file);
    expect(overlayContext.line).toBe(contextPayload.line);
    expect(overlayContext.function).toBe(contextPayload.function);
    expect(Array.isArray(overlayContext.source)).toBe(true);
  });
});

