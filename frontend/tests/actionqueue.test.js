import { describe, test, expect } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';
import { parse } from 'svelte/compiler';

const actionQueuePath = join(import.meta.dir, '../src/lib/battle/ActionQueue.svelte');
const actionQueueSource = readFileSync(actionQueuePath, 'utf8');

function getAttributeValue(node, name) {
  const attr = node?.attributes?.find((a) => a.type === 'Attribute' && a.name === name);
  if (!attr) return '';
  return attr.value
    .map((segment) => (segment.type === 'Text' ? segment.data : segment.raw ?? ''))
    .join('');
}

function hasStaticClass(node, className) {
  const classes = getAttributeValue(node, 'class')
    .split(/\s+/)
    .filter(Boolean);
  return classes.includes(className);
}

function traverse(node, callback) {
  if (!node || typeof node !== 'object') return;
  callback(node);
  for (const value of Object.values(node)) {
    if (Array.isArray(value)) {
      for (const item of value) {
        traverse(item, callback);
      }
    } else if (value && typeof value === 'object' && 'type' in value) {
      traverse(value, callback);
    }
  }
}

function findElements(root, predicate) {
  const matches = [];
  traverse(root, (node) => {
    if (node.type === 'Element' && predicate(node)) {
      matches.push(node);
    }
  });
  return matches;
}

describe('ActionQueue component', () => {
  test('renders portraits and optional action values', () => {
    expect(actionQueueSource).toContain('getCharacterImage');
    expect(actionQueueSource).toContain('showActionValues');
    expect(actionQueueSource).toContain('flashEnrageCounter');
    expect(actionQueueSource).toContain('showTurnCounter');
    expect(actionQueueSource).toContain('animate:flip');
    expect(actionQueueSource).toContain('bonus-badge');
    expect(actionQueueSource).toContain('class="entry turn-counter"');
    expect(actionQueueSource).toContain('class:enraged={showEnrageChip}');
    expect(actionQueueSource).toContain('class:motionless={motionDisabled}');
    expect(actionQueueSource).toContain('class="turn-card"');
    expect(actionQueueSource).toContain('class="turn-label"');
    expect(actionQueueSource).toContain('class="turn-value"');
    expect(actionQueueSource).toContain('class="enrage-chip"');
  });

  test('includes a turn counter tile with enrage-aware markup', () => {
    const ast = parse(actionQueueSource);
    const [turnCounter] = findElements(ast.html, (node) => hasStaticClass(node, 'entry') && hasStaticClass(node, 'turn-counter'));

    expect(turnCounter, 'turn counter entry markup missing').toBeDefined();
    expect(turnCounter.attributes.some((attr) => attr.type === 'Class' && attr.name === 'enraged'))
      .toBe(true);
    expect(turnCounter.attributes.some((attr) => attr.type === 'Class' && attr.name === 'motionless'))
      .toBe(true);

    const [turnCard] = findElements(turnCounter, (node) => hasStaticClass(node, 'turn-card'));
    expect(turnCard, 'turn counter inner card missing').toBeDefined();

    const [turnLabel] = findElements(turnCounter, (node) => hasStaticClass(node, 'turn-label'));
    expect(turnLabel, 'turn label container missing').toBeDefined();

    const [labelText] = findElements(turnCounter, (node) => hasStaticClass(node, 'label-text'));
    expect(labelText, 'turn label text missing').toBeDefined();

    const [turnValue] = findElements(turnCounter, (node) => hasStaticClass(node, 'turn-value'));
    expect(turnValue, 'turn value element missing').toBeDefined();

    const [enrageChip] = findElements(turnCounter, (node) => hasStaticClass(node, 'enrage-chip'));
    expect(enrageChip, 'enrage chip element missing').toBeDefined();
    expect(enrageChip.attributes.some((attr) => attr.type === 'Class' && attr.name === 'pulse'))
      .toBe(true);
  });

  test('defines enraged turn counter styling', () => {
    expect(actionQueueSource).toMatch(/\.entry\.turn-counter\.enraged\s*{[^}]+--turn-accent/);
    expect(actionQueueSource).toMatch(/\.entry\.turn-counter\s+\.enrage-chip/);
  });
});

describe('Settings menu toggle', () => {
  const content = readFileSync(join(import.meta.dir, '../src/lib/components/GameplaySettings.svelte'), 'utf8');
  test('includes Show Action Values control', () => {
    expect(content).toContain('Show Action Values');
    expect(content).toContain('bind:checked={showActionValues}');
  });
  test('includes Show Turn Counter control', () => {
    expect(content).toContain('Show Turn Counter');
    expect(content).toContain('bind:checked={showTurnCounter}');
  });
  test('includes Flash Enrage Counter control', () => {
    expect(content).toContain('Flash Enrage Counter');
    expect(content).toContain('bind:checked={flashEnrageCounter}');
  });
  test('includes Full Idle Mode control', () => {
    expect(content).toContain('Full Idle Mode');
    expect(content).toContain('bind:checked={fullIdleMode}');
  });
  test('includes Animation Speed slider', () => {
    expect(content).toContain('Animation Speed');
    expect(content).toContain('DotSelector');
    expect(content).toContain('bind:value={dotSpeed}');
  });
});
