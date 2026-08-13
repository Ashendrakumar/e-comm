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
  const colors={success:'bg-green-500',error:'bg-red-500',warning:'bg-orange-500',info:'bg-primary-600'};
  const icons ={success:'ti-circle-check',error:'ti-circle-x',warning:'ti-alert-triangle',info:'ti-info-circle'};
  const t=document.createElement('div');
  t.className=`fixed top-20 right-4 z-[9999] ${colors[type]||colors.info} text-white px-5 py-3 rounded-2xl shadow-2xl text-sm font-semibold pc-fade-in flex items-center gap-2 max-w-xs`;
  t.innerHTML=`<i class="ti ${icons[type]||icons.info} text-base flex-shrink-0"></i><span>${msg}</span>`;
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
  content.innerHTML='<div class="flex items-center justify-center h-48"><div class="w-10 h-10 border-4 border-primary-600 border-t-transparent rounded-full animate-spin"></div></div>';
  try{
    const res=await fetch(PC_URLS.quickView.replace('__SLUG__', slug),{headers:{'X-Requested-With':'XMLHttpRequest'}});
    content.innerHTML=await res.text();
  }catch{content.innerHTML='<p class="text-center text-gray-500 py-12">Could not load product details.</p>';}
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

  if(countEl) countEl.textContent=`(${compareItems.length}/3)`;
  if(goBtn){
    goBtn.disabled=compareItems.length<2;
    goBtn.className=compareItems.length>=2
      ?'btn-primary text-sm py-2 px-5 rounded-xl'
      :'btn-primary text-sm py-2 px-5 rounded-xl opacity-50 cursor-not-allowed';
  }

  document.querySelectorAll('.cmp-slot').forEach((slot,i)=>{
    const nameEl=slot.querySelector('.cmp-name');
    if(compareItems[i]){
      slot.className='cmp-slot flex items-center justify-between gap-2 px-3 py-2 bg-primary-50 dark:bg-primary-950 rounded-xl text-sm border-2 border-primary-300 dark:border-primary-700 min-w-[120px] h-10';
      nameEl.className='cmp-name text-xs font-semibold text-primary-700 dark:text-primary-300 truncate flex-1';
      nameEl.textContent=compareItems[i].name;
      let rmBtn=slot.querySelector('.cmp-rm');
      if(!rmBtn){
        rmBtn=document.createElement('button');
        rmBtn.className='cmp-rm flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full bg-primary-200 dark:bg-primary-800 hover:bg-red-200 dark:hover:bg-red-800 transition-colors';
        rmBtn.innerHTML='<i class="ti ti-x text-[10px] text-primary-600 dark:text-primary-400"></i>';
        slot.appendChild(rmBtn);
      }
      const itemId=compareItems[i].id;
      rmBtn.onclick=()=>toggleCompare(itemId,'');
    } else {
      slot.className='cmp-slot flex items-center justify-between gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800 rounded-xl text-sm text-gray-400 border-2 border-dashed border-gray-200 dark:border-gray-700 min-w-[120px] h-10';
      nameEl.className='cmp-name text-xs truncate';
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
    btn.title=active ? 'Remove from compare' : 'Add to compare';
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
      icon.className='ti ti-heart-filled text-red-500 text-sm';
      showToast('Added to wishlist ❤️','success');
    } else {
      icon.className='ti ti-heart text-sm';
      showToast('Removed from wishlist','info');
    }
  }catch{showToast('Something went wrong','error');}
});
