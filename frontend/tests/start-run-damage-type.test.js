import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

const pageSource = readFileSync(join(import.meta.dir, '../src/routes/+page.svelte'), 'utf8');
const partySource = readFileSync(join(import.meta.dir, '../src/lib/components/PartyPicker.svelte'), 'utf8');

function extractFunction(source, name) {
  const asyncToken = `async function ${name}`;
  const funcToken = `function ${name}`;
  let start = source.indexOf(asyncToken);
  if (start === -1) {
    start = source.indexOf(funcToken);
  }
  if (start === -1) {
    throw new Error(`Unable to locate ${name} in source`);
  }

  let parenDepth = 0;
  let braceDepth = 0;
  let bodyFound = false;
  for (let i = start; i < source.length; i += 1) {
    const char = source[i];
    if (char === '(') {
      parenDepth += 1;
    } else if (char === ')') {
      parenDepth -= 1;
    } else if (char === '{' && parenDepth === 0) {
      braceDepth += 1;
      bodyFound = true;
    } else if (char === '}' && parenDepth === 0) {
      braceDepth -= 1;
      if (braceDepth === 0 && bodyFound) {
        return source.slice(start, i + 1);
      }
    }
  }
  throw new Error(`Unable to extract ${name}`);
}

function buildFunction(ctx, source, name) {
  let parenDepth = 0;
  let bodyStart = -1;
  let bodyEnd = source.length - 1;
  let braceDepth = 0;
  for (let i = 0; i < source.length; i += 1) {
    const ch = source[i];
    if (ch === '(') {
      parenDepth += 1;
    } else if (ch === ')') {
      parenDepth -= 1;
    } else if (ch === '{' && parenDepth === 0) {
      if (bodyStart === -1) {
        bodyStart = i;
      }
      braceDepth += 1;
    } else if (ch === '}' && parenDepth === 0) {
      braceDepth -= 1;
      if (braceDepth === 0) {
        bodyEnd = i;
        break;
      }
    }
  }

  const signature = source.slice(0, bodyStart).trim();
  const body = source.slice(bodyStart + 1, bodyEnd);
  const params = signature.slice(signature.indexOf('(') + 1, signature.lastIndexOf(')'));
  const isAsync = signature.startsWith('async');
  const fnKeyword = isAsync ? 'async function' : 'function';
  const factoryBody =
    'return ' + fnKeyword + '(' + params + ') { with (ctx) { ' + body + ' } };';
  return new Function('ctx', factoryBody)(ctx);
}

const handleEditorChangeSource = extractFunction(pageSource, 'handleEditorChange');
const applyPlayerConfigSource = extractFunction(pageSource, 'applyPlayerConfig');
const syncPlayerConfigSource = extractFunction(pageSource, 'syncPlayerConfig');
const handleStartSource = extractFunction(pageSource, 'handleStart');
const refreshRosterSource = extractFunction(partySource, 'refreshRoster');

function createTestContext() {
  const startRunCalls = [];
  const ctx = {
    editorState: { pronouns: '', damageType: 'Light', hp: 0, attack: 0, defense: 0 },
    editorConfigs: {},
    playerConfigLoaded: false,
    playerConfigPromise: null,
    playerConfigRequests: 0,
    playerRosterRequests: 0,
    startRunCalls,
    dispatched: [],
    selectedParty: ['sample_player'],
    selected: [],
    previewId: null,
    previewElementOverride: '',
    userBuffPercent: 0,
    roster: [],
    browser: true,
    dev: false,
    battleActive: false,
    haltSync: false,
    runId: '',
    mapRooms: [],
    currentIndex: 0,
    currentRoomType: '',
    nextRoom: '',
    animationSpeed: 1,
    fullIdleMode: false,
    getPlayerConfig: async () => {
      ctx.playerConfigRequests += 1;
      return { pronouns: 'they', damage_type: 'Fire', hp: 12, attack: 5, defense: 4 };
    },
    getPlayers: async () => {
      ctx.playerRosterRequests += 1;
      return {
        user: { level: 1 },
        players: [
          {
            id: 'sample_player',
            name: 'Hero',
            about: '',
            owned: true,
            is_player: true,
            element: 'Fire',
            stats: { hp: 10, atk: 5, defense: 2 }
          }
        ]
      };
    },
    getCharacterImage: () => '',
    getRandomFallback: () => '',
    dispatch: (name, detail) => {
      ctx.dispatched.push({ name, detail });
      if (name === 'editorChange' && ctx.handleEditorChange) {
        ctx.handleEditorChange({ detail });
      }
    },
    getActiveRuns: async () => ({ runs: [] }),
    endAllRuns: async () => {},
    stopStatePoll: () => {},
    stopBattlePoll: () => {},
    startStatePoll: () => { ctx.statePollCalls = (ctx.statePollCalls || 0) + 1; },
    saveRunState: () => {},
    homeOverlay: () => {},
    enterRoom: async () => {},
    startRun: async (party, damageType, pressure) => {
      startRunCalls.push([party, damageType, pressure]);
      return { run_id: 'run-001', map: { rooms: [{ room_type: 'event' }, { room_type: 'battle' }], current: 0 } };
    },
    openOverlay: () => {},
    backOverlay: () => {},
    loadRunState: () => ({}),
    clearRunState: () => {},
    pollUIState: async () => {},
    startUIStatePoll: () => {},
    stopUIStatePoll: () => {},
    startBattlePoll: () => {},
    acknowledgeLoot: async () => {},
    updateParty: async () => {},
    getBackendFlavor: async () => 'test',
    sendAction: async () => {},
    getMap: async () => null,
    roomAction: async () => ({}),
    chooseCard: async () => ({}),
    chooseRelic: async () => ({}),
    advanceRoom: async () => ({})
  };

  ctx.handleEditorChange = buildFunction(ctx, handleEditorChangeSource, 'handleEditorChange');
  ctx.applyPlayerConfig = buildFunction(ctx, applyPlayerConfigSource, 'applyPlayerConfig');
  ctx.syncPlayerConfig = buildFunction(ctx, syncPlayerConfigSource, 'syncPlayerConfig');
  ctx.handleStart = buildFunction(ctx, handleStartSource, 'handleStart');
  ctx.refreshRoster = buildFunction(ctx, refreshRosterSource, 'refreshRoster');

  return ctx;
}

describe('start run damage type persistence', () => {
  test('loads backend element and preserves it when starting a run', async () => {
    const ctx = createTestContext();

    await ctx.handleStart({ detail: { pressure: 2 } });

    expect(ctx.playerConfigRequests).toBeGreaterThan(0);
    expect(ctx.startRunCalls.length).toBe(1);
    expect(ctx.startRunCalls[0][1]).toBe('Fire');
    expect(ctx.editorState.damageType).toBe('Fire');
    expect(ctx.editorConfigs.player.damageType).toBe('Fire');

    ctx.editorState = { pronouns: '', damageType: 'Light', hp: 0, attack: 0, defense: 0 };
    ctx.editorConfigs = {};
    ctx.playerConfigLoaded = false;
    ctx.playerConfigPromise = null;
    ctx.dispatched = [];

    await ctx.refreshRoster();

    expect(ctx.playerRosterRequests).toBeGreaterThan(0);
    const editorEvent = ctx.dispatched.find((event) => event.name === 'editorChange');
    expect(editorEvent?.detail?.damageType).toBe('Fire');
    expect(ctx.editorState.damageType).toBe('Fire');
  });
});
