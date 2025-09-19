<script>
  import MenuPanel from './MenuPanel.svelte';
  import { Coins } from 'lucide-svelte';
  import { createEventDispatcher, onMount } from 'svelte';
  import RewardCard from './RewardCard.svelte';
  import CurioChoice from './CurioChoice.svelte';
  import { getCardCatalog, getRelicCatalog } from '../systems/api.js';
  import { EFFECT_DESCRIPTIONS, ITEM_EFFECT_MAP } from '../systems/effectsInfo.js';

  export let items = [];
  export let gold = 0;
  export let reducedMotion = false;
  export let itemsBought = 0;
  export let taxSummary = null;

  const dispatch = createEventDispatcher();
  // Preserve original stock ordering and keep purchased items visible until unload
  let baseList = []; // enriched entries with stable keys
  let awaitingReroll = false;
  let soldKeys = new Set();
  let selectedKeys = new Set();
  let currentIndex = 0; // center index for carousel
  // Light nav lock to avoid rapid index changes; keeps motion stable
  let navLocked = false;
  const NAV_LOCK_MS = 420;

  function toFinite(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
  }

  function pickFinite(...values) {
    for (const value of values) {
      const resolved = toFinite(value);
      if (resolved !== null) return resolved;
    }
    return null;
  }

  function pricingOf(entry) {
    if (!entry || typeof entry !== 'object') {
      return { base: 0, taxed: 0, tax: 0 };
    }
    const base = pickFinite(
      entry.pricing?.base,
      entry.base_price,
      entry.base_cost,
      entry.basePrice,
      entry.baseCost,
      entry.price,
      entry.cost,
      0
    ) ?? 0;
    const taxed = pickFinite(
      entry.pricing?.taxed,
      entry.taxed_cost,
      entry.taxedCost,
      entry.price,
      entry.cost,
      base
    ) ?? base;
    const tax = pickFinite(
      entry.pricing?.tax,
      entry.tax,
      taxed - base,
      0
    ) ?? Math.max(taxed - base, 0);
    return {
      base,
      taxed,
      tax: tax < 0 ? 0 : tax
    };
  }

  function priceOf(item) {
    return pricingOf(item).taxed;
  }

  // Animation state for reroll button
  let rerollAnimationText = '';
  let isAnimating = false;
  const keyOf = (item) => `${item?.type || 'item'}:${item?.id || ''}:${priceOf(item)}`;
  function buildBaseList(list) {
    const counts = Object.create(null);
    return (list || []).map((raw) => {
      const enriched = enrich(raw);
      const base = keyOf(enriched);
      counts[base] = (counts[base] || 0) + 1;
      const key = `${base}#${counts[base]}`;
      return { ...enriched, key };
    });
  }
  function initBaseOnce() {
    if (!baseList.length && Array.isArray(items) && items.length) {
      baseList = buildBaseList(items);
      currentIndex = 0; // start at first item; wrap-around handles edges
    }
  }
  function buy(item) {
    // mark this entry as sold (by key) and pass through the purchase
    const k = item?.key || keyOf(item);
    if (k) soldKeys.add(k);
    // Force reactivity for Set mutation
    soldKeys = new Set(soldKeys);
    const pricing = pricingOf(item);
    const payload = {
      ...item,
      base_price: pricing.base,
      base_cost: pricing.base,
      taxed_cost: pricing.taxed,
      price: pricing.taxed,
      cost: pricing.taxed,
      tax: pricing.tax
    };
    dispatch('buy', payload);
  }

  function toggleSelect(item) {
    const k = item?.key || keyOf(item);
    if (!k || soldKeys.has(k)) return;
    if (selectedKeys.has(k)) selectedKeys.delete(k);
    else selectedKeys.add(k);
    // Force reactivity for Set mutation
    selectedKeys = new Set(selectedKeys);
    const idx = combinedList.findIndex((it) => it.key === k);
    if (idx >= 0) currentIndex = idx;
  }

  async function buySelected() {
    const list = combinedList.filter((it) => selectedKeys.has(it.key));
    if (!list.length) return;
    for (let i = 0; i < list.length; i++) {
      const item = list[i];
      const k = item.key;
      soldKeys.add(k);
      // Force reactivity so line crosses off immediately
      soldKeys = new Set(soldKeys);
      const pricing = pricingOf(item);
      const payload = {
        ...item,
        base_price: pricing.base,
        base_cost: pricing.base,
        taxed_cost: pricing.taxed,
        price: pricing.taxed,
        cost: pricing.taxed,
        tax: pricing.tax
      };
      dispatch('buy', payload);
      // Slow down purchase processing for stability
      await new Promise((r) => setTimeout(r, 650));
    }
    selectedKeys.clear();
    // Force reactivity after clearing selection
    selectedKeys = new Set();
  }
  
  // Animate text appearing letter by letter with jumping effect
  async function animateRerollText() {
    const fullText = 'Rerolling...';
    rerollAnimationText = '';
    isAnimating = true;
    
    for (let i = 0; i < fullText.length; i++) {
      rerollAnimationText += fullText[i];
      // Wait between each letter (adjust timing as needed)
      await new Promise(resolve => setTimeout(resolve, 150));
    }
    
    isAnimating = false;
  }
  
  async function reroll() {
    if (awaitingReroll) return; // Prevent rapid-fire clicks
    awaitingReroll = true;
    soldKeys = new Set();
    selectedKeys = new Set();
    
    // Start the text animation
    await animateRerollText();
    
    // Add forced wait before sending request
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Now send the actual reroll request
    dispatch('reroll');
  }
  function close() {
    baseList = [];
    soldKeys = new Set();
    awaitingReroll = false;
    rerollAnimationText = '';
    isAnimating = false;
    lastItemsSignature = '';
    dispatch('close');
  }

  // Split incoming stock by type and enrich with catalog metadata
  let cardMeta = {};
  let relicMeta = {};
  onMount(async () => {
    try {
      const [cards, relics] = await Promise.all([getCardCatalog(), getRelicCatalog()]);
      cardMeta = Object.fromEntries(cards.map(c => [c.id, c]));
      relicMeta = Object.fromEntries(relics.map(r => [r.id, r]));
    } catch {}
  });

  // Enrich incoming stock entries with catalog data and presentable about text.
  // For relics, we compute a stable baseAbout to avoid duplicating stack notes
  // during reactive re-enrichment (metadata loads can re-run this).
  function enrich(entry) {
    if (!entry) return entry;
    if (entry.type === 'card') {
      const m = cardMeta[entry.id] || {};
      const baseAbout = entry.about || m.about || '';
      const effectId = ITEM_EFFECT_MAP[entry.id];
      const tooltip = effectId && EFFECT_DESCRIPTIONS[effectId] ? EFFECT_DESCRIPTIONS[effectId] : baseAbout;
      // Ensure visible description by falling back to tooltip when about is empty
      const about = baseAbout || tooltip || '';
      return { ...entry, name: entry.name || m.name || entry.id, stars: entry.stars || m.stars || 1, about, tooltip };
    } else if (entry.type === 'relic') {
      const m = relicMeta[entry.id] || {};
      // Keep a stable baseAbout so reactive re-enrichment doesn't duplicate the suffix
      const baseAbout = entry.baseAbout ?? entry.about ?? m.about ?? '';
      const stacks = typeof entry.stacks === 'number' ? entry.stacks : 0;
      let about = stacks > 0 ? `${baseAbout} (Current stacks: ${stacks})` : baseAbout;
      const effectId = ITEM_EFFECT_MAP[entry.id];
      const tooltip = effectId && EFFECT_DESCRIPTIONS[effectId] ? EFFECT_DESCRIPTIONS[effectId] : baseAbout;
      if (!about) about = tooltip || '';
      return { ...entry, name: entry.name || m.name || entry.id, stars: entry.stars || m.stars || 1, baseAbout, about, tooltip };
    }
    return entry;
  }

  // Track items to detect actual changes (not just re-enrichment)
  let lastItemsSignature = '';
  function getItemsSignature(itemsList) {
    if (!Array.isArray(itemsList) || itemsList.length === 0) return '';
    // Create a signature based on item IDs and prices to detect real changes
    return itemsList
      .map((item) => {
        const pricing = pricingOf(item);
        return `${item?.type || 'item'}:${item?.id || ''}:${pricing.base}:${pricing.taxed}`;
      })
      .join('|');
  }
  
  // Initialize base list on first stock arrival; replace on reroll
  $: initBaseOnce();
  $: {
    // Handle new items arriving (could be from reroll or initial load)
    if (Array.isArray(items) && items.length) {
      const currentSignature = getItemsSignature(items);
      
      // If we're awaiting reroll and items have actually changed, complete the reroll
      if (awaitingReroll && currentSignature !== lastItemsSignature && lastItemsSignature !== '') {
        baseList = buildBaseList(items);
        soldKeys = new Set();
        awaitingReroll = false;
        rerollAnimationText = '';
        isAnimating = false;
        lastItemsSignature = currentSignature;
      }
      // If not awaiting reroll, just update the base list normally
      else if (!awaitingReroll) {
        baseList = buildBaseList(items);
        lastItemsSignature = currentSignature;
      }
    }
  }
  // Keep metadata enrichment reactive. Also depend on catalog readiness so
  // names/descriptions appear as soon as metadata loads, not only after reroll/leave.
  $: enrichedBaseList = (void cardMeta, void relicMeta, baseList.map((e) => ({ ...enrich(e), key: e.key })));
  // Partition for layout
  $: displayCards = enrichedBaseList.filter(e => e?.type === 'card');
  $: displayRelics = enrichedBaseList.filter(e => e?.type === 'relic');

  // Combined list in the order: cards then relics
  $: combinedList = [...displayCards, ...displayRelics];
  $: { if (currentIndex >= combinedList.length) currentIndex = Math.max(0, combinedList.length - 1); }

  function computeVisible(list, index) {
    // 3-item wheel with wrap-around
    const n = (list && list.length) ? list.length : 0;
    if (n === 0) return [];
    if (n === 1) return [{ item: list[0], pos: 0 }];
    const leftIdx = (index - 1 + n) % n;
    const rightIdx = (index + 1) % n;
    const out = [];
    // Keep visual order left, center, right
    out.push({ item: list[leftIdx], pos: -1 });
    out.push({ item: list[index], pos: 0 });
    // If only two items, don't duplicate center
    if (n > 2) out.push({ item: list[rightIdx], pos: 1 });
    return out;
  }
  $: visibleItems = computeVisible(combinedList, currentIndex);

  function prev() {
    const n = combinedList.length;
    if (n === 0) return;
    if (navLocked) { return; }
    navLocked = true;
    const before = currentIndex;
    currentIndex = (currentIndex - 1 + n) % n;
    const after = currentIndex;
    // navigation debug removed
    setTimeout(() => { navLocked = false; }, NAV_LOCK_MS);
  }
  function next() {
    const n = combinedList.length;
    if (n === 0) return;
    if (navLocked) { return; }
    navLocked = true;
    const before = currentIndex;
    currentIndex = (currentIndex + 1) % n;
    const after = currentIndex;
    // navigation debug removed
    setTimeout(() => { navLocked = false; }, NAV_LOCK_MS);
  }

  function estimateCost(item) {
    const p = pricingOf(item);
    return { base: p.base || 0, tax: Math.max(0, p.tax || 0), total: (p.base || 0) + Math.max(0, p.tax || 0) };
  }
  $: selectedList = combinedList
    .filter((it) => selectedKeys.has(it.key))
    .map((item) => ({ item, ...estimateCost(item) }));
  $: estimatedSubtotal = selectedList.reduce((sum, s) => sum + (s.base || 0), 0);
  $: estimatedTax = selectedList.reduce((sum, s) => sum + (s.tax || 0), 0);
  $: estimatedTotal = estimatedSubtotal + estimatedTax;

  $: samplePricing = (() => {
    if (!Array.isArray(enrichedBaseList) || enrichedBaseList.length === 0) {
      return { base: 0, taxed: 0, tax: 0 };
    }
    const withTax = enrichedBaseList.find((entry) => pricingOf(entry).tax > 0);
    if (withTax) return pricingOf(withTax);
    return pricingOf(enrichedBaseList[0]);
  })();

  $: surchargeValue = pickFinite(
    taxSummary?.current_tax,
    taxSummary?.currentTax,
    taxSummary?.tax,
    taxSummary?.surcharge,
    samplePricing.tax
  ) ?? 0;

  $: priorPurchases = pickFinite(
    taxSummary?.items_bought,
    taxSummary?.purchases,
    taxSummary?.itemsBought,
    itemsBought
  ) ?? 0;

  $: surchargeRate = (() => {
    const percent = pickFinite(
      taxSummary?.rate_percent,
      taxSummary?.ratePercent,
      taxSummary?.percent,
      taxSummary?.percentage
    );
    if (percent !== null) return percent;
    const decimal = pickFinite(taxSummary?.rate, taxSummary?.multiplier);
    if (decimal === null) return null;
    return decimal <= 1 ? decimal * 100 : decimal;
  })();

  $: nextSurcharge = pickFinite(
    taxSummary?.next_tax,
    taxSummary?.nextTax,
    taxSummary?.next_tax_amount
  );

  function formatPercent(value) {
    if (!Number.isFinite(value)) return null;
    if (Math.abs(value - Math.round(value)) < 0.05) {
      return `${Math.round(value)}%`;
    }
    return `${value.toFixed(1)}%`;
  }

  function formatSurchargeMessage(summary, tax, prior, rate, next) {
    const directMessage = (typeof summary?.message === 'string' && summary.message.trim())
      ? summary.message.trim()
      : null;
    if (directMessage) return directMessage;
    const description = (typeof summary?.description === 'string' && summary.description.trim())
      ? summary.description.trim()
      : null;
    if (description) return description;

    const parts = [];
    if (tax <= 0) {
      if (prior > 0) {
        parts.push('Tax waived');
        parts.push(`${prior} prior buy${prior === 1 ? '' : 's'}`);
        return parts.join(' · ');
      }
      return 'No tax applied';
    }

    parts.push(`+${tax}g tax`);
    const pct = formatPercent(rate ?? null);
    if (pct) parts.push(`${pct} rate`);
    if (prior > 0) {
      parts.push(`${prior} prior buy${prior === 1 ? '' : 's'}`);
    }
    const pressure = pickFinite(summary?.pressure, summary?.shop_pressure);
    if (pressure !== null) {
      parts.push(`pressure ${pressure}`);
    }
    if (next !== null && Number.isFinite(next) && next !== tax) {
      parts.push(`next +${next}g`);
    }
    return parts.join(' · ');
  }

  $: surchargeMessage = formatSurchargeMessage(
    taxSummary,
    surchargeValue,
    priorPurchases,
    surchargeRate,
    nextSurcharge
  );
  $: taxNoteClass = surchargeValue > 0 ? 'active' : 'inactive';
