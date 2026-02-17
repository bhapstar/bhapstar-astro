/* =========================
   partials.js — bhapstar
   ---------------------------------------------------------
   Loads the shared header + footer HTML partials, then runs:
   1. Dynamic year in footer
   2. Burger menu toggle (with double-bind + double-load guards)
   3. Active nav link highlighting
   4. Scroll reveal (with MutationObserver for dynamic cards)
   5. Hero star-particle canvas (index page only)
========================= */

(async function () {

  /* ─────────────────────────────────────────
     LOAD PARTIALS
     - Guards against double-injection if the
       script is accidentally included twice
  ───────────────────────────────────────── */
  async function loadInto(id, url) {
    const el = document.getElementById(id);
    if (!el) return;
    if (el.dataset.loaded === '1') return;    // double-load guard

    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(url + ' (HTTP ' + res.status + ')');

    el.innerHTML = await res.text();
    el.dataset.loaded = '1';
  }

  try {
    await loadInto('siteHeader', 'partials/header.html');
    await loadInto('siteFooter', 'partials/footer.html');

    /* ── Dynamic year ── */
    const y = document.getElementById('y');
    if (y) y.textContent = new Date().getFullYear();


    /* ─────────────────────────────────────────
       BURGER MENU
       - Must bind AFTER header HTML is injected
       - Double-bind guard via data-bound
       - Closes on outside click, Escape, or
         clicking any nav link (mobile UX)
    ───────────────────────────────────────── */
    const burger = document.querySelector('.burger');
    const menu   = document.querySelector('.nav-menu');

    if (burger && menu && !burger.dataset.bound) {
      burger.dataset.bound = '1';

      function menuOpen() {
        menu.classList.add('open');
        burger.setAttribute('aria-expanded', 'true');
      }
      function menuClose() {
        menu.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
      }

      burger.addEventListener('click', (e) => {
        e.stopPropagation();
        menu.classList.contains('open') ? menuClose() : menuOpen();
      });

      document.addEventListener('click', (e) => {
        if (menu.classList.contains('open') &&
            !menu.contains(e.target) &&
            !burger.contains(e.target)) {
          menuClose();
        }
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') menuClose();
      });

      // Close when a nav link is tapped (mobile UX)
      menu.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', menuClose);
      });
    }


    /* ─────────────────────────────────────────
       ACTIVE NAV LINK
       Matches the current page filename to the
       href of each nav link and adds .active
    ───────────────────────────────────────── */
    const path = location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-menu a').forEach(a => {
      const href = (a.getAttribute('href') || '').split('/').pop();
      if (href === path) {
        a.classList.add('active');
        a.setAttribute('aria-current', 'page');
      } else {
        a.classList.remove('active');
        a.removeAttribute('aria-current');
      }
    });


    /* ─────────────────────────────────────────
       SCROLL REVEAL
       - Adds .reveal to targets, then .in when
         they enter the viewport
       - MutationObserver catches cards injected
         dynamically (gallery, gear pages)
       - Respects prefers-reduced-motion
    ───────────────────────────────────────── */
    (function initScrollReveal() {
      const SELECTOR     = '.section, .panel, .card';
      const reduceMotion =
        window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

      if (reduceMotion) {
        document.querySelectorAll(SELECTOR).forEach(el => {
          el.classList.add('reveal', 'in');
        });
        return;
      }

      const io = new IntersectionObserver((entries) => {
        entries.forEach(en => {
          if (en.isIntersecting) {
            en.target.classList.add('in');
            io.unobserve(en.target);
          }
        });
      }, { threshold: 0.10, rootMargin: '0px 0px -6% 0px' });

      function observe(el) {
        if (!el.classList.contains('reveal')) el.classList.add('reveal');
        io.observe(el);
      }

      // Observe elements already in the DOM at load time
      document.querySelectorAll(SELECTOR).forEach(observe);

      // Watch for elements injected after load (gallery cards, gear cards)
      new MutationObserver((mutations) => {
        mutations.forEach(m => {
          m.addedNodes.forEach(node => {
            if (node.nodeType !== 1) return;
            if (node.matches?.(SELECTOR))            observe(node);
            node.querySelectorAll?.(SELECTOR).forEach(observe);
          });
        });
      }).observe(document.body, { childList: true, subtree: true });
    })();


    /* ─────────────────────────────────────────
       HERO STAR PARTICLE CANVAS
       - Only runs when .hero exists (index page)
       - Draws 160 slowly fading stars on a
         <canvas> layered above the bg slideshow
       - Each star gently breathes in and out
         using a slow sine wave (3–9 s cycle)
       - Skipped if prefers-reduced-motion is set
    ───────────────────────────────────────── */
    (function initHeroStars() {
      const hero = document.querySelector('.hero');
      if (!hero) return;
      if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;

      const canvas = document.createElement('canvas');
      canvas.id    = 'heroStars';
      canvas.setAttribute('aria-hidden', 'true');
      hero.prepend(canvas);   // sits below content, above bg layers

      const ctx = canvas.getContext('2d');
      let W, H, stars = [], raf;
      const COUNT = 160;

      function rand(min, max) { return min + Math.random() * (max - min); }

      function build() {
        stars = Array.from({ length: COUNT }, () => ({
          x:      rand(0, W),
          y:      rand(0, H),
          r:      rand(0.3, 1.6),
          // Gentle peak brightness — soft and visible, never harsh
          peak:   rand(0.25, 0.65),
          // Glacially slow cycle: each star takes 30–90 seconds for one full breathe
          speed:  rand(0.000003, 0.000009),
          // Random start point in the sine cycle so stars aren't in sync
          phase:  rand(0, Math.PI * 2),
        }));
      }

      function resize() {
        W = canvas.width  = hero.offsetWidth;
        H = canvas.height = hero.offsetHeight;
        build();
      }

      function draw(t) {
        ctx.clearRect(0, 0, W, H);
        for (const s of stars) {
          // sin oscillates between -1 and 1; remap to 0–1 for a clean fade
          const wave = 0.5 + 0.5 * Math.sin(t * s.speed * 1000 + s.phase);
          // Fade from near-zero (0.04) up to each star's individual peak
          const a = 0.04 + (s.peak - 0.04) * wave;
          ctx.beginPath();
          ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255,255,255,${a.toFixed(3)})`;
          ctx.fill();
        }
      }

      function frame(t) { draw(t); raf = requestAnimationFrame(frame); }

      resize();

      // Debounced resize — avoids thrashing on every pixel of a drag resize
      let resizeTimer;
      window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
          cancelAnimationFrame(raf);
          resize();
          raf = requestAnimationFrame(frame);
        }, 120);
      });

      raf = requestAnimationFrame(frame);
    })();


  } catch (err) {
    console.error('[partials] failed:', err);
  }

})();
