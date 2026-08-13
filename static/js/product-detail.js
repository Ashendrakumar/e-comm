/* Product detail page: gallery, variant picker, tabs, review + enquiry
   submission, "helpful" voting and wishlist.
   Endpoints come from #pd-config (rendered by products/detail.html) so no
   URL is hardcoded or template-interpolated here. */
const PD = document.getElementById('pd-config');
const PD_UUID = '00000000-0000-0000-0000-000000000000';

const CSRF = document.cookie.split(';').reduce((a,c)=>{const[k,v]=c.trim().split('=');return k==='csrftoken'?decodeURIComponent(v):a;},'');

// ── Gallery Swiper ─────────────────────────────────────────
const thumbSwiper = new Swiper('.gallery-thumb-swiper', {
  spaceBetween: 8,
  slidesPerView: 'auto',
  freeMode: true,
  watchSlidesProgress: true,
});
const mainSwiper = new Swiper('.main-gallery-swiper', {
  spaceBetween: 0,
  navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
  pagination: { el: '.swiper-pagination', clickable: true },
  thumbs: { swiper: thumbSwiper },
  keyboard: { enabled: true },
});

// ── Zoom overlay ───────────────────────────────────────────
function openZoom(src){
  document.getElementById('zoom-img').src = src;
  document.getElementById('zoom-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeZoom(){
  document.getElementById('zoom-overlay').classList.remove('open');
  document.body.style.overflow = '';
}
document.addEventListener('keydown', e => { if(e.key==='Escape'){ closeZoom(); closeInquiryModal(); }});

// ── Tab switcher ───────────────────────────────────────────
function switchTab(id, btn){
  ['desc','specs','reviews','faqs'].forEach(t=>{
    const el = document.getElementById('tab-'+t);
    if(el) el.classList.add('hidden');
  });
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  const panel = document.getElementById('tab-'+id);
  if(panel) panel.classList.remove('hidden');
  if(btn) btn.classList.add('active');
  else {
    const btns = document.querySelectorAll('.tab-btn');
    const map  = {desc:0,specs:1,reviews:2,faqs:3};
    if(btns[map[id]]) btns[map[id]].classList.add('active');
  }
}
// Init first tab
document.addEventListener('DOMContentLoaded',()=>{
  const firstBtn = document.querySelector('.tab-btn');
  if(firstBtn) firstBtn.click();
});
// Allow linking to #reviews or #specs
if(window.location.hash === '#reviews') setTimeout(()=>switchTab('reviews',null),200);
if(window.location.hash === '#specs')   setTimeout(()=>switchTab('specs',null),200);

// ── Star rating input ──────────────────────────────────────
document.querySelectorAll('#star-picker input[type=radio]').forEach(input=>{
  input.addEventListener('change',()=>{
    document.getElementById('rating-input').value = input.value;
    document.getElementById('rating-error').classList.add('hidden');
  });
});

// ── Review form submit ─────────────────────────────────────
document.getElementById('review-form')?.addEventListener('submit', async e=>{
  e.preventDefault();
  const form = e.target;
  const rating = document.getElementById('rating-input').value;
  const msgEl  = document.getElementById('review-msg');
  const btn    = document.getElementById('review-submit-btn');

  if(!rating){
    document.getElementById('rating-error').classList.remove('hidden');
    return;
  }
  btn.disabled = true;
  btn.innerHTML = '<i class="ti ti-loader animate-spin text-sm"></i> Submitting…';

  try{
    const res  = await fetch(PD.dataset.reviewUrl, {
      method:'POST', body: new FormData(form),
      headers:{'X-Requested-With':'XMLHttpRequest','X-CSRFToken':CSRF}
    });
    const data = await res.json();
    msgEl.classList.remove('hidden');
    if(data.success){
      msgEl.className = 'text-sm font-semibold p-3 rounded-xl text-center bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800';
      msgEl.textContent = data.message;
      form.reset();
      document.getElementById('rating-input').value = '';
    } else {
      msgEl.className = 'text-sm font-semibold p-3 rounded-xl text-center bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800';
      msgEl.textContent = data.message || 'Please fix the errors above.';
    }
  }catch{
    msgEl.classList.remove('hidden');
    msgEl.textContent = 'Something went wrong. Please try again.';
  }
  btn.disabled = false;
  btn.innerHTML = '<i class="ti ti-send text-sm"></i> Submit Review';
});

// ── Mark helpful ───────────────────────────────────────────
async function markHelpful(reviewId, btn){
  try{
    const res  = await fetch(PD.dataset.helpfulUrl.replace('999999999', reviewId), {
      method:'POST', headers:{'X-CSRFToken':CSRF,'X-Requested-With':'XMLHttpRequest'}
    });
    const data = await res.json();
    const el   = document.querySelector(`.helpful-count-${reviewId}`);
    if(el) el.textContent = data.helpful_count;
    btn.disabled = true;
    btn.classList.add('bg-primary-50','dark:bg-primary-950','text-primary-700');
  }catch{}
}

// ── Inquiry modal ──────────────────────────────────────────
function openInquiryModal(){
  document.getElementById('inquiry-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}
function closeInquiryModal(){
  document.getElementById('inquiry-modal').classList.add('hidden');
  document.body.style.overflow = '';
}
document.getElementById('inquiry-form')?.addEventListener('submit', async e=>{
  e.preventDefault();
  const form = e.target;
  const msgEl = document.getElementById('inquiry-msg');
  const btn   = document.getElementById('inquiry-submit-btn');
  btn.disabled = true;
  btn.innerHTML = '<i class="ti ti-loader animate-spin text-sm"></i> Sending…';
  try{
    const res  = await fetch(PD.dataset.inquiryUrl, {
      method:'POST', body: new FormData(form),
      headers:{'X-Requested-With':'XMLHttpRequest','X-CSRFToken':CSRF}
    });
    const data = await res.json();
    msgEl.classList.remove('hidden');
    if(data.success){
      msgEl.className = 'text-sm font-semibold p-3 rounded-xl text-center bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800';
      msgEl.innerHTML = '<i class="ti ti-circle-check mr-1"></i>' + data.message;
      form.reset();
      setTimeout(()=>closeInquiryModal(), 3000);
    } else {
      msgEl.className = 'text-sm font-semibold p-3 rounded-xl text-center bg-red-50 text-red-700 border border-red-200';
      msgEl.textContent = data.message;
    }
  }catch{
    msgEl.classList.remove('hidden');
    msgEl.textContent = 'Something went wrong. Please try again.';
  }
  btn.disabled = false;
  btn.innerHTML = '<i class="ti ti-send"></i> Send Enquiry';
});

// ── Share: copy link ───────────────────────────────────────
function copyLink(){
  navigator.clipboard.writeText(window.location.href).then(()=>{
    const icon  = document.getElementById('copy-icon');
    const toast = document.getElementById('copy-toast');
    icon.className  = 'ti ti-check text-green-500';
    toast.classList.remove('hidden');
    setTimeout(()=>{ icon.className='ti ti-link'; toast.classList.add('hidden'); }, 2500);
  });
}

// ── Wishlist ───────────────────────────────────────────────
async function toggleWishlistBtn(btn){
  const pid = btn.dataset.product;
  const icon= btn.querySelector('i');
  try{
    const res  = await fetch(PD.dataset.wishlistUrl.replace(PD_UUID, pid),{
      method:'POST', headers:{'X-CSRFToken':CSRF,'X-Requested-With':'XMLHttpRequest'}
    });
    if(res.redirected||res.status===302){ showToast('Sign in to save to wishlist','info'); return; }
    const data = await res.json();
    if(data.status==='added'){
      icon.className='ti ti-heart-filled text-red-500 text-xl';
      btn.classList.add('border-red-400','bg-red-50','dark:bg-red-950');
      showToast('Added to wishlist ❤️','success');
    } else {
      icon.className='ti ti-heart text-xl';
      btn.classList.remove('border-red-400','bg-red-50','dark:bg-red-950');
      showToast('Removed from wishlist','info');
    }
  }catch{ showToast('Something went wrong','error'); }
}

// Compare (toggleCompare / compare bar) and showToast() are provided globally by
// products/partials/product_card_scripts.html — the compare button on this page
// (.compare-btn[data-id]) is styled by the shared updateCompareUI() automatically.
