/* =========================
   partials.js — bhapstar
   ---------------------------------------------------------
   Loads the shared header + footer HTML partials, then runs:
   1. Dynamic year in footer
   2. Puzzles dropdown toggle (with double-bind + double-load guards)
   3. Active nav link highlighting
   4. Puzzles / Articles submenu toggles + active-child highlighting
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
    var theme = 'dark';
    try {
      var saved = localStorage.getItem('theme');
      if (saved === 'light' || saved === 'dark') {
        theme = saved;
        document.documentElement.setAttribute('data-theme', saved);
      }
    } catch (e) {}
    /* The <meta name="theme-color"> in every page is hardcoded to the dark
       value, so a returning light-theme visitor used to get a dark browser
       chrome bar until they toggled. Set it here as well as in applyTheme. */
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', theme === 'light' ? '#eceaf6' : '#050414');
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
    // Bind EVERY .nav-group (the header's Puzzles group AND the footer's),
    // each toggling its own submenu. Per-button double-bind guard.
    const navGroups = document.querySelectorAll('.nav-group');

    navGroups.forEach((group) => {
      const btn     = group.querySelector('.nav-group-btn');
      const submenu = group.querySelector('.nav-submenu');
      if (!btn || !submenu || btn.dataset.bound) return;
      btn.dataset.bound = '1';

      const closeSubmenu = () => {
        submenu.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      };
      const openSubmenu = () => {
        submenu.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      };

      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        submenu.classList.contains('open') ? closeSubmenu() : openSubmenu();
      });

      // Close after a link is chosen (navigation happens anyway)
      submenu.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', closeSubmenu);
      });

      // Expose a closer for the shared outside-click / Escape handlers
      group._closeSubmenu = closeSubmenu;
    });

    // One shared outside-click + Escape handler covering all groups
    if (navGroups.length && !document.body.dataset.navGroupsBound) {
      document.body.dataset.navGroupsBound = '1';

      document.addEventListener('click', (e) => {
        document.querySelectorAll('.nav-group').forEach((group) => {
          const submenu = group.querySelector('.nav-submenu');
          if (submenu && submenu.classList.contains('open') && !group.contains(e.target)) {
            group._closeSubmenu && group._closeSubmenu();
          }
        });
      });

      document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        document.querySelectorAll('.nav-group').forEach((group) => {
          group._closeSubmenu && group._closeSubmenu();
        });
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

    // Section directories: /gear/<slug>.html and /articles/<slug>.html are real
    // pages that live one level down, so the filename match above never fires
    // for their parent nav entry. Mark the parent active from the directory.
    const dir = location.pathname.split('/').filter(Boolean)[0] || '';
    if (dir === 'gear' || dir === 'articles') {
      document.querySelectorAll(`.nav-menu a[href$="/${dir}.html"]`).forEach(a => {
        a.classList.add('active');
        a.setAttribute('aria-current', 'page');
      });
    }

    // If a submenu child is the active page (a puzzle, a field card page, or
    // an individual article), highlight that group's button — but don't force
    // the popover open now that the nav is always visible.
    //
    // This runs AFTER the directory match above, not before. "All Articles"
    // now lives inside the Articles popover, so on /articles/<slug>.html it is
    // the directory rule that marks it active. Highlighting the buttons first
    // would leave the Articles button unlit on every article page.
    document.querySelectorAll('.nav-submenu a.active').forEach(a => {
      a.closest('.nav-group')?.querySelector('.nav-group-btn')?.classList.add('active');
    });


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

  /* ── Tap counter ──
     Cloudflare Web Analytics discards query strings, so ?src=... never reaches
     it. This records the source to the taps Worker instead.

     It lives here rather than in card.html so that any page can be the target
     of a tag, a printed QR code or a link, not just the card. It only fires
     for a source in the list below, and it is fire and forget: if the Worker
     is down or the request is blocked, the page does not care.

     The visitor id is the same key the gallery likes module uses, so a device
     that already has one is not given a second. It exists so the stats can
     report distinct devices as well as raw taps. */
  try {
    var TAP_URL  = 'https://bhapstar-taps.bhapindersingh.workers.dev/tap';
    var TAP_SRCS = {
      nfc: 1,          // NFC business card
      qr: 1,           // generic printed QR
      card: 1,         // printed QR cards
      x: 1,            // links posted on X
      'pdf-phone': 1,  // QR on the phone field card
      'pdf-camera': 1, // QR on the camera field card
      'pdf-meteors': 1, // QR on the meteor shower field card
      'pdf-calibration': 1, // QR on the calibration frames field card
      'pdf-asiair': 1, // QR on the ASIAir field card
      'pdf-moon': 1    // QR on the Moon field card
    };
    var tapSrc = new URLSearchParams(location.search).get('src');

    if (tapSrc && TAP_SRCS[tapSrc]) {
      var uid = localStorage.getItem('_bhap_uid');
      if (!uid) {
        uid = (window.crypto && crypto.randomUUID)
          ? crypto.randomUUID()
          : String(Date.now()) + '-' + String(Math.random()).slice(2);
        localStorage.setItem('_bhap_uid', uid);
      }
      // text/plain keeps this a simple request, so there is no CORS preflight
      // and the tap costs one round trip rather than two.
      fetch(TAP_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
        body: JSON.stringify({ src: tapSrc, uid: uid }),
        keepalive: true
      }).catch(function () { /* a missed tap is not worth a broken page */ });

      // Tidy the address bar so a shared or bookmarked link does not carry the
      // source with it and count a second time.
      try {
        var qs = new URLSearchParams(location.search);
        qs.delete('src');
        var rest = qs.toString();
        history.replaceState(null, '',
          location.pathname + (rest ? '?' + rest : '') + location.hash);
      } catch (e) { /* not worth breaking the page over */ }
    }
  } catch (e) { /* localStorage can throw in locked-down browsers */ }

})();


