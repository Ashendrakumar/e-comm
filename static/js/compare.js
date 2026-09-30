/* Compare page: remove / clear products, difference highlighting and the
   "show only differences" filter. Rows are rendered server-side; rows marked
   [data-diff-check] (rating, availability) get their .is-diff flag here from
   each cell's data-value. */
(function(){
  const cfg   = document.getElementById('cmp-config');
  const table = document.getElementById('compare-table');
  if(!cfg) return;

  const LIST_URL    = cfg.dataset.listUrl;
  const COMPARE_URL = cfg.dataset.compareUrl;
  const itemsEl     = document.getElementById('cmp-items');
  const shown       = itemsEl ? JSON.parse(itemsEl.textContent) : [];

  // Keep localStorage in step with what the server actually rendered — ids that
  // were invalid, inactive or deleted are dropped so the compare bar stays honest.
  function save(items){
    localStorage.setItem('tzCompare', JSON.stringify(items));
    if(typeof compareItems !== 'undefined'){ compareItems = items; }
    if(typeof updateCompareUI === 'function'){ updateCompareUI(); }
  }
  save(shown);

  function go(items){
    save(items);
    window.location.href = items.length ? COMPARE_URL + '?' + items.map(p => 'ids=' + encodeURIComponent(p.id)).join('&')
                                        : LIST_URL;
  }

  document.querySelectorAll('[data-remove]').forEach(btn => {
    btn.addEventListener('click', () => go(shown.filter(p => p.id !== btn.dataset.remove)));
  });
  const clearBtn = document.getElementById('cmp-clear');
  if(clearBtn) clearBtn.addEventListener('click', () => go([]));

  if(!table) return;

  table.querySelectorAll('.cmp-row[data-diff-check]').forEach(row => {
    const vals = new Set([...row.querySelectorAll('.cmp-cell[data-value]')].map(c => c.dataset.value));
    row.classList.toggle('is-diff', vals.size > 1);
  });

  const highlight = document.getElementById('cmp-highlight');
  const onlyDiff  = document.getElementById('cmp-only-diff');
  const noDiffRow = table.querySelector('.cmp-no-diff');
  const sections  = [...table.querySelectorAll('.cmp-section')];

  function pref(key, fallback){
    try { const v = localStorage.getItem(key); return v === null ? fallback : v === '1'; }
    catch(e){ return fallback; }
  }
  function setPref(key, on){ try { localStorage.setItem(key, on ? '1' : '0'); } catch(e){} }

  function apply(){
    const hl   = highlight ? highlight.checked : false;
    const only = onlyDiff  ? onlyDiff.checked  : false;
    table.classList.toggle('cmp-highlight', hl);
    table.classList.toggle('cmp-only-diff', only);

    // Hide section headers whose rows are all filtered out.
    sections.forEach(sec => {
      let el = sec.nextElementSibling, visible = false;
      while(el && !el.classList.contains('cmp-section')){
        if(el.classList.contains('cmp-row') && (!only || el.classList.contains('is-diff'))) visible = true;
        el = el.nextElementSibling;
      }
      sec.hidden = !visible;
    });
    if(noDiffRow) noDiffRow.hidden = !(only && !table.querySelector('.cmp-row.is-diff'));
  }

  if(highlight){
    highlight.checked = pref('tzCmpHighlight', true);
    highlight.addEventListener('change', () => { setPref('tzCmpHighlight', highlight.checked); apply(); });
  }
  if(onlyDiff){
    onlyDiff.checked = pref('tzCmpOnlyDiff', false);
    onlyDiff.addEventListener('change', () => { setPref('tzCmpOnlyDiff', onlyDiff.checked); apply(); });
  }
  apply();
})();
