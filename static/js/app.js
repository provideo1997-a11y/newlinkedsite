(() => {
  'use strict';
  // The loader is visible only when JavaScript is available; no-JS users never get blocked.
  document.documentElement.classList.add('js');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const loader = document.getElementById('loader');
  const finishLoader = () => {
    if (!loader || loader.dataset.done === '1') return;
    loader.dataset.done = '1';
    loader.classList.add('is-hidden');
    window.setTimeout(() => loader.remove(), reduceMotion ? 0 : 850);
  };
  if (loader) {
    const bar = loader.querySelector('.loader-line i');
    if (bar && !reduceMotion) {
      let progress = 0;
      const tick = () => {
        progress = Math.min(94, progress + Math.max(1, (94 - progress) * 0.12));
        bar.style.width = `${progress}%`;
        const progressbar = bar.closest('[role=progressbar]');
        if (progressbar) progressbar.setAttribute('aria-valuenow', String(Math.round(progress)));
        if (progress < 94 && loader.dataset.done !== '1') requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }
    const ready = () => window.setTimeout(finishLoader, reduceMotion ? 0 : 550);
    if (document.readyState === 'complete') ready();
    else window.addEventListener('load', ready, { once: true });
    window.setTimeout(finishLoader, 3600);
  }

  const languageSelect = document.getElementById('language-select');
  if (languageSelect) languageSelect.addEventListener('change', () => {
    const url = new URL(window.location.href);
    url.searchParams.set('lang', languageSelect.value);
    window.location.assign(url.toString());
  });

  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.main-nav');
  const closeMenu = (returnFocus = false) => {
    if (!toggle || !nav) return;
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    if (returnFocus) toggle.focus();
  };
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
      if (open) {
        const firstLink = nav.querySelector('a');
        if (firstLink) firstLink.focus();
      }
    });
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && nav.classList.contains('is-open')) closeMenu(true); });
    document.addEventListener('click', event => {
      if (!nav.contains(event.target) && !toggle.contains(event.target)) closeMenu();
    });
  }

  const revealItems = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduceMotion) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); }
    }), { threshold: 0.10, rootMargin: '0px 0px -35px 0px' });
    revealItems.forEach(item => observer.observe(item));
  } else revealItems.forEach(item => item.classList.add('visible'));

  const progress = document.querySelector('.scroll-progress i');
  let scheduled = false;
  const updateProgress = () => {
    if (!progress) return;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    progress.style.width = `${max > 0 ? (window.scrollY / max) * 100 : 0}%`;
    scheduled = false;
  };
  window.addEventListener('scroll', () => {
    if (!scheduled) { scheduled = true; requestAnimationFrame(updateProgress); }
  }, { passive: true });
  updateProgress();

  const hero = document.querySelector('.hero');
  if (hero && !reduceMotion && window.matchMedia('(pointer:fine)').matches) {
    hero.addEventListener('pointermove', event => {
      const rect = hero.getBoundingClientRect();
      hero.style.setProperty('--mx', `${((event.clientX - rect.left) / rect.width) * 100}%`);
      hero.style.setProperty('--my', `${((event.clientY - rect.top) / rect.height) * 100}%`);
    }, { passive: true });
  }
})();
// Live character counter for the case description.
document.addEventListener('DOMContentLoaded',()=>{const field=document.getElementById('case-story');const count=document.getElementById('story-count');if(field&&count){const update=()=>{count.textContent=String(field.value.length);count.style.color=field.value.length>=25?'#c8ff3d':'#96a3a4'};field.addEventListener('input',update);update();}});


