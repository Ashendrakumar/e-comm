/* Client-side validation for every form marked `data-validate`.
 *
 * Checks the rules already in the markup (required, type=email, minlength,
 * maxlength) plus two the browser does not: required text that is only
 * spaces, and phone numbers (type=tel: 7-15 digits, as core/validators.py).
 * Errors are shown inline under each field (.field-error, aria-invalid,
 * aria-describedby) instead of the browser's bubbles; the first invalid field
 * gets focus.
 *
 * It listens for `submit` on document in the capture phase, so an invalid form
 * is stopped before ajax-form.js or a page's own submit handler sees it.
 * Without JS the browser's native validation still applies.
 *
 * Error slot: `[data-error-for~="<name>"]` inside the form if present (e.g. the
 * star rating), otherwise a <p class="field-error"> added after the control.
 *
 * Server errors (Django `form.errors` JSON) go through
 *   FormValidate.showErrors(form, errors)  -> returns messages it could not place.
 */
(function () {
  const SKIP_TYPES = new Set(['hidden', 'submit', 'button', 'reset', 'image', 'file']);
  const HONEYPOT   = 'hp_website';

  function controls(form) {
    const seen = new Set();
    return [...form.elements].filter(el => {
      if (!el.name || el.disabled || SKIP_TYPES.has(el.type) || el.name === HONEYPOT) return false;
      if (el.type === 'radio') {                    // one entry per radio group
        if (seen.has(el.name)) return false;
        seen.add(el.name);
      }
      return true;
    });
  }

  function labelFor(el) {
    const label = el.id && el.form.querySelector(`label[for="${CSS.escape(el.id)}"]`);
    const text  = (label && label.textContent) || el.getAttribute('aria-label') || el.placeholder || 'this field';
    return text.replace(/\*|\(optional\)/gi, '').trim().replace(/^your\s+/i, '').toLowerCase();
  }

  function phoneOk(value) {
    const digits = (value.match(/\d/g) || []).length;
    return /^\+?[\d\s().-]+$/.test(value) && digits >= 7 && digits <= 15;
  }

  /** The error message for one control, or '' when it is valid. */
  function check(el) {
    if (el.type === 'radio') {
      const group = el.form.querySelectorAll(`input[type=radio][name="${CSS.escape(el.name)}"]`);
      const required = [...group].some(r => r.required);
      return required && ![...group].some(r => r.checked) ? (el.dataset.msgRequired || 'Please choose an option.') : '';
    }
    const value = el.value.trim();
    const min   = +el.getAttribute('minlength') || 0;
    const max   = +el.getAttribute('maxlength') || 0;

    if (!value) return el.required ? (el.dataset.msgRequired || `Please enter your ${labelFor(el)}.`) : '';
    if (el.type === 'email' && (el.validity.typeMismatch || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value)))
      return 'Enter a valid email address, like name@example.com.';
    if (el.type === 'tel' && !phoneOk(value))
      return 'Enter a valid phone number, e.g. +91 98765 43210.';
    if (min && value.length < min)
      return `Please enter at least ${min} characters (you have ${value.length}).`;
    if (max && value.length > max)
      return `Please keep this under ${max} characters (you have ${value.length}).`;
    if (el.tagName === 'SELECT' && el.required && !el.value) return 'Please choose an option.';
    return '';
  }

  function slotFor(el) {
    const form = el.form;
    let slot = form.querySelector(`[data-error-for~="${CSS.escape(el.name)}"]`);
    if (slot) return slot;
    const id = `${el.id || `${form.id || 'f'}-${el.name}`}-error`;
    slot = document.getElementById(id);
    if (!slot) {
      slot = document.createElement('p');
      slot.id = id;
      slot.className = 'field-error hidden';
      el.insertAdjacentElement('afterend', slot);
    }
    return slot;
  }

  function targets(el) {
    return el.type === 'radio'
      ? [...el.form.querySelectorAll(`input[type=radio][name="${CSS.escape(el.name)}"]`)]
      : [el];
  }

  function setError(el, message) {
    const slot = slotFor(el);
    if (!slot.id) slot.id = `${el.form.id || 'f'}-${el.name}-error`;
    slot.textContent = message;
    slot.classList.toggle('hidden', !message);
    targets(el).forEach(t => {
      const ids = (t.getAttribute('aria-describedby') || '').split(/\s+/).filter(i => i && i !== slot.id);
      if (message) {
        t.setAttribute('aria-invalid', 'true');
        ids.push(slot.id);
      } else {
        t.removeAttribute('aria-invalid');
      }
      ids.length ? t.setAttribute('aria-describedby', ids.join(' ')) : t.removeAttribute('aria-describedby');
    });
  }

  function validateField(el) {
    const message = check(el);
    setError(el, message);
    return !message;
  }

  function validate(form) {
    let first = null;
    controls(form).forEach(el => {
      if (!validateField(el) && !first) first = el;
    });
    if (first) {
      first.focus({ preventScroll: true });
      first.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
    return !first;
  }

  function clear(form) {
    controls(form).forEach(el => setError(el, ''));
  }

  /** Show Django form.errors ({field: [messages]}); returns the ones with no matching field. */
  function showErrors(form, errors) {
    const leftover = [];
    let first = null;
    Object.entries(errors || {}).forEach(([name, list]) => {
      const message = [].concat(list).map(m => (typeof m === 'string' ? m : m.message)).join(' ');
      const el = form.elements[name] instanceof RadioNodeList ? form.elements[name][0] : form.elements[name];
      const slot = form.querySelector(`[data-error-for~="${CSS.escape(name)}"]`);
      if (el && el.type !== 'hidden') {
        setError(el, message);
        first = first || el;
      } else if (slot) {
        slot.textContent = message;
        slot.classList.remove('hidden');
      } else {
        leftover.push(message);
      }
    });
    if (first) first.focus();
    return leftover;
  }

  // Stop invalid submits before any other submit handler runs.
  document.addEventListener('submit', e => {
    const form = e.target;
    if (!form.matches('form[data-validate]')) return;
    form.dataset.submitted = '1';
    if (!validate(form)) {
      e.preventDefault();
      e.stopImmediatePropagation();
    }
  }, true);

  // Validate a field once the user leaves it (if they typed something), then
  // re-check it live while it shows an error, so the message clears as it is fixed.
  document.addEventListener('focusout', e => {
    const el = e.target;
    if (!el.form || !el.form.matches('form[data-validate]') || !el.name || SKIP_TYPES.has(el.type)) return;
    if (el.value.trim() || el.form.dataset.submitted) validateField(el);
  });
  ['input', 'change'].forEach(type => document.addEventListener(type, e => {
    const el = e.target;
    if (!el.form || !el.form.matches('form[data-validate]') || !el.name) return;
    if (el.getAttribute('aria-invalid') === 'true' || el.type === 'radio') validateField(el);
  }));

  // Our messages replace the browser's bubbles (only once this script has loaded).
  document.querySelectorAll('form[data-validate]').forEach(f => { f.noValidate = true; });
  document.addEventListener('reset', e => {
    if (e.target.matches('form[data-validate]')) { clear(e.target); delete e.target.dataset.submitted; }
  }, true);

  window.FormValidate = { validate, clear, showErrors };
})();
