// Forms: send to the form service in the background, say clearly what happened, never fail silently.
// Works with any service that accepts a normal form post and answers JSON (for example Formspree).
(function () {
  document.querySelectorAll('form[data-pta-form]').forEach(form => {
    const status = form.querySelector('.form-status');
    const button = form.querySelector('button[type="submit"]');
    const mail = form.dataset.mailto || '';
    const noEmail = mail ? ' You can also email us at ' + mail + '.' : '';
    let sending = false;

    function say(text, kind) {
      status.textContent = text;
      status.className = 'form-status ' + kind;
      status.setAttribute('role', kind === 'error' ? 'alert' : 'status');
    }

    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (sending) return;
      if (!form.checkValidity()) { form.reportValidity(); return; }
      const trap = form.querySelector('[name="_gotcha"]');
      if (trap && trap.value) { say(form.dataset.success, 'ok'); form.reset(); return; }   // a bot filled the hidden field
      const endpoint = form.dataset.endpoint || '';
      if (!endpoint) { say('This form is not connected yet, so nothing was sent.' + noEmail, 'error'); return; }
      sending = true;
      const label = button.textContent;
      button.disabled = true; button.textContent = 'Sending...'; say('Sending...', 'info');
      const stop = new AbortController();
      const timer = setTimeout(() => stop.abort(), 20000);
      try {
        const res = await fetch(endpoint, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' }, signal: stop.signal });
        if (res.ok) {
          say(form.dataset.success || 'Thank you! We got it.', 'ok');
          form.reset();
        } else {
          let why = '';
          try { const j = await res.json(); why = (j.errors && j.errors.map(e => e.message).join(' ')) || j.error || ''; } catch (_) { /* no details */ }
          say('Sorry, that did not send' + (why ? ' (' + why + ')' : '') + '. Please try again.' + noEmail, 'error');
        }
      } catch (_) {
        say('Sorry, we could not reach the form service. Please check your connection and try again.' + noEmail, 'error');
      } finally {
        clearTimeout(timer);
        sending = false; button.disabled = false; button.textContent = label;
      }
    });
  });
})();
