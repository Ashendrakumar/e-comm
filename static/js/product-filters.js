/* Filter panel behaviour, shared by /products/ and /products/category/<slug>/.
   #filter-form is the single source of truth for what is applied; the panel
   ships a hidden scope_cat field so the same endpoint serves both routes.
   The endpoint URL is read from #filter-form[data-ajax-url] (rendered by
   Django) instead of being inlined in a template. */
const FILTER_AJAX_URL = document.getElementById('filter-form')?.dataset.ajaxUrl;
// Every other function guards on its own hooks, so a page that loads this
// without a #filter-form simply does nothing instead of throwing on line 1.

// ── Accordion ──────────────────────────────────────────────────────
function toggleAcc(btn){ btn.closest('.filter-section').classList.toggle('collapsed'); }

// ── Mobile drawer ──────────────────────────────────────────────────
function openMobileFilter(){
  const d=document.getElementById('mob-filter'), p=document.getElementById('mob-panel');
  if(!d) return;
  d.classList.remove('hidden');
  if(p) requestAnimationFrame(()=>p.classList.remove('translate-x-full'));
}
function closeMobileFilter(){
  const d=document.getElementById('mob-filter'), p=document.getElementById('mob-panel');
  if(!d) return;
  if(!p){ d.classList.add('hidden'); return; }
  p.classList.add('translate-x-full');
  setTimeout(()=>d.classList.add('hidden'),250);
}

// ── Grid / List toggle ─────────────────────────────────────────────
function setView(v){
  const grid=document.getElementById('product-grid');
  const bG=document.getElementById('btn-grid');
  const bL=document.getElementById('btn-list');
  const on ='px-3 py-2 bg-primary-600 text-white transition-colors';
  const off='px-3 py-2 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors';
  if(v==='list'){
    if(grid) grid.classList.add('list-mode');
    if(bG) bG.className=off;
    if(bL) bL.className=on+' border-l border-gray-200 dark:border-gray-700';
  } else {
    if(grid) grid.classList.remove('list-mode');
    if(bG) bG.className=on;
    if(bL) bL.className=off+' border-l border-gray-200 dark:border-gray-700';
  }
  localStorage.setItem('pview',v);
}

// ── Skeleton loader ────────────────────────────────────────────────
function showSkeleton(){
  const grid=document.getElementById('product-grid');
  if(!grid) return;
  const n=Math.min(parseInt(document.getElementById('perpage-select')?.value||12,10)||12,12);
  grid.classList.remove('list-mode');
  grid.innerHTML=Array.from({length:n}).map(()=>'<div class="skeleton skeleton-card"></div>').join('');
}

// ── Core AJAX loader ───────────────────────────────────────────────
function ajaxLoad(params){
  const view=localStorage.getItem('pview')||'grid';
  params.set('view',view);

  const section=document.getElementById('products-section');
  if(!section) return;
  showSkeleton();
  section.style.opacity='0.6';
  section.style.pointerEvents='none';

  // Reflect state in the URL so refresh / share / back-button work. pathname is
  // kept as-is, which is what keeps this working on every route.
  history.replaceState({},'',window.location.pathname+'?'+params.toString());

  fetch(FILTER_AJAX_URL+'?'+params.toString(),{headers:{'X-Requested-With':'XMLHttpRequest'}})
    .then(r=>r.json())
    .then(data=>{
      section.innerHTML=data.html+'<div id="pagination-section">'+data.pagination+'</div>';
      document.querySelectorAll('#live-count,#result-count').forEach(el=>el.textContent=data.count);
      const cw=document.getElementById('chip-wrap');
      if(cw && typeof data.chips==='string') cw.innerHTML=data.chips;
      section.style.opacity='';
      section.style.pointerEvents='';
      if(typeof updateCompareUI==='function') updateCompareUI();
      if(view==='list'){ const g=document.getElementById('product-grid'); if(g) g.classList.add('list-mode'); }
    })
    .catch(()=>{section.style.opacity='';section.style.pointerEvents='';});
}

// Build params from the desktop filter form + toolbar controls
function collectParams(){
  const form=document.getElementById('filter-form');
  const params=new URLSearchParams(new FormData(form));
  // Drop empty values so the URL stays clean. `scope_cat` is never empty when
  // present, so the page's category scope always survives this.
  for(const k of [...params.keys()]){ if(params.get(k)==='') params.delete(k); }
  const sort=document.getElementById('sort-select')?.value;
  const per =document.getElementById('perpage-select')?.value;
  if(sort) params.set('sort',sort);
  if(per)  params.set('per_page',per);
  params.delete('page');
  return params;
}

// ── AJAX filter (called on every control change) ───────────────────
function doAjaxFilter(){ ajaxLoad(collectParams()); }

// ── Chip removal — reset the control, then re-filter ───────────────
// Going through the form (rather than editing the query string) keeps the
// sidebar and the results in sync, and keeps `scope_cat` untouched.
function clearFilterControl(key,val){
  const form=document.getElementById('filter-form');
  if(!form) return;
  if(key==='price_range'){
    form.querySelectorAll('[name=min_price],[name=max_price]').forEach(el=>el.value='');
    form.querySelectorAll('.price-preset').forEach(b=>b.classList.remove('active'));
    return;
  }
  const fields=[...form.querySelectorAll('[name="'+key+'"]')];
  if(!fields.length) return;
  const radios=fields.filter(el=>el.type==='radio');
  if(radios.length){
    radios.forEach(el=>{ el.checked = el.value===''; });
    return;
  }
  fields.forEach(el=>{
    if(el.type==='checkbox'){ if(!val || el.value===val) el.checked=false; }
    else el.value='';
  });
}
function removeFilterChip(key,val){ clearFilterControl(key,val); doAjaxFilter(); }

// ── Wire-up ────────────────────────────────────────────────────────
(function(){
  const form=document.getElementById('filter-form');
  if(form){
    // Checkbox / radio changes filter immediately
    form.querySelectorAll('input[type=checkbox],input[type=radio]')
        .forEach(el=>el.addEventListener('change',doAjaxFilter));

    // Debounced text search + price inputs
    let debounce;
    form.querySelectorAll('.js-live-search,.js-live-price').forEach(el=>{
      el.addEventListener('input',()=>{ clearTimeout(debounce); debounce=setTimeout(doAjaxFilter,500); });
    });

    // Price quick presets
    form.querySelectorAll('.price-preset').forEach(btn=>{
      btn.addEventListener('click',()=>{
        form.querySelector('[name=min_price]').value=btn.dataset.min||'';
        form.querySelector('[name=max_price]').value=btn.dataset.max||'';
        form.querySelectorAll('.price-preset').forEach(b=>b.classList.remove('active'));
        btn.classList.add('active');
        doAjaxFilter();
      });
    });

    // "Apply Filters" is a no-op fallback for no-JS; intercept it here
    form.addEventListener('submit',e=>{ e.preventDefault(); doAjaxFilter(); });
  }

  // AJAX pagination — delegated, so it survives innerHTML replacement
  const section=document.getElementById('products-section');
  if(section){
    section.addEventListener('click',e=>{
      const link=e.target.closest('#pagination-wrap a');
      if(!link) return;
      e.preventDefault();
      ajaxLoad(new URLSearchParams(link.search));
      const anchor=document.querySelector('.max-w-7xl');
      if(anchor) window.scrollTo({top:anchor.offsetTop-20,behavior:'smooth'});
    });
  }

  // Restore saved grid/list preference
  if((localStorage.getItem('pview')||'grid')==='list') setView('list');
})();
