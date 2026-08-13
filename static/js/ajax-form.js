/* Generic AJAX form submit.
 *
 * Replaces four near-identical inline handlers (homepage contact, contact page,
 * service enquiry, area enquiry). Opt a form in with `data-ajax-form`:
 *
 *   <form action="..." data-ajax-form
 *         data-msg-target="#contact-msg"        (element to write the result into)
 *         data-ajax-url="..."                   (optional; defaults to form.action)
 *         data-error-text="..."                 (optional validation-failure text)
 *         data-msg-ok-class="..."               (optional success classes)
 *         data-msg-err-class="..."              (optional failure classes)
 *         data-loading-text="...">              (optional button HTML while sending)
 *
 * The submit button's original innerHTML is captured and restored, so the label
 * never has to be duplicated in JS.
 *
 * Delegated from document, so it also covers forms injected after page load.
 */
document.addEventListener('submit', async function (e) {
  const form = e.target.closest('form[data-ajax-form]');
  if (!form) return;
  e.preventDefault();

  const d       = form.dataset;
  const btn     = form.querySelector('[type=submit]');
  const msg     = d.msgTarget ? document.querySelector(d.msgTarget) : null;
  const okClass  = d.msgOkClass  || 'text-sm text-center text-green-600 font-medium';
  const errClass = d.msgErrClass || 'text-sm text-center text-red-500';
  const restore = btn ? btn.innerHTML : '';

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = d.loadingText || '<i class="ti ti-loader-2 animate-spin"></i> Sending...';
  }

  const show = (cls, text) => {
    if (!msg) return;
    msg.classList.remove('hidden');
    msg.className = cls;
    msg.textContent = text;
  };

  try {
    const res = await fetch(d.ajaxUrl || form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': window.csrfToken },
    });
    const data = await res.json();
    if (data.success) {
      form.reset();
      show(okClass, data.message);
    } else {
      show(errClass, d.errorText || 'Please check the form and try again.');
    }
  } catch (err) {
    show(errClass, 'Something went wrong. Please try again.');
  }

  if (btn) {
    btn.disabled = false;
    btn.innerHTML = restore;
  }
});