/* ══════════════════════════════════════════════════════════════════════
   Field card download counter
   ----------------------------------------------------------------------
   The tap counter above answers "how did somebody reach the site".
   This answers the opposite question: "which field cards do people
   actually take away".

   Those are genuinely different numbers and must not be mixed. A
   'pdf-moon' tap means a QR printed ON the Moon card was scanned, so
   somebody already holding a card came to the site. A 'dl-moon' event
   means somebody on the site downloaded that card. Same PDF, opposite
   directions, hence the separate dl- prefix.

   It is a delegated listener on the document rather than a handler bound
   to each link, so it covers the download button on every article page
   and the six on field-cards.html without either generator knowing this
   exists. A card added later is covered by adding one line to DL_SRCS.

   Whitelisted by filename for the same reason the tap counter is
   whitelisted by source: the Worker rejects anything not in its own
   VALID_SRC list, so sending a value it will refuse is a wasted request.

   This counts clicks on the link, which is the only thing a static site
   can see. It is not a count of completed downloads, and a browser
   extension that blocks the request will make it an undercount. It is
   there for the shape of the numbers, not for an audit.
   ══════════════════════════════════════════════════════════════════════ */
(function () {
  var DL_URL = 'https://bhapstar-taps.bhapindersingh.workers.dev/tap';

  // PDF filename -> the source recorded against the download.
  // Keys must match the files in /downloads/, values must match VALID_SRC
  // in the Worker.
  var DL_SRCS = {
    'milky-way-phone-field-card.pdf':  'dl-phone',
    'milky-way-camera-field-card.pdf': 'dl-camera',
    'meteor-shower-field-card.pdf':    'dl-meteors',
    'moon-field-card.pdf':             'dl-moon',
    'asiair-field-card.pdf':           'dl-asiair',
    'calibration-frames-field-card.pdf': 'dl-calibration'
  };

  // Same key the tap counter and the gallery likes module use, so a device
  // that already has an id is not given a second one.
  function visitorId() {
    try {
      var uid = localStorage.getItem('_bhap_uid');
      if (!uid) {
        uid = (window.crypto && crypto.randomUUID)
          ? crypto.randomUUID()
          : String(Date.now()) + '-' + String(Math.random()).slice(2);
        localStorage.setItem('_bhap_uid', uid);
      }
      return uid;
    } catch (e) {
      return null;   // locked-down browser: still count the download
    }
  }

  document.addEventListener('click', function (ev) {
    var link = ev.target.closest && ev.target.closest('a[href*="/downloads/"]');
    if (!link) return;

    var file = (link.getAttribute('href') || '').split('/').pop().split('?')[0];
    var src  = DL_SRCS[file];
    if (!src) return;

    // text/plain keeps this a simple request, so there is no CORS preflight.
    // keepalive matters because the click may start a navigation on browsers
    // that open the PDF in place rather than saving it.
    try {
      fetch(DL_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
        body: JSON.stringify({ src: src, uid: visitorId() }),
        keepalive: true
      }).catch(function () { /* a missed count is not worth a broken download */ });
    } catch (e) { /* likewise */ }
    // No preventDefault anywhere: the download must happen either way.
  }, true);
})();


