# Render Free — Fase 1 de homologacao do GATI

**Estado:** preparacao de codigo; nao significa deploy aprovado nem ambiente publicado.
**Arquitetura mantida:** Django no Render Free, Neon PG18, R2 privado e scanner Windows
independente, a serem integrados nas fases posteriores.

## Decisoes e riscos

- Um Web Service `free` declarado em `render.yaml`, com auto-deploy **desligado**.
- Django WSGI por Gunicorn 26.2.0, com 1 worker e 2 threads (parametros iniciais,
  nao comprovacao de performance).
- Docker Python 3.14 slim; ClamAV nao roda nem e instalado no contêiner.
- Uma regiao Render `virginia` foi selecionada como ponto de partida, pois o Render
  nao disponibiliza regiao brasileira; a latencia ate o Neon Sao Paulo requer medicao.
- Render termina HTTPS na borda. `config.settings.render` confia no header
  `X-Forwarded-Proto` exclusivamente com `RENDER_SERVICE_ID`, mantendo
  `SECURE_SSL_REDIRECT` e cookies seguros. **Antes da abertura da homologacao,
  testar que o proxy sobrescreve headers falsificados pelo cliente.**
- HSTS de longa duracao e preload ficam desligados para o subdominio compartilhado
  `onrender.com`, apenas nos settings Render.
- `/health/ready/` verifica a conectividade ao Neon; `/health/live/` nao consulta banco.
- Render Free pode suspender o servidor apos 15 minutos sem requisicoes, reiniciar
  inesperadamente e perder arquivos locais. 512 MB/0,1 CPU exigem medir uso real.
- Render Free **nao oferece jobs one-off nem shell**; nenhuma migration ou seed
  e executada no Dockerfile ou no start. Migrations permanecem no workflow manual
  e controlado GitHub Actions; a conta web `gati_app` nao recebe DDL.
- `config.settings.render` desativa e-mail de forma **fail-closed**. Nao escreva
  links de redefinicao ou assinatura em disco efemero ou logs. A API HTTPS
  de e-mail faz parte de uma fase posterior.
- Uploads e importacoes permanecem bloqueados quando o ClamAV nao responde,
  pelo mecanismo fail-closed atual. **Nao usar essas funcionalidades na Render**
  antes de implementar R2 + quarentena + scanner independente.
- Nao registrar dados reais nem criar conta administrativa nesta fase.
  O endpoint Render e publico: se houver dados sinteticos, restringir o acesso
  administrativo e reforcar testes de autenticacao antes de conceder usuarios.

## Blueprint e configuracao segura

O `render.yaml` e uma proposta declarativa e deve ser lido antes de qualquer acao
no dashboard. A aplicacao ainda **nao foi criada** por esta fase.

1. Confirmar manualmente que o workspace Render esta no plano gratuito e **nao**
   habilitar upgrades, banco Render, cron pago, worker pago ou disco persistente.
2. Se futuramente autorizado, criar uma Blueprint com o repositorio do GATI,
   revisar que o servico exibido esta em `plan: free` e `autoDeployTrigger: off`.
3. Definir **somente na interface protegida da Render**, na criacao, estas variaveis
   marcadas como `sync: false`:
   - `GATI_SECRET_KEY`: gerar localmente pelo Python `secrets.token_urlsafe(48)`
     (minimo 50 caracteres); nao reutilizar credenciais do Windows.
   - `PGHOST`: hostname direto do Neon informado no painel, sem prefixo `postgresql://`.
   - `PGPASSWORD`: senha **de `gati_app`**, nao de `gati_homologacao_owner`.
4. `GATI_ALLOWED_HOSTS`, `GATI_CSRF_ORIGINS` e `GATI_PUBLIC_URL` sao
   referenciados do hostname e URL HTTPS fornecidos pelo proprio Render.
   Se usar dominio personalizado, revisar os tres valores explicitamente.
5. Conferir `PGDATABASE=gati_homologacao`, `PGUSER=gati_app`,
   `PGSSLMODE=verify-full`. O CA Mozilla fornecido por `certifi` valida o
   certificado e o hostname remoto. Nao adotar `sslmode=require`.
6. Antes do deploy futuro, verificar se o painel permite limitar despesas sem
   cadastrar pagamento, e observar limites de horas, largura de banda e builds.

**Nunca** incluir senha em mensagem, commit, issue, print, URL publica ou log.
A URL completa de migrations de owner guardada no GitHub Actions nao pertence
ao servico Render.

## Verificacoes antes de liberar a Fase 2 ou publicar o servico

1. CI: Ruff, Django check, migrations check, testes, SAST, SCA e detector de segredos.
2. CI: Docker build sem conexao ao Neon; `collectstatic` finalizado dentro da imagem.
3. CI: testes rejeitam usuario owner, host local, banco errado e modo TLS fraco.
4. No primeiro deploy autorizado: endpoint `/health/ready/` retorna 200, TLS externo,
   sem loops de redirect nem cookies inseguros. Testar request com
   `X-Forwarded-Proto: https` falsificado, exigindo que o Render sobrescreva
   o header antes de considera-lo confiavel.
5. Verificar `/entrar/`, autorizacao, 403, CSRF, headers, logout e isolamento dos
   fluxos externos, somente com dados sinteticos.
6. Medir RSS/CPU, latencia Django-Neon, frio/quente, limite de conexoes e custo.
   Testar reinicio sem perda de dados de dominio; armazenamento R2 ainda pendente.
7. O fluxo inicial nao insere dados no Neon. Quando autorizado, criar os
   grupos/status e usuario funcional por procedimento separado, sem superuser
   tecnico e sem senha em logs.

## Rollback

Se uma imagem falhar: voltar a imagem/commit anterior no Render (recurso limitado
no plano Free). O banco Neon e independente e nenhuma migration e executada
automaticamente. Nunca executar `migrate --fake`, limpar tabelas ou reduzir TLS.
Desligar o Web Service se uma falha expuser a aplicacao; investigar logs sanitizados.

## Referencias

- https://render.com/docs/free
- https://render.com/docs/blueprint-spec
- https://render.com/docs/docker
- https://render.com/docs/tls
- https://render.com/docs/health-checks
- https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header
