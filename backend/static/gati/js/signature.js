document.addEventListener('DOMContentLoaded',async()=>{
 if(!document.getElementById('signature-start')) return;
 const token=location.hash.slice(1);history.replaceState(null,'',location.pathname);
 const status=document.getElementById('signature-status');
 if(!token){status.textContent='Convite ausente. Abra o link recebido ou solicite um novo convite.';return;}
 const form=document.getElementById('token-form');const data=new FormData(form);data.set('token',token);
 try{const response=await fetch(location.pathname,{method:'POST',body:data,credentials:'same-origin'});const result=await response.json();
 if(response.ok) location.replace(result.url);else status.textContent=result.error||'Não foi possível abrir o convite.';
 }catch{status.textContent='Conexão indisponível. Abra novamente o link do convite.';}
});
