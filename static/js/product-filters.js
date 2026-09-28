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
  document.documentElement.style.overflow='hidden';   // only the drawer scrolls while it's open
  if(p) requestAnimationFrame(()=>p.classList.remove('translate-x-full'));
}
function closeMobileFilter(){
  const d=document.getElementById('mob-filter'), p=document.getElementById('mob-panel');
  if(!d) return;
  document.documentElement.style.overflow='';
  if(!p){ d.classList.add('hidden'); return; }
  p.classList.add('translate-x-full');
  setTimeout(()=>d.classList.add('hidden'),250);
}

// ── Skeleton loader ────────────────────────────────────────────────
function showSkeleton(){
  const grid=document.getElementById('product-grid');
  if(!grid) return;
  grid.innerHTML=Array.from({length:12}).map(()=>'<div class="skeleton skeleton-card"></div>').join('');
}

// ── Core AJAX loader ───────────────────────────────────────────────
function ajaxLoad(params){
  const section=document.getElementById('products-section');
  if(!section) return;
  const gen=++loadGen;                 // any in-flight "load more" is now stale
  showSkeleton();
  section.style.opacity='0.6';
  section.style.pointerEvents='none';

  // Reflect state in the URL so refresh / share / back-button work. pathname is
  // kept as-is, which is what keeps this working on every route.
  history.replaceState({},'',window.location.pathname+'?'+params.toString());

  fetch(FILTER_AJAX_URL+'?'+params.toString(),{headers:{'X-Requested-With':'XMLHttpRequest'}})
    .then(r=>r.json())
    .then(data=>{
      if(gen!==loadGen) return;
      section.innerHTML=data.html+'<div id="load-more-section">'+data.load_more+'</div>';
      document.querySelectorAll('#result-count').forEach(el=>el.textContent=data.count);
      const cw=document.getElementById('chip-wrap');
      if(cw && typeof data.chips==='string') cw.innerHTML=data.chips;
      section.style.opacity='';
      section.style.pointerEvents='';
      refreshCardUI();
      watchLoadMore();
    })
    .catch(()=>{section.style.opacity='';section.style.pointerEvents='';});
}

// Build params from the desktop filter form (sort lives in it too)
function collectParams(){
  const form=document.getElementById('filter-form');
  const params=new URLSearchParams(new FormData(form));
  // Drop empty values so the URL stays clean. `scope_cat` is never empty when
  // present, so the page's category scope always survives this.
  for(const k of [...params.keys()]){ if(params.get(k)==='') params.delete(k); }
  params.delete('page');
  params.delete('offset');
  return params;
}

// Re-apply compare / wishlist state to cards that were just rendered
function refreshCardUI(){
  if(typeof updateCompareUI==='function') updateCompareUI();
  if(typeof syncWishlistUI==='function')  syncWishlistUI();
}

// ── Infinite scroll ────────────────────────────────────────────────
// The page opens with FIRST_BATCH products (views.py); when #load-more (under the
// grid) comes into view the next NEXT_BATCH are fetched from the same endpoint with ?offset=N and
// appended. The server omits #load-more once everything is shown.
let loadGen=0, loadingMore=false, moreObserver=null;

function loadMore(){
  const box=document.getElementById('load-more');
  const grid=document.getElementById('product-grid');
  if(!box || !grid || loadingMore || !FILTER_AJAX_URL) return;
  loadingMore=true;
  const gen=loadGen;
  const btn=document.getElementById('load-more-btn');
  if(btn) btn.style.visibility='hidden';   // .btn's display beats [hidden]

  // Skeleton cards stand in for the batch that's coming (NEXT_BATCH, or fewer at the end)
  const offset=parseInt(box.dataset.nextOffset,10)||0;
  const n=Math.max(Math.min(parseInt(box.dataset.batch,10)||8,(parseInt(box.dataset.total,10)||0)-offset),1);
  grid.insertAdjacentHTML('beforeend',
    '<div class="skeleton skeleton-card js-more-skeleton" aria-hidden="true"></div>'.repeat(n));
  grid.setAttribute('aria-busy','true');

  const params=collectParams();
  params.set('offset',offset);

  const done=()=>{
    loadingMore=false;
    grid.querySelectorAll('.js-more-skeleton').forEach(el=>el.remove());
    grid.removeAttribute('aria-busy');
    if(btn) btn.style.visibility='';
  };
  fetch(FILTER_AJAX_URL+'?'+params.toString(),{headers:{'X-Requested-With':'XMLHttpRequest'}})
    .then(r=>r.json())
    .then(data=>{
      done();
      if(gen!==loadGen) return;        // filters changed meanwhile; this batch belongs to the old results
      grid.insertAdjacentHTML('beforeend',data.html);
      refreshCardUI();
      if(data.next_offset){
        box.dataset.nextOffset=data.next_offset;
        // Re-observe so a sentinel that is still on screen triggers the next batch
        if(moreObserver){ moreObserver.unobserve(box); moreObserver.observe(box); }
      } else {
        if(moreObserver) moreObserver.disconnect();
        box.remove();
      }
    })
    .catch(done);
}

function watchLoadMore(){
  if(moreObserver) moreObserver.disconnect();
  const box=document.getElementById('load-more');
  if(!box || !('IntersectionObserver' in window)) return;   // the button still works without it
  moreObserver=new IntersectionObserver(entries=>{
    if(entries.some(e=>e.isIntersecting)) loadMore();
  },{rootMargin:'0px 0px 300px 0px'});   // start fetching a little before the end of the grid
  moreObserver.observe(box);
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
    // Checkbox / radio / sort changes filter immediately
    form.querySelectorAll('input[type=checkbox],input[type=radio],select')
        .forEach(el=>el.addEventListener('change',doAjaxFilter));

    // Debounced text search + price inputs
    let debounce;
    form.querySelectorAll('.js-live-search,.js-live-price').forEach(el=>{
      el.addEventListener('input',()=>{ clearTimeout(debounce); debounce=setTimeout(doAjaxFilter,500); });
    });

    // "Apply Filters" is a no-op fallback for no-JS; intercept it here
    form.addEventListener('submit',e=>{ e.preventDefault(); doAjaxFilter(); });
  }

  // Price quick presets (button.pill.price-preset; .active = selected).
  // Wired in every form that hosts the panel (desktop AJAX form + the mobile
  // drawer's plain form); only #filter-form re-filters immediately.
  document.querySelectorAll('.price-preset').forEach(btn=>{
    const f=btn.form;
    if(!f) return;
    const minEl=f.querySelector('[name=min_price]'), maxEl=f.querySelector('[name=max_price]');
    // Reflect an already-applied preset on page load
    if(minEl && maxEl && (minEl.value||maxEl.value) &&
       minEl.value===(btn.dataset.min||'') && maxEl.value===(btn.dataset.max||'')) btn.classList.add('active');
    btn.addEventListener('click',()=>{
      if(minEl) minEl.value=btn.dataset.min||'';
      if(maxEl) maxEl.value=btn.dataset.max||'';
      f.querySelectorAll('.price-preset').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      if(f===form) doAjaxFilter();
    });
  });
  // Typing a custom price clears the preset highlight
  document.querySelectorAll('.js-live-price').forEach(el=>{
    el.addEventListener('input',()=>{ el.form?.querySelectorAll('.price-preset').forEach(b=>b.classList.remove('active')); });
  });

  // "Load more" button — delegated, so it survives innerHTML replacement
  const section=document.getElementById('products-section');
  if(section){
    section.addEventListener('click',e=>{
      if(e.target.closest('#load-more-btn')) loadMore();
    });
  }
  watchLoadMore();
})();
