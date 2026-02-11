(function () {
  function lightboxIsOpen() {
    const lb = document.querySelector(".lightbox");
    return lb && lb.classList.contains("open");
  }

  document.addEventListener("contextmenu", (e) => {
    const target = e.target;
    
    // Allow puzzle interactions (or block menu specifically on canvas)
    if (target.closest?.("canvas")) {
      e.preventDefault();
      return;
    }

    // Block inside open lightbox
    if (lightboxIsOpen() && target.closest?.(".lightbox")) {
      e.preventDefault();
      return;
    }

    // Block on hero (or any zone you mark)
    if (target.closest?.(".protect-zone")) {
      e.preventDefault();
      return;
    }

    // Block on images
    if (target.closest?.("img")) {
      e.preventDefault();
    }
  });

document.addEventListener("dragstart", (e) => {
  if (e.target.closest?.("img, video")) e.preventDefault();
});

})();

