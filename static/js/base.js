/* Site-wide behaviour: theme toggle, toasts, CSRF helper, mobile menu and
   the Swiper carousels.
   The INITIAL theme resolution deliberately stays inline in <head> (see
   base.html) — moving it here would cost a request before first paint and
   bring back the light->dark flash. */
// Theme — the initial resolution happens in a blocking inline script in <head>
// (see base.html) so there is no light→dark flash. This only handles changes.
function applyTheme(dark){
  const root=document.documentElement;
  root.classList.toggle('dark',dark);
  root.style.colorScheme=dark?'dark':'light';
}
function toggleDark(){
  const dark=!document.documentElement.classList.contains('dark');
  applyTheme(dark);
  try{ localStorage.setItem('theme',dark?'dark':'light'); }catch(e){}
}
// Follow the OS while the visitor has not made an explicit choice.
if(window.matchMedia){
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',e=>{
    let stored=null;
    try{ stored=localStorage.getItem('theme'); }catch(_){}
    if(!stored) applyTheme(e.matches);
  });
}
// Toasts auto-dismiss
setTimeout(()=>document.querySelectorAll('.toast-msg').forEach(e=>e.remove()),5000);
// CSRF helper
function getCookie(n){const v=document.cookie.split(';').find(c=>c.trim().startsWith(n+'='));return v?decodeURIComponent(v.trim().slice(n.length+1)):null}
const csrfToken=getCookie('csrftoken');
// Mobile menu: see static/js/header.js — it owns toggleMobileMenu() and
// matches the actual header markup (slide-in panel + backdrop).

// Hero swiper
if(document.querySelector('.hero-swiper')){
  new Swiper('.hero-swiper',{loop:true,autoplay:{delay:5000,disableOnInteraction:false},pagination:{el:'.swiper-pagination',clickable:true},navigation:{nextEl:'.swiper-button-next',prevEl:'.swiper-button-prev'},effect:'fade',fadeEffect:{crossFade:true}});
}
// Product swipers
document.querySelectorAll('.product-swiper').forEach(el=>{
  new Swiper(el,{slidesPerView:2,spaceBetween:16,navigation:{nextEl:el.querySelector('.swiper-button-next'),prevEl:el.querySelector('.swiper-button-prev')},breakpoints:{640:{slidesPerView:3},768:{slidesPerView:4},1024:{slidesPerView:5}}});
});
// Brand swiper
if(document.querySelector('.brand-swiper')){
  new Swiper('.brand-swiper',{slidesPerView:3,spaceBetween:16,autoplay:{delay:2500},loop:true,breakpoints:{480:{slidesPerView:4},768:{slidesPerView:6},1024:{slidesPerView:8}}});
}
// Expose CSRF token globally for shared product-card scripts.
window.csrfToken=csrfToken;
