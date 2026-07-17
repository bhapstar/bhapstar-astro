/* =========================
   partials.js — bhapstar
   ---------------------------------------------------------
   Loads the shared header + footer HTML partials, then runs:
   1. Dynamic year in footer
   2. Puzzles dropdown toggle (with double-bind + double-load guards)
   3. Active nav link highlighting
   4. Puzzles submenu toggle + auto-open on active child
   5. Scroll reveal (with MutationObserver for dynamic cards)
   6. Hero star-particle canvas (index page only)
   7. Instagram references (footer icon + homepage panel), gated by the
      single HIDE_INSTAGRAM flag below
========================= */

// Set to true to hide every Instagram reference site-wide in one go — the
// footer icon link on every page, and the whole "Latest from Instagram"
// panel on the homepage (including never loading embed.js at all). Useful
// for periods where a partner agreement restricts linking to personal
// social accounts. Flip this one line, commit, done — no other file needs
// touching. Set back to false to restore everything.
const HIDE_INSTAGRAM = false;

// Hides the Field Notes page from navigation (header + footer links) site-wide
// without deleting the page — it stays reachable by direct URL. The per-image
// write-ups now live inline on the gallery (Options → Detailed info).
// Set back to false to restore the nav links.
const HIDE_FIELD_NOTES = true;

