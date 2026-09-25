/* Header: slide-in mobile menu.
   Defines the canonical toggleMobileMenu() — base.js used to declare a stale
   `classList.toggle("hidden")` version that loaded later and silently won,
   which is why the slide-in never animated. That duplicate is now removed.
   Colours live in the header's token-based styles (.m-panel / .m-backdrop);
   this only flips the Tailwind transform/opacity/pointer-events state. */
function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  const panel = document.getElementById('mobile-menu-panel');
  const backdrop = document.getElementById('mobile-menu-backdrop');
  const toggle = document.getElementById('mobile-menu-toggle');
  const isOpen = menu.classList.contains('pointer-events-auto');

  if (isOpen) {
    panel.classList.add('-translate-x-full');
    backdrop.classList.add('opacity-0');
    backdrop.classList.remove('opacity-100');
    menu.classList.remove('pointer-events-auto');
    setTimeout(() => menu.classList.add('pointer-events-none'), 200);
    document.body.style.overflow = '';
  } else {
    menu.classList.remove('pointer-events-none');
    menu.classList.add('pointer-events-auto');
    // Force reflow so the transition triggers
    void panel.offsetWidth;
    panel.classList.remove('-translate-x-full');
    backdrop.classList.remove('opacity-0');
    backdrop.classList.add('opacity-100');
    document.body.style.overflow = 'hidden';
  }
  if (toggle) toggle.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
}

// Escape closes the drawer.
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  const menu = document.getElementById('mobile-menu');
  if (menu && menu.classList.contains('pointer-events-auto')) toggleMobileMenu();
});

// Publish the live heights of the sticky header (and a page's sticky sub-bar, e.g.
// the category sub-category pills) as CSS variables, so anything that sticks
// below them (.lp-sticky sidebars, .lp-subnav) uses real numbers at every width
// instead of guessed pixel offsets.
(function(){
  const root = document.documentElement;
  const header = document.getElementById('main-header');
  if (!header || !('ResizeObserver' in window)) return;
  let subnav = null;           // lives in page content, parsed after this script runs
  const sync = () => {
    root.style.setProperty('--header-h', header.offsetHeight + 'px');
    root.style.setProperty('--subnav-h', (subnav ? subnav.offsetHeight : 0) + 'px');
  };
  const ro = new ResizeObserver(sync);
  ro.observe(header);
  sync();
  const findSubnav = () => {
    subnav = document.querySelector('[data-sticky-subnav]');
    if (subnav) ro.observe(subnav);
    sync();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', findSubnav);
  else findSubnav();
})();
