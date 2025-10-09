import { describe, it, expect, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Script, createContext } from 'node:vm';

function extractProcessRecentEvents(source) {
  const anchor = 'function processRecentEvents';
  const start = source.indexOf(anchor);
  if (start === -1) {
    throw new Error('processRecentEvents definition not found');
  }

  let depth = 0;
  let inSingle = false;
  let inDouble = false;
  let inTemplate = false;
  let templateExprDepth = 0;
  let prev = '';
  let end = source.length;

  for (let index = start; index < source.length; index += 1) {
    const char = source[index];

    if (inSingle) {
      if (char === "'" && prev !== '\\') {
        inSingle = false;
      }
    } else if (inDouble) {
      if (char === '"' && prev !== '\\') {
        inDouble = false;
      }
    } else if (inTemplate) {
      if (templateExprDepth === 0) {
        if (char === '`' && prev !== '\\') {
          inTemplate = false;
        } else if (char === '{' && prev === '$') {
          templateExprDepth = 1;
        }
      } else {
        if (char === '{') {
          templateExprDepth += 1;
        } else if (char === '}') {
          templateExprDepth -= 1;
        }
      }
    } else {
      if (char === "'") {
        inSingle = true;
      } else if (char === '"') {
        inDouble = true;
      } else if (char === '`') {
        inTemplate = true;
      } else if (char === '{') {
        depth += 1;
      } else if (char === '}') {
        depth -= 1;
        if (depth === 0) {
          end = index + 1;
          break;
        }
      }
    }

    prev = char;
  }

  if (depth !== 0) {
    throw new Error('Failed to parse processRecentEvents body');
  }

  return source.slice(start, end);
}

const here = fileURLToPath(new URL('.', import.meta.url));

function loadProcessRecentEvents() {
  const source = readFileSync(
    join(here, '../src/lib/components/BattleView.svelte'),
    'utf8'
  );
  const fnSource = extractProcessRecentEvents(source);

  const queueTickIndicators = vi.fn();

  const context = createContext({
    recentEventCounts: new Map(),
    lastRecentEventTokens: [],
    relevantRecentEventTypes: new Set(['damage_taken']),
    normalizeRecentEvent: (event) => event,
    eventToken: (event) => event.token,
    queueTickIndicators,
    Map,
    Set,
    Array,
    console,
  });

  const script = new Script(`${fnSource};processRecentEvents`);
  script.runInContext(context);

  return {
    processRecentEvents: context.processRecentEvents,
    context,
    queueTickIndicators,
  };
}

describe('BattleView recent event processing', () => {
  it('resets dedupe state when an empty payload arrives between identical batches', () => {
    const { processRecentEvents, context, queueTickIndicators } = loadProcessRecentEvents();

    const batch = [
      { type: 'damage_taken', token: 'foe:hit:1', amount: 8 },
      { type: 'damage_taken', token: 'foe:hit:1', amount: 8 },
    ];

    const first = processRecentEvents(batch);
    expect(first).toHaveLength(2);
    expect(queueTickIndicators).toHaveBeenCalledTimes(1);
    expect(context.recentEventCounts.get('foe:hit:1')).toBe(2);
    expect(context.lastRecentEventTokens).toEqual(['foe:hit:1', 'foe:hit:1']);

    const reset = processRecentEvents([]);
    expect(reset).toHaveLength(0);
    expect(context.recentEventCounts.size).toBe(0);
    expect(context.lastRecentEventTokens).toEqual([]);

    const second = processRecentEvents(batch);
    expect(second).toHaveLength(2);
    expect(queueTickIndicators).toHaveBeenCalledTimes(2);
    expect(context.recentEventCounts.get('foe:hit:1')).toBe(2);
  });
});