/* ══════════════════════════════════════════════════════════════════════
   Figure lightbox
   ----------------------------------------------------------------------
   Makes every figure on an article page openable: photographs and the
   inline SVG diagrams alike. Lives here rather than in the article
   generator so that all thirteen article pages get it without being
   rebuilt, and so a new article gets it for free.

   Scoped to figure.article-fig. That keeps it away from the gallery,
   which has its own lightbox with zoom, rotate and navigation, and away
   from the icon SVGs in the header and footer.

   Clicking anywhere closes, the image included. Escape closes. The X is
   there for keyboard and screen reader users.
   ══════════════════════════════════════════════════════════════════════ */
(function () {
  var figures = document.querySelectorAll('figure.article-fig');
  if (!figures.length) return;

  // The gallery runs its own overlay. If one is already on the page,
  // stay out of its way rather than stacking two lightboxes.
  if (document.querySelector('.lightbox')) return;

  var box = null, stage = null, cap = null, opener = null;

  function build() {
    box = document.createElement('div');
    box.className = 'figbox';
    box.id = 'figbox';
    box.hidden = true;
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-label', 'Enlarged figure');
    box.tabIndex = -1;

    var x = document.createElement('button');
    x.type = 'button';
    x.className = 'figbox-x';
    x.setAttribute('aria-label', 'Close');
    x.innerHTML = '&#215;';

    stage = document.createElement('div');
    stage.className = 'figbox-stage';

    cap = document.createElement('p');
    cap.className = 'figbox-cap';

    var hint = document.createElement('p');
    hint.className = 'figbox-hint';
    hint.textContent = 'Click anywhere to close';

    box.appendChild(x);
    box.appendChild(stage);
    box.appendChild(cap);
    box.appendChild(hint);
    document.body.appendChild(box);

    // One handler on the overlay: the image is inside it, so a click on
    // the picture closes exactly like a click on the backdrop.
    box.addEventListener('click', close);
    box.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' || ev.key === 'Esc') { ev.preventDefault(); close(); }
    });
  }

  function captionFor(fig) {
    var fc = fig.querySelector('figcaption');
    return fc ? fc.textContent.replace(/\s+/g, ' ').trim() : '';
  }

  function open(fig, node) {
    if (!box) build();

    opener = node;
    stage.innerHTML = '';

    var diagram = node.tagName.toLowerCase() === 'svg';
    stage.classList.toggle('is-diagram', diagram);

    if (diagram) {
      // Cloned rather than moved, so the figure keeps its diagram. The
      // clone stays in the document, so the var() colours it is drawn
      // with still resolve against the current theme.
      var svg = node.cloneNode(true);
      svg.removeAttribute('width');
      svg.removeAttribute('height');
      svg.removeAttribute('class');
      svg.setAttribute('aria-hidden', 'true');
      stage.appendChild(svg);
    } else {
      var img = document.createElement('img');
      // currentSrc resolves srcset, so a lightbox never shows a smaller
      // file than the one already on the page.
      img.src = node.currentSrc || node.src;
      img.alt = node.alt || '';
      img.decoding = 'async';
      stage.appendChild(img);
    }

    var text = captionFor(fig);
    cap.textContent = text;
    cap.style.display = text ? '' : 'none';

    box.hidden = false;
    // Next frame, so the opening transition has a state to move from.
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { box.classList.add('open'); });
    });
    document.documentElement.style.overflow = 'hidden';
    box.focus();
  }

  function close() {
    if (!box || box.hidden) return;
    box.classList.remove('open');
    document.documentElement.style.overflow = '';

    var done = function () {
      box.hidden = true;
      stage.innerHTML = '';
      if (opener && opener.focus) {
        // Focus goes back to the figure that was opened, not to the top.
        var host = opener.closest ? opener.closest('figure.article-fig') : null;
        if (host) host.focus();
      }
      opener = null;
    };

    var reduce = false;
    try {
      reduce = window.matchMedia &&
               window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (e) {}
    if (reduce) { done(); return; }
    window.setTimeout(done, 200);
  }

  Array.prototype.forEach.call(figures, function (fig) {
    var nodes = fig.querySelectorAll('img, svg');
    if (!nodes.length) return;

    Array.prototype.forEach.call(nodes, function (node) {
      // A figure holding two diagrams side by side gets one target each.
      var host = node.parentNode === fig ? fig : node;
      node.style.cursor = 'zoom-in';
      node.addEventListener('click', function (ev) {
        ev.preventDefault();
        open(fig, node);
      });
    });

    fig.classList.add('fig-openable');
    fig.tabIndex = 0;
    fig.setAttribute('role', 'button');
    fig.setAttribute('aria-label',
      (captionFor(fig) || 'Figure') + '. Activate to enlarge.');
    fig.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        open(fig, fig.querySelector('img, svg'));
      }
    });
  });
})();
