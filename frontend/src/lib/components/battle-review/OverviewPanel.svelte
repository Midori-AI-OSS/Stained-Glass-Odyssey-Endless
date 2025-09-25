<script>
  import { getContext } from 'svelte';
  import {
    Zap,
    Shield,
    Flame,
    Heart,
    Skull,
    XOctagon,
    HeartOff,
    TrendingUp
  } from 'lucide-svelte';
  import DamageOverview from './DamageOverview.svelte';
  import ActionComparison from './ActionComparison.svelte';
  import EffectsSummary from './EffectsSummary.svelte';
  import OverviewDetails from './OverviewDetails.svelte';
  import { BATTLE_REVIEW_CONTEXT_KEY } from '../../systems/battleReview/state.js';
  import { fmt } from './utils.js';

  const {
    summary,
    overviewTotals,
    overviewGrand,
    displayParty,
    displayFoes,
    props
  } = getContext(BATTLE_REVIEW_CONTEXT_KEY);

  const detailConfigs = [
    {
      key: 'critical_hits',
      icon: Zap,
      title: 'Critical Hits Analysis',
      formatter: (data, entity, amount) => {
        const critDamage = data.critical_damage?.[entity];
        return `${fmt(amount)} crits${critDamage ? ` (${fmt(critDamage)} dmg)` : ''}`;
      }
    },
    {
      key: 'shield_absorbed',
      icon: Shield,
      title: 'Shield Protection',
      formatter: (_data, _entity, amount) => `${fmt(amount)} absorbed`
    },
    {
      key: 'dot_damage',
      icon: Flame,
      title: 'DoT Damage',
      formatter: (_data, _entity, amount) => `${fmt(amount)} DoT dmg`
    },
    {
      key: 'hot_healing',
      icon: Heart,
      title: 'HoT Healing',
      formatter: (_data, _entity, amount) => `${fmt(amount)} HoT heal`
    },
    {
      key: 'kills',
      icon: Skull,
      title: 'Kills',
      formatter: (_data, _entity, amount) => `${fmt(amount)} kills`
    },
    {
      key: 'dot_kills',
      icon: Flame,
      title: 'DoT Kills',
      formatter: (_data, _entity, amount) => `${fmt(amount)} DoT kills`
    },
    {
      key: 'ultimates_used',
      icon: Zap,
      title: 'Ultimates Used',
      formatter: (_data, _entity, amount) => `${fmt(amount)} used`
    },
    {
      key: 'ultimate_failures',
      icon: XOctagon,
      title: 'Ultimate Failures',
      formatter: (_data, _entity, amount) => `${fmt(amount)} failed`
    },
    {
      key: 'healing_prevented',
      icon: HeartOff,
      title: 'Healing Prevented',
      formatter: (_data, _entity, amount) => `${fmt(amount)} prevented`
    },
    {
      key: 'temporary_hp_granted',
      icon: TrendingUp,
      title: 'Temporary HP',
      formatter: (_data, _entity, amount) => `${fmt(amount)} temp HP`
    }
  ];

  function buildPartyTotals(data, list) {
    return Object.entries(data.damage_by_type || {})
      .filter(([id]) => list.some((entity) => entity.id === id))
      .reduce((acc, [_, damages]) => {
        Object.entries(damages || {}).forEach(([element, amount]) => {
          acc[element] = (acc[element] || 0) + (amount || 0);
        });
        return acc;
      }, {});
  }

  function buildActionTotals(data, ids) {
    const source = data.damage_by_action || {};
    return Object.entries(source)
      .filter(([id]) => ids.includes(id))
      .reduce((acc, [_, actions]) => {
        Object.entries(actions || {}).forEach(([action, amount]) => {
          acc[action] = (acc[action] || 0) + (amount || 0);
        });
        return acc;
      }, {});
  }

  function buildDetailEntries(data, key, formatter) {
    return Object.entries(data?.[key] || {})
      .sort((a, b) => (b[1] || 0) - (a[1] || 0))
      .map(([entity, amount]) => ({ entity, label: formatter(data, entity, amount) }));
  }

  function resourceEntries(data) {
    const entities = new Set([
      ...Object.keys(data.resources_spent || {}),
      ...Object.keys(data.resources_gained || {})
    ]);
    return Array.from(entities).map((entity) => {
      const spent = data.resources_spent?.[entity] || {};
      const gained = data.resources_gained?.[entity] || {};
      const types = Array.from(new Set([...Object.keys(spent), ...Object.keys(gained)]));
      const lines = types.map((type) => `${type}: ${fmt(spent[type] || 0)} spent / ${fmt(gained[type] || 0)} gained`);
      return { entity, label: lines.join(' • ') };
    });
  }

  function effectEntries(effects = {}) {
    return Object.entries(effects)
      .sort((a, b) => (b[1] || 0) - (a[1] || 0))
      .map(([name, count]) => ({ name, count }));
  }

  $: summaryData = $summary || {};
  $: totals = $overviewTotals || {};
  $: grandTotal = $overviewGrand || 0;
  $: partyDamage = buildPartyTotals(summaryData, $displayParty || []);
  $: foeDamage = buildPartyTotals(summaryData, $displayFoes || []);
  $: partyTotal = Object.values(partyDamage).reduce((a, b) => a + b, 0);
  $: foeTotal = Object.values(foeDamage).reduce((a, b) => a + b, 0);
  $: combatTotal = partyTotal + foeTotal;
  $: partyActions = buildActionTotals(summaryData, summaryData.party_members || []);
  $: foeActions = buildActionTotals(summaryData, summaryData.foes || []);
  $: detailSections = detailConfigs.map((config) => ({
    icon: config.icon,
    title: config.title,
    entries: buildDetailEntries(summaryData, config.key, config.formatter)
  }));
  $: resources = resourceEntries(summaryData);
  $: effectApplications = effectEntries(summaryData.effect_applications || {}).slice(0, 8);
  $: relicEffects = summaryData.relic_effects || {};
  $: cardEffects = summaryData.card_effects || {};
</script>

<section class="overview-grid">
  <DamageOverview
    totals={totals}
    grandTotal={grandTotal}
    summary={summaryData}
    cards={$props.cards || []}
    relics={$props.relics || []}
    partyTotals={{ partyDamage, foeDamage, partyTotal, foeTotal, combatTotal }}
  />

  <ActionComparison {partyActions} {foeActions} />

  <EffectsSummary {relicEffects} {cardEffects} />

  <OverviewDetails {detailSections} {resources} {effectApplications} />
</section>

<style>
  .overview-grid {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
</style>
