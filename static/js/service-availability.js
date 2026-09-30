/* Service availability strip — filled from GET /api/v1/service-availability/.

   Markup (see templates/partials/service_availability.html):
     <section data-availability data-api="/api/v1/service-availability/?area=surat" data-layout="tiles|list">
       … heading …
       <div data-availability-list> skeleton placeholders </div>
     </section>

   Items are built with textContent (never innerHTML), and the icon class is
   whitelisted, so admin-entered text can't inject markup. If the request fails
   or returns nothing, the whole section is hidden rather than left half-empty. */
(function(){
  const ICON = /^ti-[a-z0-9-]+$/;

  function el(tag, cls, text){
    const n = document.createElement(tag);
    if(cls) n.className = cls;
    if(text) n.textContent = text;
    return n;
  }

  function render(item){
    const card = el('div', 'avail-item');
    const ico = el('span', 'avail-ico');
    ico.setAttribute('aria-hidden', 'true');
    ico.appendChild(el('i', 'ti ' + (ICON.test(item.icon || '') ? item.icon : 'ti-circle-check')));
    const body = el('div', 'avail-body');
    body.appendChild(el('p', 'avail-title', item.title));
    if(item.description) body.appendChild(el('p', 'avail-desc', item.description));
    card.append(ico, body);
    return card;
  }

  async function load(section){
    const list = section.querySelector('[data-availability-list]');
    try{
      const res = await fetch(section.dataset.api, {headers:{'Accept':'application/json'}});
      if(!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      const items = Array.isArray(data) ? data : (data.results || []);
      if(!items.length){ section.hidden = true; return; }
      list.replaceChildren(...items.map(render));
      list.setAttribute('aria-busy', 'false');
    }catch(err){
      console.warn('Service availability failed to load:', err);
      section.hidden = true;
    }
  }

  document.querySelectorAll('[data-availability]').forEach(load);
})();
