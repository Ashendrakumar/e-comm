/* Header: slide-in mobile menu.
   Defines the canonical toggleMobileMenu() — base.js used to declare a stale
   `classList.toggle("hidden")` version that loaded later and silently won,
   which is why the slide-in never animated. That duplicate is now removed. */
  // Slide-in mobile menu animation
  function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  const panel = document.getElementById('mobile-menu-panel');
  const backdrop = document.getElementById('mobile-menu-backdrop');
  const isOpen = menu.classList.contains('pointer-events-auto');

  if (isOpen) {
    panel.classList.add('-translate-x-full');
    backdrop.classList.add('opacity-0');
    backdrop.classList.remove('opacity-100');
    menu.classList.remove('pointer-events-auto');
    setTimeout(() => menu.classList.add('pointer-events-none'), 200);
  } else {
    menu.classList.remove('pointer-events-none');
    menu.classList.add('pointer-events-auto');
    // Force reflow so the transition triggers
    void panel.offsetWidth;
    panel.classList.remove('-translate-x-full');
    backdrop.classList.remove('opacity-0');
    backdrop.classList.add('opacity-100');
  }
}