// Reliable single-button intake. The POST returns JSON only after the case is
// committed. The browser then navigates the current tab to the WhatsApp draft.
// A bounded client timeout and server-side idempotency make retry safe.
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('case-intake-form');
  if (!form) return;
  const submit = form.querySelector('button[type="submit"], input[type="submit"]');
  const status = document.getElementById('case-submit-status');
  if (!submit) return;

  const originalHTML = submit.innerHTML;
  const originalLabel = submit.getAttribute('aria-label');
  let activeController = null;
  let activeTimers = [];
  const clearTimers = () => { activeTimers.forEach(window.clearTimeout); activeTimers = []; };
  const setStatus = message => { if (status) status.textContent = message || ''; };
  const reset = message => {
    clearTimers();
    activeController = null;
    form.removeAttribute('aria-busy');
    delete form.dataset.submitting;
    submit.disabled = false;
    submit.classList.remove('is-submitting');
    submit.innerHTML = originalHTML;
    if (originalLabel) submit.setAttribute('aria-label', originalLabel);
    else submit.removeAttribute('aria-label');
    setStatus(message);
  };

  const sendRequest = () => fetch(form.action || window.location.pathname, {
    method: 'POST',
    body: new FormData(form),
    credentials: 'same-origin',
    cache: 'no-store',
    headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
    // The route must answer JSON for this same-origin POST. If a proxy or
    // framework returns a redirect, surface it instead of silently following it.
    redirect: 'error',
    signal: activeController.signal,
  });
  const readPayload = async response => {
    const contentType = response.headers.get('content-type') || '';
    const payload = contentType.toLowerCase().includes('application/json')
      ? await response.json().catch(() => null)
      : null;
    return { contentType, payload };
  };
  const applyRefreshedTokens = payload => {
    const csrfField = form.querySelector('input[name=csrf_token]');
    const caseField = form.querySelector('input[name=case_token]');
    const question = document.getElementById('human-question');
    const answer = document.getElementById('human_answer');
    if (csrfField && payload.csrf_token) csrfField.value = payload.csrf_token;
    if (caseField && payload.case_token) caseField.value = payload.case_token;
    if (question && payload.human_question) question.textContent = payload.human_question;
    if (!payload.retryable && answer) answer.value = '';
  };

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (form.dataset.submitting === '1') return;
    if (!form.reportValidity()) return;

    form.dataset.submitting = '1';
    form.setAttribute('aria-busy', 'true');
    submit.disabled = true;
    submit.classList.add('is-submitting');
    submit.setAttribute('aria-label', submit.dataset.submittingLabel || 'Sending to WhatsApp');
    setStatus(form.dataset.savingMessage || 'Saving your case securely…');

    const controller = new AbortController();
    activeController = controller;
    activeTimers.push(window.setTimeout(() => {
      if (form.dataset.submitting === '1') {
        setStatus(form.dataset.waitingMessage || 'The server is still processing your request.');
        submit.classList.remove('is-submitting');
      }
    }, 8000));
    activeTimers.push(window.setTimeout(() => {
      if (form.dataset.submitting === '1') setStatus(form.dataset.slowMessage || 'This is taking longer than expected.');
    }, 18000));
    // Render Free cold starts can be slow. The deadline is bounded; it never
    // forces a reload, and a retry uses the same signed case reference.
    activeTimers.push(window.setTimeout(() => controller.abort(), 120000));

    try {
      let response = await sendRequest();
      let parsed = await readPayload(response);
      let payload = parsed.payload;

      // Recover an expired/mismatched CSRF token without reloading the page.
      // Only retry once, and only while the same signed case token is valid.
      if (payload && payload.code === 'CSRF_TOKEN_REFRESHED') {
        applyRefreshedTokens(payload);
        if (!payload.retryable) {
          reset(payload.error || form.dataset.timeoutMessage || 'Your form session expired. Please solve the refreshed check and send again.');
          return;
        }
        setStatus(form.dataset.savingMessage || 'Refreshing the secure session…');
        response = await sendRequest();
        parsed = await readPayload(response);
        payload = parsed.payload;
        if (payload && payload.code === 'CSRF_TOKEN_REFRESHED') applyRefreshedTokens(payload);
      }

      if (!response.ok || !payload || payload.ok !== true || typeof payload.redirect_url !== 'string') {
        let message = payload && payload.error ? payload.error : (!parsed.contentType.toLowerCase().includes('application/json')
          ? `${form.dataset.invalidResponseMessage || 'Unexpected server response.'} (HTTP ${response.status})`
          : (response.status ? `HTTP ${response.status}: ${form.dataset.invalidResponseMessage || 'Unexpected server response.'}` : (form.dataset.invalidResponseMessage || 'The server returned an unexpected response.')));
        if (payload && payload.support_reference && response.status >= 500) message += ` (Support reference: ${payload.support_reference})`;
        reset(message);
        return;
      }

      let destination;
      try { destination = new URL(payload.redirect_url); }
      catch (_) { reset(form.dataset.invalidResponseMessage || 'The server returned an invalid WhatsApp destination.'); return; }
      if (destination.protocol !== 'https:' || destination.hostname !== 'wa.me' || !/^\/[0-9]{8,15}$/.test(destination.pathname)) {
        reset(form.dataset.invalidResponseMessage || 'The server returned an unexpected WhatsApp destination.');
        return;
      }
      clearTimers();
      setStatus(form.dataset.savedMessage || 'Case saved. Opening WhatsApp…');
      // One successful form action: save on the server, then leave this page.
      window.location.assign(destination.href);
    } catch (error) {
      const message = error && error.name === 'AbortError'
        ? (form.dataset.timeoutMessage || 'No response arrived in time. You can safely retry with the same button.')
        : (form.dataset.networkMessage || 'The connection was interrupted. Retry with the same button.');
      reset(message);
    }
  });

  window.addEventListener('pageshow', event => {
    if (activeController) activeController.abort();
    reset('');
    // Returning from WhatsApp via browser Back resets the control in place.
    // The signed case token remains idempotent, so a repeated send cannot duplicate it.
  });
});