</script>

<MenuPanel data-testid="shop-menu" padding="0.6rem 0.6rem 0.8rem 0.6rem">
  <div class="header">
    <h3>Shop</h3>
    <div class="spacer" />
    <div class="currency" title="Gold">
      <Coins size={16} class={`coin-icon${!reducedMotion ? ' shine' : ''}`} /> {gold}
    </div>
  </div>
  <div class="bottom">
  <div class="shop-layout">
    <div class="carousel" on:keydown={(e)=>{ if(e.key==='ArrowLeft') prev(); if(e.key==='ArrowRight') next(); }} tabindex="0">
      <button class="nav left" type="button"
        on:click|stopPropagation|preventDefault={prev}
        aria-label="Previous">‹</button>
      <div class="strip">
          {#each visibleItems as { item, pos } (item.key)}
            {@const isCard = item.type === 'card'}
            <div class={`slot pos${pos} ${soldKeys.has(item.key) ? 'sold' : ''} ${selectedKeys.has(item.key) ? 'selected' : ''}`}
                 on:click={() => toggleSelect(item)}
                 title={`${item.name} (${item.stars}★ ${isCard ? 'card' : 'relic'})`}>
            {#if isCard}
              <RewardCard entry={item} type="card" fluid={true} disabled={soldKeys.has(item.key)} />
            {:else}
              <CurioChoice entry={item} fluid={true} disabled={soldKeys.has(item.key)} />
            {/if}
            <div class="slot-price">
              <Coins size={12} class="coin-icon" /> {pricingOf(item).taxed}
            </div>
          </div>
        {/each}
      </div>
      <button class="nav right" type="button"
        on:click|stopPropagation|preventDefault={next}
        aria-label="Next">›</button>
    </div>
    <aside class="receipt">
      <div class="receipt-head">
        <h4>Receipt</h4>
        <div class={`tax-note ${taxNoteClass}`}>{surchargeMessage}</div>
      </div>
      {#if selectedList.length === 0}
        <div class="empty">No items selected.</div>
      {:else}
        <ul class="lines">
          {#each selectedList as sel (sel.item.key)}
            <li class={`line ${soldKeys.has(sel.item.key) ? 'done' : ''}`}>
              <span class="name">{sel.item.name}</span>
              <span class="dots" />
              <span class="price"><Coins size={12} class="coin-icon" /> {sel.total}</span>
            </li>
          {/each}
        </ul>
        <div class="summary">
          <div class="row"><span>Subtotal</span><span class="dots" /><span class="price"><Coins size={12} class="coin-icon" /> {estimatedSubtotal}</span></div>
          <div class="row"><span>Tax (est.)</span><span class="dots" /><span class="price"><Coins size={12} class="coin-icon" /> {estimatedTax}</span></div>
          <div class="row total"><span>Total</span><span class="dots" /><span class="price"><Coins size={12} class="coin-icon" /> {estimatedTotal}</span></div>
        </div>
      {/if}
    </aside>
    <div class="actions actions-under">
      <div class="action-buttons">
        <button class="action primary" disabled={selectedKeys.size === 0} on:click={buySelected}>Buy Selected</button>
        <button class="action" disabled={awaitingReroll} on:click={reroll}>
          {#if awaitingReroll}
            <span class="reroll-text">
              {#each rerollAnimationText.split('') as char, i}
                <span class="jump-letter" style={`animation-delay: ${i * 0.1}s`}>{char}</span>
              {/each}
            </span>
          {:else}
            Reroll
          {/if}
        </button>
        <button class="action" on:click={close}>Leave</button>
      </div>
    </div>
  </div>
  </div>

</MenuPanel>

<style>
  .header { display:flex; align-items:center; gap:0.5rem; }
  .header h3 { margin: 0; }
  .spacer { flex: 1; }
  .currency { display:flex; align-items:center; gap:0.35rem; }
  .coin-icon { color: #d4af37; }
  .shine { animation: coin-shine 2s linear infinite; }
  @keyframes coin-shine { 0%,100% { filter: brightness(1); } 50% { filter: brightness(1.4); } }

  .bottom { margin-top: 0; flex: 1; display:flex; flex-direction:column; align-items:center; justify-content:center; }
  .shop-layout { display:grid; grid-template-columns: minmax(0, 2fr) 240px; column-gap: 1.2rem; row-gap: 0; margin-top: 0.5rem; align-items: center; }
  .carousel { position: relative; display:flex; align-items:center; justify-content:center; min-height: 68vh; }
  .strip { position: relative; display:flex; gap: 1.2rem; align-items:center; justify-content:center; width:100%; padding: 0.25rem 2rem; }
  .nav { position:absolute; top:50%; transform: translateY(-50%); z-index: 50; width: 3rem; height: 3rem; border: 1px solid rgba(255,255,255,0.35); background: rgba(0,0,0,0.7); color:#fff; display:flex; align-items:center; justify-content:center; cursor:pointer; pointer-events:auto; user-select:none; }
  .nav.left { left: 0; }
  .nav.right { right: 0; }
  .slot { position: relative; display:flex; flex-direction:column; align-items:center; justify-content:center; transition: width 360ms ease-in-out, height 360ms ease-in-out, filter 220ms ease, opacity 220ms ease; opacity: 0.98; flex: 0 0 auto; height: clamp(520px, 70vh, 860px); will-change: width, height; }
  .slot.sold { opacity: 0.55; filter: grayscale(0.25); }
  /* Remove selection outline; keep checkmark indicator only */
  .slot.selected::after { display: none; }
  /* Removed checkmark UI for selection to avoid visual bugs */
  .slot-price { margin-top: 0.25rem; font-size: 0.85rem; opacity: 0.9; display:flex; align-items:center; gap: 0.25rem; }
  .pos-1, .pos0, .pos1 {}
  .pos-1 { width: clamp(260px, 26vw, 380px); opacity: 0.96; }
  .pos0  { width: clamp(380px, 42vw, 560px); z-index: 3; }
  .pos1  { width: clamp(260px, 26vw, 380px); opacity: 0.96; }
  /* Make side items shorter than center to reduce visual dominance */
  .pos0  { height: clamp(500px, 66vh, 820px); }
  .pos-1, .pos1 { height: clamp(440px, 56vh, 720px); }
  /* Center (big) relics: slightly reduce round glyph size so it stays inside */
  /* Shop relic sizing: make all relic round glyphs consistent across positions */
  .slot :global(.card-art.fluid) :global(.glyph.round) { width: 70% !important; }
  /* Ensure inner buttons and card art fill the slot, leaving space for price */
  .slot :global(.tooltip-wrapper) {
    display: block;
    width: 100%;
  }
  .slot :global(button.card),
  .slot :global(button.curio) {
    display: block;
    width: 100%;
    height: auto;
  }
  .slot :global(.card-art) {
    width: 100%;
  }

  .receipt { background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.25); padding: 0.6rem 0.6rem 0.2rem 0.6rem; display:flex; flex-direction:column; gap: 0.5rem; min-height: 360px; }
  .receipt-head { display:flex; align-items:center; justify-content:space-between; gap:0.5rem; }
  .receipt h4 { margin: 0; font-size: 1rem; }
  .receipt .empty { opacity: 0.75; font-size: 0.9rem; }
  .lines { list-style: none; padding: 0; margin: 0; display:flex; flex-direction:column; gap: 0.35rem; }
  .line { display:flex; align-items:center; gap: 0.5rem; }
  .line .name { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width: 14rem; }
  .line .dots { flex:1; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent); }
  .line .price { display:flex; align-items:center; gap: 0.25rem; }
  .line.done { opacity: 0.55; text-decoration: line-through; }
  .summary { margin-top: 0.25rem; padding-top: 0.4rem; border-top: 1px solid rgba(255,255,255,0.2); display:flex; flex-direction:column; gap: 0.35rem; }
  .summary .row { display:flex; align-items:center; gap: 0.5rem; }
  .summary .row .dots { flex:1; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent); }
  .summary .row .price { display:flex; align-items:center; gap: 0.25rem; }
  .summary .total { font-weight: 700; }

  /* debug-note removed */

  .actions { display:flex; gap:0.75rem; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-top: 0.75rem; }
  .action-buttons { margin-left:auto; display:flex; gap:0.5rem; }
  .action { border: 1px solid rgba(255,255,255,0.35); background: rgba(0,0,0,0.5); color:#fff; padding: 0.35rem 0.7rem; }
  .action.primary { border-color: color-mix(in srgb, #8ac 60%, #fff); background: rgba(20,30,60,0.6); }
  .action:disabled { opacity: 0.5; cursor: not-allowed; }
  /* Place the action row under the receipt column in the grid */
  .actions-under { grid-column: 2; justify-self: stretch; display:flex; margin-top: 0; }
  .actions-under .action-buttons { margin-left: auto; }
  .tax-note { font-size:0.85rem; opacity:0.9; color:#d4af37; min-width: 12rem; }
  .tax-note.inactive { color:#8ecf8e; }
  .tax-note span { white-space:nowrap; }

  /* Reroll text animation */
  .reroll-text {
    display: inline-block;
  }
  
  .jump-letter {
    display: inline-block;
    animation: letter-jump 0.6s ease-in-out;
  }
  
  @keyframes letter-jump {
    0%, 100% { 
      transform: translateY(0); 
    }
    50% { 
      transform: translateY(-8px); 
    }
  }

  @media (max-width: 920px) {
    .shop-layout { grid-template-columns: 1fr; }
    .actions { flex-direction:column; align-items:stretch; }
    .tax-note { text-align:center; }
    .action-buttons { justify-content:center; margin-left: 0; }
  }
</style>
