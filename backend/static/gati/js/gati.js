document.addEventListener('DOMContentLoaded', () => {
  const menu = document.querySelector('.menu-button');
  const sidebar = document.getElementById('app-sidebar');
  const close = sidebar?.querySelector('.shell-close');
  const backdrop = document.querySelector('.shell-backdrop');
  const workspace = document.querySelector('.app-shell .workspace');
  const skip = document.querySelector('.skip-link');

  if (menu && sidebar && close && backdrop && workspace) {
    const mobile = window.matchMedia('(max-width: 900px)');
    let lastMobile = mobile.matches;
    let focusLostOnResize = null;
    const isOpen = () => document.body.classList.contains('nav-open');
    const activeLink = () => sidebar.querySelector('a.selected') || sidebar.querySelector('nav a');

    const closeMenu = (restoreFocus = true) => {
      const wasOpen = isOpen();
      const focusWasInside = sidebar.contains(document.activeElement);
      document.body.classList.remove('nav-open');
      workspace.inert = false;
      if (skip) skip.inert = false;
      sidebar.removeAttribute('role');
      sidebar.removeAttribute('aria-modal');
      sidebar.removeAttribute('aria-label');
      backdrop.hidden = true;
      menu.setAttribute('aria-expanded', 'false');
      if (mobile.matches && (focusWasInside || (wasOpen && restoreFocus))) menu.focus();
      sidebar.inert = mobile.matches;
      if (!mobile.matches && (document.activeElement === close || document.activeElement === menu)) {
        activeLink()?.focus();
      }
    };

    const openMenu = () => {
      if (!mobile.matches || isOpen()) return;
      sidebar.inert = false;
      sidebar.setAttribute('role', 'dialog');
      sidebar.setAttribute('aria-modal', 'true');
      sidebar.setAttribute('aria-label', 'Navegação do GATI');
      document.body.classList.add('nav-open');
      backdrop.hidden = false;
      menu.setAttribute('aria-expanded', 'true');
      close.focus();
      workspace.inert = true;
      if (skip) skip.inert = true;
    };

    menu.hidden = false;
    close.hidden = false;
    document.body.classList.add('nav-enhanced');
    closeMenu(false);
    // A regra responsiva pode ocultar o elemento antes do evento change.
    document.addEventListener('focusout', event => {
      if (mobile.matches !== lastMobile && !event.relatedTarget) focusLostOnResize = event.target;
    });
    mobile.addEventListener('change', () => {
      const lost = focusLostOnResize;
      focusLostOnResize = null;
      lastMobile = mobile.matches;
      closeMenu(false);
      if (document.activeElement !== document.body || !lost) return;
      if (mobile.matches && sidebar.contains(lost)) menu.focus();
      if (!mobile.matches && (lost === close || lost === menu)) activeLink()?.focus();
    });
    menu.addEventListener('click', openMenu);
    close.addEventListener('click', () => closeMenu());
    backdrop.addEventListener('click', () => closeMenu());

    document.addEventListener('keydown', event => {
      if (!isOpen()) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        closeMenu();
      }
      if (event.key === 'Tab') {
        const items = [...sidebar.querySelectorAll('a[href], button:not([disabled])')]
          .filter(item => item.getClientRects().length && getComputedStyle(item).visibility === 'visible');
        const first = items[0];
        const last = items[items.length - 1];
        if (!first) return;
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    });
    document.addEventListener('focusin', event => {
      if (isOpen() && !sidebar.contains(event.target)) close.focus();
    });
  }

  document.querySelectorAll('.print-button').forEach(button => button.addEventListener('click', () => window.print()));
});

document.addEventListener('htmx:responseError', () => {
  const box = document.getElementById('records');
  if (box) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-warning';
    alert.setAttribute('role', 'alert');
    alert.textContent = 'Não foi possível atualizar a listagem. Recarregue a página e confira os filtros.';
    box.prepend(alert);
  }
});
