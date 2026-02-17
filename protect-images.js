/* =========================
   protect-images.js
   ---------------------------------------------------------
   "Speed bumps" to discourage casual image saving.
   Not a hard technical lock — determined users can always
   view page source — but removes the easy one-tap routes.

   Protections applied:
   1. Right-click context menu  — blocked on images, canvas,
                                   open lightbox, .protect-zone
   2. Drag-start                — blocked on img + video
   3. Touch long-press (mobile) — blocked via touchstart
                                   preventDefault on protected els
   4. selectstart               — blocked on .protect-zone so
                                   click-drag doesn't select img
   5. keyboard shortcut hints   — no action taken on S/U/C etc.
                                   (browser shortcuts can't be
                                   reliably blocked; this is noted
                                   for awareness only)
========================= */

(function () {

  /* Returns true when the gallery/gear lightbox is open */
  function lightboxIsOpen() {
    const lb = document.querySelector('.lightbox');
    return lb ? lb.classList.contains('open') : false;
  }

  /* Returns true when the target is inside a protected area */
  function isProtected(target) {
    if (!target || !target.closest) return false;
    return (
      target.closest('canvas')        ||   // puzzle canvas
      target.closest('.protect-zone') ||   // hero + any marked zone
      target.closest('.lightbox-inner') || // inside lightbox
      target.closest('#galleryGrid')   ||  // gallery grid
      target.tagName === 'IMG'         ||  // any image
      target.tagName === 'VIDEO'            // any video
    );
  }

  /* ── 1. Right-click context menu ── */
  document.addEventListener('contextmenu', (e) => {
    if (isProtected(e.target)) {
      e.preventDefault();
      return;
    }
    // Also block when lightbox is open, regardless of exact target
    if (lightboxIsOpen()) {
      e.preventDefault();
    }
  });

  /* ── 2. Drag start (desktop) ── */
  document.addEventListener('dragstart', (e) => {
    if (e.target.closest?.('img, video')) {
      e.preventDefault();
    }
  });

  /* ── 3. Touch long-press (mobile "Save image" sheet) ──
     touchstart with preventDefault on the touch event stops
     the browser from registering the long-press gesture.
     { passive: false } is required to allow preventDefault. */
  document.addEventListener('touchstart', (e) => {
    if (isProtected(e.target)) {
      // Only cancel if it looks like a hold (single touch on img/canvas)
      // We don't cancel multi-touch (pinch-zoom) — check touches.length
      if (e.touches.length === 1 && (
        e.target.tagName === 'IMG'    ||
        e.target.tagName === 'VIDEO'  ||
        e.target.closest('canvas')    ||
        e.target.closest('.lightbox-inner')
      )) {
        e.preventDefault();
      }
    }
  }, { passive: false });

  /* ── 4. Select-start (stops click-drag text/image selection) ── */
  document.addEventListener('selectstart', (e) => {
    if (
      e.target.closest?.('.protect-zone') ||
      e.target.closest?.('.lightbox-inner') ||
      e.target.tagName === 'IMG'
    ) {
      e.preventDefault();
    }
  });

  /* ── 5. Pointer events on lightbox image ──
     Belt-and-braces: if the CSS pointer-events:none ever gets
     overridden by another stylesheet, this ensures the image
     itself still can't be interacted with while the lightbox
     is open. */
  document.addEventListener('pointerdown', (e) => {
    if (lightboxIsOpen() && e.target.closest('.lightbox-inner img')) {
      e.preventDefault();
    }
  });

})();
