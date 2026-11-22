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
// Keep the simple HTML form flow; only prevent accidental double-clicks.
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('case-create-form');
  if (!form) return;
  form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"]');
    if (button) button.disabled = true;
  }, { once: true });
});

// Live character counter for the case description.
document.addEventListener('DOMContentLoaded',()=>{const field=document.getElementById('case-story');const count=document.getElementById('story-count');if(field&&count){const update=()=>{count.textContent=String(field.value.length);count.style.color=field.value.length>=25?'#c8ff3d':'#96a3a4'};field.addEventListener('input',update);update();}});


// Case intake uses a standard server-rendered POST/redirect flow. This avoids
// AJAX/CSRF token renewal races and makes the saved-case second step explicit.

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

  // Open the prepared WhatsApp report from a direct button click.
  // Keep this YAKUZA confirmation tab open so visitors can return after sending.
  const whatsappButton = document.getElementById('case-ready-whatsapp');
  if (whatsappButton) {
    whatsappButton.addEventListener('click', () => {
      const target = whatsappButton.dataset.whatsappUrl;
      if (!target) return;
      const opened = window.open(target, '_blank');
      if (opened) {
        try { opened.opener = null; } catch (_error) { /* Browser may isolate the new tab automatically. */ }
      } else {
        // Popup blockers can prevent a new tab; still let the visitor continue.
        window.location.assign(target);
      }
    });
  }

  const printButton = document.getElementById('print-report');
  if (printButton) printButton.addEventListener('click', () => window.print());

});
