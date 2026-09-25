/* Product card behaviour: Quick View, Compare and Wishlist.
   Loaded once globally from base.html — every card on the site uses it.
   URLs come from #pc-config (rendered by products/partials/product_card_scripts.html)
   instead of being hardcoded, so they survive changes to products/urls.py. */
const _pcCfg = document.getElementById('pc-config');
const PC_URLS = {
  quickView: _pcCfg.dataset.quickViewUrl,
  wishlist:  _pcCfg.dataset.wishlistUrl,
  compare:   _pcCfg.dataset.compareUrl,
};
const PC_UUID = '00000000-0000-0000-0000-000000000000';

// ════════════════════════════════════════════════════════════════════
//  SHARED PRODUCT-CARD BEHAVIOUR  (Quick View · Compare · Wishlist)
//  Loaded once globally — every product card on the site uses this.
// ════════════════════════════════════════════════════════════════════

// ── Toast ───────────────────────────────────────────────────────────
function showToast(msg, type='info'){
  // Look lives in .pc-toast / .pc-toast--{type} (product-card.css), built on tokens.
  const icons ={success:'ti-circle-check',error:'ti-circle-x',warning:'ti-alert-triangle',info:'ti-info-circle'};
  if(!icons[type]) type='info';
  const t=document.createElement('div');
  t.className=`pc-toast pc-toast--${type} pc-fade-in`;
  t.setAttribute('role','status');
  t.innerHTML=`<i class="ti ${icons[type]}"></i><span>${msg}</span>`;
  document.body.appendChild(t);
  setTimeout(()=>{t.style.opacity='0';t.style.transition='opacity .3s';setTimeout(()=>t.remove(),300);},3500);
}

// ── Quick View ──────────────────────────────────────────────────────
async function openQV(slug){
  const modal=document.getElementById('qv-modal');
  const content=document.getElementById('qv-content');
  if(!modal||!content)return;
  modal.classList.add('open');
  document.body.style.overflow='hidden';
  content.innerHTML='<div class="flex items-center justify-center h-48"><div class="pc-spinner" role="status" aria-label="Loading"></div></div>';
  try{
    const res=await fetch(PC_URLS.quickView.replace('__SLUG__', slug),{headers:{'X-Requested-With':'XMLHttpRequest'}});
    content.innerHTML=await res.text();
  }catch{content.innerHTML='<p class="text-center text-muted py-12">Could not load product details.</p>';}
}
function closeQV(){
  const modal=document.getElementById('qv-modal');
  if(!modal)return;
  modal.classList.remove('open');
  document.body.style.overflow='';
}
// Alias called by the product card markup.
function openQuickView(slug){openQV(slug);}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeQV();});

// ── Compare ─────────────────────────────────────────────────────────
let compareItems=JSON.parse(localStorage.getItem('tzCompare')||'[]');

function updateCompareUI(){
  const bar=document.getElementById('compare-bar');
  const countEl=document.getElementById('cmp-count');
  const goBtn=document.getElementById('cmp-go-btn');

  if(countEl) countEl.textContent=`${compareItems.length}/3`;
  if(goBtn){
    // .btn:disabled supplies the dimmed / not-allowed look — no class swap needed.
    goBtn.disabled=compareItems.length<2;
    goBtn.className='btn btn-primary cmp-bar-btn';
  }

  document.querySelectorAll('.cmp-slot').forEach((slot,i)=>{
    const nameEl=slot.querySelector('.cmp-name');
    if(compareItems[i]){
      // Slot look lives in #compare-bar .cmp-slot(.is-filled) — product-card.css.
      slot.classList.add('is-filled');
      nameEl.textContent=compareItems[i].name;
      let rmBtn=slot.querySelector('.cmp-rm');
      if(!rmBtn){
        rmBtn=document.createElement('button');
        rmBtn.type='button';
        rmBtn.className='cmp-rm';
        rmBtn.setAttribute('aria-label','Remove from compare');
        rmBtn.innerHTML='<i class="ti ti-x" aria-hidden="true"></i>';
        slot.appendChild(rmBtn);
      }
      const itemId=compareItems[i].id;
      rmBtn.onclick=()=>toggleCompare(itemId,'');
    } else {
      slot.classList.remove('is-filled');
      nameEl.textContent='Empty slot';
      const rmBtn=slot.querySelector('.cmp-rm');
      if(rmBtn) rmBtn.remove();
    }
  });

  if(bar){
    if(compareItems.length>0) bar.classList.add('show');
    else bar.classList.remove('show');
  }

  // Reflect state on every compare button currently in the DOM. One semantic
  // class — .pc-act-cmp.is-active carries the light and dark styling.
  document.querySelectorAll('.compare-btn').forEach(btn=>{
    const active=compareItems.some(p=>p.id===btn.dataset.id);
    btn.classList.toggle('is-active',active);
    btn.setAttribute('aria-pressed',active ? 'true' : 'false');
    const label=active ? 'Remove from compare' : 'Add to compare';
    btn.setAttribute('aria-label',label);
    // Card buttons show aria-label as a styled tooltip; others keep a plain title.
    if(!btn.classList.contains('pc-act')) btn.title=label;
  });
}

function toggleCompare(id,name){
  const idx=compareItems.findIndex(p=>p.id===id);
  if(idx>-1){
    compareItems.splice(idx,1);
    showToast('Removed from compare','info');
  } else {
    if(compareItems.length>=3){showToast('Max 3 products for comparison','warning');return;}
    compareItems.push({id,name});
    showToast('Added to compare','success');
  }
  localStorage.setItem('tzCompare',JSON.stringify(compareItems));
  updateCompareUI();
}

function clearCompare(){
  compareItems=[];
  localStorage.setItem('tzCompare','[]');
  updateCompareUI();
  showToast('Compare list cleared','info');
}

function goCompare(){
  if(compareItems.length<2){showToast('Select at least 2 products','warning');return;}
  window.location.href=PC_URLS.compare + '?'+compareItems.map(p=>'ids='+p.id).join('&');
}

updateCompareUI();

// ── Wishlist (event-delegated so it works for cards added later) ─────
document.addEventListener('click',async e=>{
  const btn=e.target.closest('.wishlist-btn');
  if(!btn)return; e.preventDefault();
  const pid=btn.dataset.product;
  try{
    const res=await fetch(PC_URLS.wishlist.replace(PC_UUID, pid),{
      method:'POST',
      headers:{'X-CSRFToken':(window.csrfToken||''),'X-Requested-With':'XMLHttpRequest'}
    });
    if(res.redirected||res.status===302||res.url.includes('login')){
      showToast('Sign in to save wishlist items','info'); return;
    }
    const data=await res.json();
    const icon=btn.querySelector('i');
    if(data.status==='added'){
      icon.className='ti ti-heart-filled';   // coloured by .pc-wish .ti-heart-filled
      btn.setAttribute('aria-label','Remove from wishlist');
      showToast('Added to wishlist ❤️','success');
    } else {
      icon.className='ti ti-heart';
      btn.setAttribute('aria-label','Add to wishlist');
      showToast('Removed from wishlist','info');
    }
  }catch{showToast('Something went wrong','error');}
});

// Expose the compare bar's height (it wraps to 3 rows on phones) so the floating
// WhatsApp button can sit above it — see .wa-fab in product-card.css.
(function(){
  const bar=document.getElementById('compare-bar');
  if(!bar||!('ResizeObserver' in window)) return;
  new ResizeObserver(()=>document.documentElement.style.setProperty('--cmp-bar-h',bar.offsetHeight+'px')).observe(bar);
})();