// Admin list filtering is intentionally client-side and applies only to the 250 recent rows
// that the server currently renders. The CSV export remains the full-data export path.
document.addEventListener('DOMContentLoaded', () => {
  const search = document.getElementById('case-search');
  const status = document.getElementById('case-status-filter');
  const count = document.getElementById('case-filter-count');
  const empty = document.getElementById('case-filter-empty');
  const rows = Array.from(document.querySelectorAll('[data-case-row]'));

  if (rows.length && search && status && count) {
    const template = count.dataset.countTemplate || 'Showing __visible__ of __total__ loaded cases';
    const normalize = value => String(value || '').normalize('NFKC').toLocaleLowerCase();
    const update = () => {
      const query = normalize(search.value.trim());
      const selectedStatus = status.value;
      let visible = 0;
      rows.forEach(row => {
        const matchesText = !query || normalize(row.textContent).includes(query);
        const matchesStatus = selectedStatus === 'all' || row.dataset.caseStatus === selectedStatus;
        const show = matchesText && matchesStatus;
        row.hidden = !show;
        if (show) visible += 1;
      });
      if (empty) empty.hidden = visible !== 0;
      count.textContent = template
        .replace('__visible__', String(visible))
        .replace('__total__', String(rows.length));
    };
    search.addEventListener('input', update);
    status.addEventListener('change', update);
    update();
  }

  // Copy references without exposing them to a third-party clipboard library.
  const copyButton = document.querySelector('[data-copy-reference]');
  const copyFeedback = document.getElementById('copy-feedback');
  if (copyButton && copyFeedback) {
    copyButton.addEventListener('click', async () => {
      const value = copyButton.dataset.copyReference || '';
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(value);
        } else {
          const helper = document.createElement('textarea');
          helper.value = value;
          helper.setAttribute('readonly', '');
          helper.style.position = 'fixed';
          helper.style.opacity = '0';
          document.body.appendChild(helper);
          helper.select();
          const copied = document.execCommand('copy');
          helper.remove();
          if (!copied) throw new Error('Clipboard command unavailable');
        }
        copyFeedback.textContent = copyButton.dataset.copySuccess || 'Copied.';
      } catch (_error) {
        copyFeedback.textContent = copyButton.dataset.copyError || 'Copy failed.';
      }
    });
  }

  const printButton = document.getElementById('print-report');
  if (printButton) printButton.addEventListener('click', () => window.print());

  // A page restored from the back-forward cache must not retain a disabled submit button.
  window.addEventListener('pageshow', () => {
    const form = document.getElementById('case-intake-form');
    if (!form) return;
    form.removeAttribute('aria-busy');
    delete form.dataset.submitting;
    const submit = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submit) {
      submit.disabled = false;
      submit.classList.remove('is-submitting');
    }
  });
});