(async function () {

  /* ─────────────────────────────────────────
     THEME (dark is the default; light is opt-in)
     Apply any saved preference as early as this script
     runs, so light-mode users see minimal flash. The
     header toggle (wired further below) flips it live.
  ───────────────────────────────────────── */
  (function initThemeEarly(){
    try {
      var saved = localStorage.getItem('theme');
      if (saved === 'light' || saved === 'dark') {
        document.documentElement.setAttribute('data-theme', saved);
      }
    } catch (e) {}
  })();

  /* ─────────────────────────────────────────
     LOAD PARTIALS
     - Guards against double-injection if the
       script is accidentally included twice
  ───────────────────────────────────────── */
  async function loadInto(id, url) {
    const el = document.getElementById(id);
    if (!el) return;
    if (el.dataset.loaded === '1') return;    // double-load guard

    const res = await fetch(url, { cache: 'default' });
    if (!res.ok) throw new Error(url + ' (HTTP ' + res.status + ')');

    el.innerHTML = await res.text();
    el.dataset.loaded = '1';
  }

  /* ─────────────────────────────────────────
     SCROLL REVEAL — runs immediately, before any awaits,
     so the MutationObserver is live before gallery/blog
     cards are injected by their own async data fetches.
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
    }, {
      // threshold: 0 — reveal as soon as ANY part of the element intersects.
      // A ratio-based threshold (e.g. 0.10) is unreachable for elements much
      // taller than the viewport (the Field Notes section on mobile), leaving
      // them stuck at opacity 0. The rootMargin below still delays the reveal
      // until the element is slightly inside the viewport.
      threshold: 0,
      rootMargin: '0px 0px -8% 0px'
    });

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


  try {
    // Root-absolute URLs: GitHub Pages serves 404.html for nested missing
    // paths (e.g. /share/typo.html), where a relative 'partials/…' would
    // resolve to /share/partials/… and fail. All real pages live at the
    // site root, so absolute paths behave identically for them.
    await loadInto('siteHeader', '/partials/header.html');
    await loadInto('siteFooter', '/partials/footer.html');

    /* ── Hide Instagram references (gated by HIDE_INSTAGRAM above) ── */
    if (HIDE_INSTAGRAM) {
      // Footer social icon — present on every page
      document.querySelector('a.social-icon[href*="instagram.com"]')?.remove();
      // Homepage "Latest from Instagram" panel (no-op on other pages,
      // since the selector simply won't match anything there)
      document.querySelector('.instagram-section')?.remove();
    } else {
      // Only load Instagram's embed script when the panel is actually
      // shown — avoids the network request entirely when hidden.
      if (document.querySelector('.instagram-panel')) {
        const s = document.createElement('script');
        s.async = true;
        s.src = '//www.instagram.com/embed.js';
        document.body.appendChild(s);
      }
    }

    /* ── Hide Field Notes nav links (gated by HIDE_FIELD_NOTES above) ── */
    if (HIDE_FIELD_NOTES) {
      document.querySelectorAll('a[href*="field_notes.html"]').forEach(a => {
        (a.closest('li') || a).remove();
      });
    }

    /* ── Dynamic year ── */
    const y = document.getElementById('y');
    if (y) y.textContent = new Date().getFullYear();


    /* ─────────────────────────────────────────
       PUZZLES DROPDOWN
       - The burger has been removed; the header nav
         links are always visible now, so only the
         Puzzles group needs interaction.
       - Click toggles the submenu popover; it closes
         on outside click, Escape, or choosing a link.
       - Must bind AFTER header HTML is injected;
         double-bind guard via data-bound.
    ───────────────────────────────────────── */
    const menu        = document.querySelector('.nav-menu');
    const navGroup    = menu && menu.querySelector('.nav-group');
    const navGroupBtn = menu && menu.querySelector('.nav-group-btn');
    const navSubmenu  = menu && menu.querySelector('.nav-submenu');

    if (navGroup && navGroupBtn && navSubmenu && !navGroupBtn.dataset.bound) {
      navGroupBtn.dataset.bound = '1';

      function submenuOpen() {
        navSubmenu.classList.add('open');
        navGroupBtn.setAttribute('aria-expanded', 'true');
      }
      function submenuClose() {
        navSubmenu.classList.remove('open');
        navGroupBtn.setAttribute('aria-expanded', 'false');
      }

      navGroupBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        navSubmenu.classList.contains('open') ? submenuClose() : submenuOpen();
      });

      // Close when clicking anywhere outside the Puzzles group
      document.addEventListener('click', (e) => {
        if (navSubmenu.classList.contains('open') &&
            !navGroup.contains(e.target)) {
          submenuClose();
        }
      });

      // Close on Escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') submenuClose();
      });

      // Close after a puzzle link is chosen (navigation happens anyway)
      navSubmenu.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', submenuClose);
      });
    }


    /* ─────────────────────────────────────────
       THEME TOGGLE (button injected with the header)
       - Flips html[data-theme] between dark and light
       - Persists the choice to localStorage
       - Keeps the mobile browser chrome colour in sync
    ───────────────────────────────────────── */
    (function initThemeToggle(){
      const btn = document.querySelector('.theme-toggle');
      if (!btn || btn.dataset.bound) return;
      btn.dataset.bound = '1';

      function currentTheme(){
        return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      }
      function applyTheme(theme){
        document.documentElement.setAttribute('data-theme', theme);
        try { localStorage.setItem('theme', theme); } catch (e) {}
        btn.setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
        const meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute('content', theme === 'light' ? '#eceaf6' : '#050414');
      }

      btn.setAttribute('aria-pressed', currentTheme() === 'light' ? 'true' : 'false');
      btn.addEventListener('click', () => {
        applyTheme(currentTheme() === 'light' ? 'dark' : 'light');
      });
    })();


    /* ─────────────────────────────────────────
       ACTIVE NAV LINK
       Matches the current page filename to the
       href of each nav link and adds .active
    ───────────────────────────────────────── */
    const path = location.pathname.split('/').pop() || 'index.html';

    // Check all links including submenu links
    document.querySelectorAll('.nav-menu a, .nav-submenu a').forEach(a => {
      const href = (a.getAttribute('href') || '').split('/').pop();
      if (href === path) {
        a.classList.add('active');
        a.setAttribute('aria-current', 'page');
      } else {
        a.classList.remove('active');
        a.removeAttribute('aria-current');
      }
    });

    // If a puzzle page is the active page, highlight the Puzzles button —
    // but don't force the popover open now that the nav is always visible.
    const activeSubmenuLink = document.querySelector('.nav-submenu a.active');
    if (activeSubmenuLink) {
      const grp = activeSubmenuLink.closest('.nav-group');
      grp?.querySelector('.nav-group-btn')?.classList.add('active');
    }


    /* ─────────────────────────────────────────
       BACK TO TOP BUTTON
       - Injected once into <body>
       - Appears after scrolling 400px
       - Uses existing CSS vars for theming
       - Respects prefers-reduced-motion
    ───────────────────────────────────────── */
    (function initBackToTop() {
      if (document.getElementById('backToTop')) return; // guard

      const btn = document.createElement('button');
      btn.id            = 'backToTop';
      btn.type          = 'button';
      btn.setAttribute('aria-label', 'Back to top');
      btn.innerHTML     = '↑';

      const isMobile = window.matchMedia('(max-width: 720px)').matches;

      btn.style.cssText = `
        position: fixed;
        bottom: ${isMobile ? '110px' : '28px'};
        right: 22px;
        z-index: 900;
        width: 42px;
        height: 42px;
        border-radius: 50%;
        border: 1px solid rgba(167,139,250,0.35);
        background: rgba(10,8,30,0.75);
        color: var(--accent, #a78bfa);
        font-size: 18px;
        line-height: 1;
        cursor: pointer;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        opacity: 0;
        transform: translateY(12px);
        transition: opacity 250ms ease, transform 250ms ease;
        pointer-events: none;
      `;

      document.body.appendChild(btn);

      const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

      function update() {
        const visible = window.scrollY > 400;
        btn.style.opacity       = visible ? '1' : '0';
        btn.style.transform     = visible ? 'translateY(0)' : 'translateY(12px)';
        btn.style.pointerEvents = visible ? 'auto' : 'none';
      }

      window.addEventListener('scroll', update, { passive: true });
      update();

      btn.addEventListener('click', () => {
        if (reduceMotion) {
          window.scrollTo(0, 0);
        } else {
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
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
          r:      rand(0.75, 2.5),
          // Gentle peak brightness — soft and visible, never harsh
          peak:   rand(0.25, 0.65),
          // Glacially slow cycle: each star takes 30–90 seconds for one full breathe
          speed:  rand(0.000002, 0.000006),
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
