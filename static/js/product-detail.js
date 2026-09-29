/* Product detail page: gallery, variant picker, tabs, review + enquiry
   submission, "helpful" voting and wishlist.
   Endpoints come from #pd-config (rendered by products/detail.html) so no
   URL is hardcoded or template-interpolated here. */
const PD = document.getElementById('pd-config');
const PD_UUID = '00000000-0000-0000-0000-000000000000';

const CSRF = document.cookie.split(';').reduce((a,c)=>{const[k,v]=c.trim().split('=');return k==='csrftoken'?decodeURIComponent(v):a;},'');

// ── Gallery Swiper ─────────────────────────────────────────
const mainSwiper = new Swiper('.main-gallery-swiper', {
  spaceBetween: 0,
  navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
  pagination: { el: '.swiper-pagination', clickable: true },
  keyboard: { enabled: true },
});

// Thumbnails (.pd-thumb) pick the slide; the active one follows swipes / arrows too.
const pdThumbs = [...document.querySelectorAll('.pd-thumb')];
function markThumb(i){
  pdThumbs.forEach((t, n) => {
    const on = n === i;
    t.classList.toggle('is-active', on);
    if (on) { t.setAttribute('aria-current', 'true'); t.scrollIntoView({block: 'nearest', inline: 'nearest'}); }
    else t.removeAttribute('aria-current');
  });
}
pdThumbs.forEach(t => t.addEventListener('click', () => mainSwiper.slideTo(+t.dataset.index)));
mainSwiper.on?.('slideChange', () => markThumb(mainSwiper.activeIndex));

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
  });
});

// ── Review form submit ─────────────────────────────────────
// Fields (incl. the star rating) are checked first by form-validate.js.
document.getElementById('review-form')?.addEventListener('submit', async e=>{
  e.preventDefault();
  const form = e.target;
  const msgEl  = document.getElementById('review-msg');
  const btn    = document.getElementById('review-submit-btn');
  btn.disabled = true;
  btn.innerHTML = '<i class="ti ti-loader animate-spin"></i> Submitting…';

  try{
    const res  = await fetch(PD.dataset.reviewUrl, {
      method:'POST', body: new FormData(form),
      headers:{'X-Requested-With':'XMLHttpRequest','X-CSRFToken':CSRF}
    });
    const data = await res.json();
    msgEl.classList.remove('hidden');
    if(data.success){
      msgEl.className = 'pd-msg is-success';
      msgEl.textContent = data.message;
      form.reset();
      document.getElementById('rating-input').value = '';
    } else {
      msgEl.className = 'pd-msg is-error';
      const extra = window.FormValidate ? FormValidate.showErrors(form, data.errors) : [];
      msgEl.textContent = [data.message || 'Please fix the errors above.', ...extra].join(' ');
    }
  }catch{
    msgEl.className = 'pd-msg is-error';
    msgEl.textContent = 'Something went wrong. Please try again.';
  }
  btn.disabled = false;
  btn.innerHTML = '<i class="ti ti-send"></i> Submit Review';
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
    btn.classList.add('is-voted');   // styled in product-detail.css
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
  btn.innerHTML = '<i class="ti ti-loader animate-spin"></i> Sending…';
  try{
    const res  = await fetch(PD.dataset.inquiryUrl, {
      method:'POST', body: new FormData(form),
      headers:{'X-Requested-With':'XMLHttpRequest','X-CSRFToken':CSRF}
    });
    const data = await res.json();
    msgEl.classList.remove('hidden');
    if(data.success){
      msgEl.className = 'pd-msg is-success';
      msgEl.innerHTML = '<i class="ti ti-circle-check mr-1"></i>' + data.message;
      form.reset();
      setTimeout(()=>closeInquiryModal(), 3000);
    } else {
      msgEl.className = 'pd-msg is-error';
      const extra = window.FormValidate ? FormValidate.showErrors(form, data.errors) : [];
      msgEl.textContent = [data.message || 'Please fix the errors above.', ...extra].join(' ');
    }
  }catch{
    msgEl.className = 'pd-msg is-error';
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
    icon.className  = 'ti ti-check pd-success';
    toast.classList.remove('hidden');
    setTimeout(()=>{ icon.className='ti ti-link'; toast.classList.add('hidden'); }, 2500);
  });
}

// ── Wishlist ───────────────────────────────────────────────
// Stored in the browser by the shared toggleWishlist() in product-card.js,
// which also restyles this button (.pd-wishlist.is-active) and the header count.
function toggleWishlistBtn(btn){ toggleWishlist(btn.dataset.product); }

// Compare (toggleCompare / compare bar) and showToast() are provided globally by
// products/partials/product_card_scripts.html — the compare button on this page
// (.compare-btn[data-id]) is styled by the shared updateCompareUI() automatically.
