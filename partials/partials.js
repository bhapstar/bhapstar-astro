<<<<<<< HEAD
(async function(){
  async function loadInto(id, url){
    const el = document.getElementById(id);
    if(!el) return;

    const res = await fetch(url, { cache: 'no-store' });
    if(!res.ok) throw new Error(url + ' (HTTP ' + res.status + ')');

    el.innerHTML = await res.text();
  }

  try{
    await loadInto('siteHeader', 'partials/header.html');
    await loadInto('siteFooter', 'partials/footer.html');

    // Year
    const y = document.getElementById('y');
    if(y) y.textContent = new Date().getFullYear();

    // Burger (must bind AFTER header is injected)
    const burger = document.querySelector('.burger');
    const menu = document.querySelector('.nav-menu');

    if(burger && menu){
      burger.addEventListener('click', () => {
        const open = menu.classList.toggle('open');
        burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      });

      document.addEventListener('click', (e) => {
        if(menu.classList.contains('open') && !menu.contains(e.target) && !burger.contains(e.target)){
          menu.classList.remove('open');
          burger.setAttribute('aria-expanded','false');
        }
      });

      document.addEventListener('keydown', (e) => {
        if(e.key === 'Escape'){
          menu.classList.remove('open');
          burger.setAttribute('aria-expanded','false');
        }
      });
    }

    // Active nav link based on current page
    const path = location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-menu a').forEach(a => {
      const href = (a.getAttribute('href') || '').split('/').pop();
      if(href === path) a.classList.add('active');
      else a.classList.remove('active');
    });

  }catch(err){
    console.error('[partials] failed:', err);
  }
})();
=======
(async function(){
  async function loadInto(id, url){
    const el = document.getElementById(id);
    if(!el) return;

    const res = await fetch(url, { cache: 'no-store' });
    if(!res.ok) throw new Error(url + ' (HTTP ' + res.status + ')');

    el.innerHTML = await res.text();
  }

  try{
    await loadInto('siteHeader', 'partials/header.html');
    await loadInto('siteFooter', 'partials/footer.html');

    // Year
    const y = document.getElementById('y');
    if(y) y.textContent = new Date().getFullYear();

    // Burger (must bind AFTER header is injected)
    const burger = document.querySelector('.burger');
    const menu = document.querySelector('.nav-menu');

    if(burger && menu){
      burger.addEventListener('click', () => {
        const open = menu.classList.toggle('open');
        burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      });

      document.addEventListener('click', (e) => {
        if(menu.classList.contains('open') && !menu.contains(e.target) && !burger.contains(e.target)){
          menu.classList.remove('open');
          burger.setAttribute('aria-expanded','false');
        }
      });

      document.addEventListener('keydown', (e) => {
        if(e.key === 'Escape'){
          menu.classList.remove('open');
          burger.setAttribute('aria-expanded','false');
        }
      });
    }

    // Active nav link based on current page
    const path = location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-menu a').forEach(a => {
      const href = (a.getAttribute('href') || '').split('/').pop();
      if(href === path) a.classList.add('active');
      else a.classList.remove('active');
    });

  }catch(err){
    console.error('[partials] failed:', err);
  }
})();
>>>>>>> df22d6c (Initial VS Code connection)
