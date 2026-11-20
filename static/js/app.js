(() => {
  'use strict';
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
  const closeMenu = () => {
    if (!toggle || !nav) return;
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  };
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
    document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMenu(); });
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
