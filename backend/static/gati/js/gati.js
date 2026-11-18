document.addEventListener('DOMContentLoaded',()=>{
 const menu=document.querySelector('.menu-button');
 menu?.addEventListener('click',()=>{const open=document.body.classList.toggle('nav-open');menu.setAttribute('aria-expanded',String(open));});
 const closeMenu=()=>{document.body.classList.remove('nav-open');menu?.setAttribute('aria-expanded','false');};
 document.addEventListener('keydown',event=>{if(event.key==='Escape'){closeMenu();menu?.focus();}});
 document.addEventListener('click',event=>{if(document.body.classList.contains('nav-open')&&!event.target.closest('.sidebar,.menu-button'))closeMenu();});
 document.querySelectorAll('.print-button').forEach(button=>button.addEventListener('click',()=>window.print()));
});
document.addEventListener('htmx:responseError',event=>{
 const box=document.getElementById('records');
 if(box){const alert=document.createElement('div');alert.className='alert alert-warning';alert.setAttribute('role','alert');alert.textContent='Não foi possível atualizar a listagem. Recarregue a página e confira os filtros.';box.prepend(alert);}
});
