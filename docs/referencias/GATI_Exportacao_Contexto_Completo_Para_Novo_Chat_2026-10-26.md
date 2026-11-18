---
tipo: transferencia_de_contexto_tecnico
projeto: "DESENVOLVIMENTO - PROJETO FACUL / G.A.T.I"
titulo: "Exportação consolidada da conversa para continuidade em outro chat/conta"
versao_do_documento: "1.0"
data_da_compilacao: "2026-10-26"
idioma: "pt-BR"
formato: "Markdown UTF-8"
status_do_trabalho: "DU-F0.2-01: commit principal local criado; revisão visual registrada em seis documentos ainda não confirmados como comitados/publicados"
prioridade_na_retomada: "Verificar o estado atual do repositório antes de executar novas ações"
---

# G.A.T.I. — Exportação integral do contexto técnico e da trajetória de trabalho

> **Leia este documento integralmente ao iniciar o novo chat.** Ele concentra os objetivos, decisões, restrições, histórico, evidências técnicas, código implementado, falhas encontradas, correções, documentação e próximos passos do projeto G.A.T.I. Está organizado para preservar a continuidade sem acesso à conta anterior. **Não é uma transcrição textual literal de todas as mensagens:** é uma consolidação técnica muito detalhada do histórico disponível. A fonte de verdade para arquivos e estado corrente é sempre o repositório Git e a documentação oficial efetivamente existente.
>
> **Checkpoint crítico em 26/10/2026:** o último estado local comprovado foi `feat/f0-walking-skeleton`, com commit principal `036c4e490c6abd5a219f8140aaa644003dde40b0` e **seis documentos modificados, ainda sem confirmação de segundo commit/push**. Uma consulta somente leitura ao GitHub em 26/10/2026 retornou **404 (branch remota não encontrada)** para `feat/f0-walking-skeleton`. Não assumir publicação, PR, merge ou conclusão da DU.

## 1. Instrução de retomada para o novo ChatGPT

Atue como **engenheiro de software sênior, arquiteto de software, desenvolvedor, DevSecOps e especialista em cybersecurity**, com foco em qualidade, segurança, desempenho, escalabilidade, manutenibilidade, observabilidade, eficiência e rastreabilidade. Continue o projeto **G.A.T.I** exatamente do checkpoint descrito neste documento, conferindo o estado real antes de alterar algo. Use português brasileiro, rigor técnico e soluções incrementais. Não invente requisitos, APIs, versões, estado do Git ou resultados de testes.

Regras de trabalho assumidas pelo usuário neste histórico:

1. **Todas as alterações, criações ou remoções de arquivos do repositório devem ser entregues como comandos Windows PowerShell prontos para executar no terminal do VS Code**, sob `C:\PROJETOS\G.A.T.I`. Não pedir edição manual de arquivos. Não usar ZIP para atualizações rotineiras.
2. Comandos que escrevem arquivos devem validar branch/HEAD/estado e ocorrência exata do conteúdo antigo **antes da gravação**, preservar UTF-8 sem BOM e newline adequado, interromper em divergências, validar o resultado e, quando proporcional, oferecer rollback seguro. Não fazer alterações especulativas ou destrutivas.
3. **O usuário faz manualmente commit, push, merge e gerenciamento de branches no GitHub Desktop.** O assistente NÃO executa essas operações de escrita Git, salvo autorização nova e explícita. O uso de GitHub conectado/terminal para **leitura e diagnóstico** é permitido.
4. **Em todas as respostas técnicas, terminar com exatamente dois comandos completos de PowerShell, cada um acompanhado de breve explicação do que faz.** Não fornecer fragmentos incompletos, comandos destrutivos nem executar `git push`/`git commit` pelo terminal.
5. Cada Development Unit (DU) precisa de documentação e rastreabilidade `.md` ao longo de **SPEC → PLAN → TASKS → BASELINE → IMPLEMENTAÇÃO → TESTES → VERIFY → REVISÃO DE SEGURANÇA → REGRESSÃO → DOCUMENTAÇÃO → RASTREABILIDADE → ANÁLISE DO README → COMMIT RECOMENDADO**. `verify` automatizado **ainda não existe** na F0.2-01 e só deve ser implementado na F0.4-01.
6. **Só marcar a DU como CONCLUÍDA após** validações, publicação, releitura do conteúdo remoto, integração manual na `main`, releitura da `main` e formalização do encerramento documental. Não confundir um placeholder ou documento escrito com implementação executável.
7. Código novo/modificado recebe comentários explicativos em PT-BR por trecho/linha de lógica quando apropriado. O comentário esclarece intenção, regra e risco, sem redundância superficial. Respeitar limitações de formato.
8. Segurança desde a concepção: menor privilégio, segredos fora de Git, validação de entradas, controles OWASP adequados, supply chain, testes, observabilidade, rollback e rastreabilidade. Em achados, explicar causa raiz, impacto, pré-condições, correção, regressão e risco residual.
9. O repositório tem muitos placeholders para arquitetura futura. **Não materializar toda a arquitetura prevista de uma vez**; usar YAGNI, menor conjunto funcional e DUs sequenciais. Evitar antecipar PostgreSQL/UsuarioTI, ambientes, pytest/CI no Walking Skeleton.
10. Antes de sugerir versões atualizadas, dependências, CVEs ou advisories, verificar fontes oficiais atuais. Evitar mudar decisões técnicas já aprovadas sem uma justificativa e registro arquitetural (ADR se pertinente).

**Primeira ação no novo chat:** identificar se o usuário já fez o segundo commit e push desde o último registro. Como essa confirmação não existe neste histórico, iniciar por comandos **somente leitura** (`status`, `log`, `rev-parse`, `ls-remote`) e/ou consulta read-only ao GitHub. Não reexecutar automaticamente scripts históricos de modificação de arquivos.

## 2. Origem, objetivo e escopo inicial

- Projeto principal: **G.A.T.I** (gerenciamento do parque de ativos de TI; sistema central do projeto da faculdade).
- Projeto/conversa: **DESENVOLVIMENTO - PROJETO FACUL**.
- Repositório privado: **`Miranda-txt/G.A.T.I`**.
- Objetivo original da iniciativa: **redesenhar a documentação e o projeto para usar GitHub**, substituindo referências e práticas de ferramentas equivalentes, preservando o conteúdo pertinente e a apresentação já existente. O pedido inicial mencionava um PDF de requisitos, com a orientação de alterar **somente o necessário para a migração de ferramenta**, mantendo formatação. Não assumir neste novo chat que todos os artefatos daquela reformulação original já estejam finalizados sem conferir os arquivos.
- A continuidade evoluiu para a execução controlada da **F0 — Bootstrap e Walking Skeleton** no repositório GitHub, governada por specs, DUs, testes, revisão e rastreabilidade.
- O sistema alvo deve ser produzido gradualmente, com entrega utilizável e arquitetura sustentável, não apenas documentação ou scaffolding não funcional.

### 2.1 Fontes normativas e materiais utilizados

Reconsultar os arquivos oficiais no repositório (ou pedir que sejam anexados novamente à outra conta caso os conectores não tenham acesso). Nomes citados no histórico:

| Documento / arquivo | Papel e precedência |
|---|---|
| `GATI_Documento_Consolidado_Requisitos_Projeto_v1.0.0_GitHub.pdf` | Requisitos consolidados e referência normativa de negócio/projeto. Apareceu como documento enviado pelo usuário e no repo sob `docs/requisitos/`. |
| `GATI_Fases_Desenvolvimento.md` | Sequência F0–F13 e alocação formal das DUs; autoridade para o **momento** de implementação. |
| `GATI_Arquitetura_Pastas_Arquivos.md` | Organização/arquitetura alvo, distinção entre estrutura futura e incremento mínimo atual. |
| `GATI_Contexto_Tecnico_Diretrizes_Desenvolvimento.md` | Diretrizes técnicas complementares do projeto. |
| `GATI_Metodologia_Desenvolvimento.md` | Processo oficial do próprio GATI, no repositório em `docs/metodologia/`. |
| `metologias de desenvolvimento.md` | Diretrizes metodológicas aproveitáveis; **não** é arquitetura técnica do GATI. |
| `BoasPraticasDesenvolvimento.md` | Boas práticas de engenharia aproveitáveis; **não** substitui decisões técnicas específicas GATI. |
| `GATI_Arquitetura_Completa.zip` | Inventário de estrutura-alvo com muitos arquivos placeholders; não implementar tudo automaticamente. |
| `README.md`, `specs/F0-bootstrap/` | Status operacional, plano, tarefas, evidências, testes e rastreabilidade da F0 em andamento. |

A fonte de fases atribui:
- `DU-F0.2-01`: estruturar Django, garantir inicialização local, monólito modular, preparar separação domínio/serviços/views/DRF/templates.
- `DU-F0.2-02`: configurar **PostgreSQL 18** e criar `UsuarioTI` customizado desde a migration inicial, ORM/migrations como fonte de verdade do schema.
- `DU-F0.3-01`: organizar ambientes/settings (`GATI_ENV`), validação fail-safe de segredos, hosts e CSRF.
- `DU-F0.4-01`: estruturar pytest, pytest-django, coverage, comando `verify` e testes mínimos.
- `DU-F0.5-01`: iniciar GitHub Actions/CI.

**Decisão deliberada:** não antecipar entregas dessas DUs na F0.2-01. O documento de fases e a arquitetura oficial definem a ordem, não a mera existência de pastas placeholders.

## 3. Metodologia, arquitetura e tecnologia aprovadas

### 3.1 Princípios de engenharia

- Engenhar, não somente gerar código; entender requisitos, usuários, ameaças, trade-offs, impactos em DB/API/contratos/dependências/testes.
- Arquitetura incremental, simples, modular, testável, segura e observável. KISS/YAGNI/DRY/SOLID/Clean/Hexagonal/DDD/CQRS/event-driven são ferramentas contextuais, não obrigações dogmáticas.
- Segurança de APIs, controle de acesso por recurso, injeções/XSS/CSRF/SSRF, segredos, TLS, dependências, IaC, backup/rollback e monitoração conforme risco e fase.
- Validações baseadas em evidência real; não informar execução de testes que não ocorreram.
- README sempre deve ser avaliado em cada DU (atualizado ou registro explícito de nenhuma mudança necessária).
- Para cada DU, relacionar requisito → SPEC/PLAN/TASKS → arquivos alterados → testes/evidência → riscos/ADR → status → commit recomendado.

### 3.2 Arquitetura alvo

- **Monólito modular Django**, com separação de domínio, serviços, entrada HTTP/DRF e templates.
- ORM Django e migrations como autoridade sobre o banco.
- Evitar microserviços, Celery, Redis, brokers, K8s e camadas abstratas prematuras.
- Backend/config cuida de configuração de infraestrutura, não de regras de negócio.
- Estruturas para produção, escalabilidade, cache, filas e outras integrações entram quando a DU pertinente justificar.

### 3.3 Stack-alvo estabelecida

| Tecnologia | Linha aprovada/planejada | Situação neste checkpoint |
|---|---|---|
| Python | 3.14.x | **3.14.8** instalada/validada localmente durante F0.2-01. |
| Django | 5.2.x LTS | **5.2.17** instalada, pinned no pyproject, inicialização real validada. |
| Django REST Framework | 3.17.x | Planejado; **não instalado nesta DU**. |
| django-filter | 26.1 | Planejado; não instalado. |
| drf-spectacular | 0.30 | Planejado; não instalado. |
| Django Templates | Framework Django | Estrutura completa ainda não implementada. |
| HTMX | 2.0.x | Planejado; não instalado. |
| Bootstrap | 5.3.x | Planejado; não instalado. |
| PostgreSQL | 18.x | DU-F0.2-02, ainda não implementado. |
| .NET | 10 (componentes futuros) | Previsto para fases futuras, não presente na F0.2-01. |
| pytest / pytest-django / coverage | Ainda a formalizar | DU-F0.4-01. |
| GitHub Actions | CI futuro | DU-F0.5-01. |

A política formal de lock, ferramentas de lint/format e type checking Python não havia sido definida nas fontes técnicas revisadas; foi **deliberadamente adiada** em vez de inventar padrão não aprovado. A dependência do Django foi fixada em `5.2.17` para reprodutibilidade local mínima.

### 3.4 Regras de formatação já presentes no repo

- `.editorconfig`: `utf-8`, `LF`, newline final, trim trailing; `py` 4 espaços; `yml/yaml/json/md/html/css/js` 2; `cs` 4.
- `.gitattributes`: `* text=auto`; extensões como sh/py/yml/yaml com LF; cs/sln com CRLF. Markdown não tinha `eol` explícito; no Windows, Git alertou repetidamente “LF will be replaced by CRLF”.
- `.gitignore`: inclui `.venv/`, `venv/`, `.env` e derivados (exceto `.env.example`), caches Python, build/bin/obj, arquivos IDE, secret/cert, backups, logs, mídia/storages/quarantine, dentre outros. **`backend/.venv` foi confirmado fora do Git.**
- Para validar whitespace do Git no Windows sem bloquear com `safecrlf`, usou-se `git -c core.safecrlf=false --no-pager diff --check` (para alterações unstaged). Avisos LF→CRLF foram considerados não bloqueadores; **não** alterar `.gitattributes` apenas por estética no escopo atual.

## 4. Repositório e ambiente Windows

| Item | Valor conhecido |
|---|---|
| Repositório remoto | `Miranda-txt/G.A.T.I` (privado) |
| Branch padrão | `main` |
| Raiz local | `C:\PROJETOS\G.A.T.I` |
| Backend | `C:\PROJETOS\G.A.T.I\backend` |
| Branch local da DU | `feat/f0-walking-skeleton` |
| Git provido pelo GitHub Desktop | `C:\Users\Rafael\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe` |
| Git CLI registrado | `2.53.0.windows.4` |
| Python | `3.14.8` |
| Python local | `C:\Users\Rafael\AppData\Local\Programs\Python\Python314\python.exe` |
| OpenSSL relatado após atualização Python | `3.5.9 29 Sep 2026` |
| pip | `25.3` |
| Ambiente virtual | `backend\.venv` (ignorado) |

**Atenção:** caminhos sob `C:\Users\...`, instalações e versões podem mudar. Não pressupor que o Git ou Python de outra máquina esteja no mesmo diretório. O assistente usou o Git empacotado no GitHub Desktop porque o Git global não estava necessariamente disponível.

## 5. Linha do tempo consolidada — do começo ao último checkpoint

### Etapa A — redesenho orientado ao GitHub

1. Usuário solicitou que o projeto/documentação migrasse menções e fluxos de ferramentas equivalentes para o GitHub, preservando o projeto e a formatação do documento original.
2. Foram estabelecidas restrições para tratar GitHub como plataforma de colaboração/versionamento, com o usuário gerindo commits/push/merge pelo GitHub Desktop.
3. O trabalho passou a se orientar pelo repositório real e pela documentação GATI, com controle formal por fase/subfase/DU e análise de baseline antes de código.

### Etapa B — F0.1: inspeção, baseline e fechamento

4. A inspeção inicial do repositório observou **629 entradas aproximadamente**, muitas delas apenas placeholders. Inicialmente não havia aplicação Django executável nem suíte de testes, migrations ou `scripts/verify.py` funcional (o arquivo `scripts/verify.py` era somente placeholder). **Não tratar placeholders como implementação.**
5. Base histórica antiga: SHA `d4e13500ce5fb36e4929849dfd98faea438424ad`.
6. `DU-F0.1-01` — inspeção: concluída.
7. `DU-F0.1-02` — baseline/remediação: concluída e rastreada com branch `chore/f0-governanca-baseline` e commits `6d832e...`, `e9b973...`; PR **#1** integrada à `main` sob merge `7963fdc...`.
8. Fechamento documental em branch `docs/f0-encerra-baseline`, commit `a18119a5b43698d31812250a0e05dd6101ed5696`; PR **#2** integrada à main sob merge `4340fdcfaad786c9f129cac077f9eefa8f00747f` (`docs(f0): encerra baseline e libera walking skeleton`).
9. `main`/`origin/main` encontravam-se nesse SHA `4340fdc...` quando começou o Walking Skeleton. Não afirmar que ainda é o HEAD remoto atual sem consultar.

### Etapa C — abertura e baseline DU-F0.2-01

10. Usuário criou manualmente a branch **`feat/f0-walking-skeleton`** pelo GitHub Desktop, baseada em `4340fdc...`.
11. Foi criado o documento `specs/F0-bootstrap/DU-F0.2-01_Walking_Skeleton_Django.md` com baseline, decisões, critérios de teste/aceite, riscos e evolução das evidências.
12. A baseline local tinha Python **3.14.2**; atualização controlada para Python **3.14.8** por instalador oficial `python.org`, verificando SHA-256 e assinatura Authenticode. Depois, verificaram-se Python/OpenSSL/pip.
13. Foi criado o ambiente virtual `backend/.venv`; verificado que seria ignorado pelo Git.
14. No `backend/pyproject.toml`, a dependência mínima foi definida em `[dependency-groups] runtime = ["Django==5.2.17"]`; instalação feita via `pip install --group runtime`.

### Etapa D — implementação do Walking Skeleton

15. Foram convertidos seis placeholders técnicos em código real: `backend/manage.py`, `backend/config/settings/base.py`, `backend/config/urls.py`, `backend/config/wsgi.py`, `backend/config/asgi.py`, `backend/pyproject.toml`.
16. Arquitetura intencionalmente mínima: `DEBUG=False`, `ALLOWED_HOSTS` somente loopback, `INSTALLED_APPS=[]`, `MIDDLEWARE=[]`, `TEMPLATES=[]`, `DATABASES={}`, rota GET `/` com texto simples; WSGI/ASGI carregam settings `config.settings.base`.
17. `pip check`, `py_compile`, `manage.py check`, carregamento WSGI/ASGI e smoke test HTTP real passaram. O servidor foi iniciado em `127.0.0.1:8765 --noreload`, GET `/` retornou HTTP 200 e payload lógico `GATI Walking Skeleton`; processo temporário foi encerrado.
18. Primeiro smoke test encontrou payload com sequência literal PowerShell `` `n `` persistida incorretamente. Foi corrigido para escape Python `\n` em `HttpResponse`, regressão repetida e aprovada.
19. Revisão de segurança concluiu ausência de bloqueadores críticos/altos/médios nesta DU. Risco residual explicitamente controlado: `SECRET_KEY` estático **público e não secreto** apenas para bootstrap; deve ser substituído antes de qualquer uso criptográfico/produção, na F0.3-01. Sem sessões, auth ou apps de assinatura em funcionamento.
20. Verificação delimitou escopo técnico: não antecipou PostgreSQL, psycopg, DRF, Celery, Redis, pytest, coverage ou CI. `verify` ainda não existe.

### Etapa E — documentação, revisão e correções

21. Foram atualizados README, `spec.md`, `plan.md`, `tasks.md`, `test-plan.md`, `traceability.md` e a DU individual. Total do **primeiro incremento: 13 artefatos** (6 backend, 6 documentos rastreados e 1 documento novo da DU).
22. Revisão final identificou caractere de controle **vertical tab** (`U+000B`) gerado pelo PowerShell quando o backtick Markdown de `` `verify` `` em string expansível foi interpretado como escape `` `v ``. Corrigido em `test-plan.md`, validado sem caracteres de controle C0 inesperados.
23. Outro detalhe: Markdown da regressão aparecia como `` `GATI Walking Skeleton``n` `` (code span ambíguo). Foi corrigido para **code span com delimitadores duplos**, exibido como `` ``GATI Walking Skeleton`n`` `` nos dois documentos de teste/DU. Validado com `Select-String`, `git diff --check` e checagem de caracteres de controle.
24. Os 13 arquivos foram revisados pela pessoa usuária no GitHub Desktop. A pessoa informou: **“revisao visual feita”**; a revisão foi posteriormente registrada como aprovada sem divergências reportadas.
25. Ao tentar registrar a aprovação, uma checagem de `git diff --name-only` encontrou **0** arquivos e o script abortou antes da gravação. O diagnóstico inicial de que os arquivos estariam apenas staged foi refutado por `git status --porcelain`, `git diff --cached`, `git diff` e `ls-files --others`: todos retornaram zero. A explicação correta: **o usuário já havia realizado o commit local do incremento principal**.
26. `git log` revelou o commit principal local `036c4e490c6abd5a219f8140aaa644003dde40b0`, mensagem **`feat(f0): implementa walking skeleton django`**, criado em **2026-10-04 20:59:48 -0300**. `git diff 4340fdc..HEAD` confirmou exatamente 13 arquivos alterados, **463 inserções, 34 deleções**. O working tree estava limpo naquele momento.
27. Um primeiro script para registrar o estado pós-commit falhou **na análise sintática** (ParserError): backticks de Markdown dentro de strings PowerShell com aspas duplas escaparam caracteres de fechamento, produzindo token inesperado na linha `**Mensagem:**`. Por ser ParserError, nenhuma modificação do script ocorreu.
28. O script seguinte foi refeito com **aspas simples nas strings Markdown** e validação exata de branch/HEAD/working tree; executou com sucesso: **“REVISÃO VISUAL REGISTRADA COM SUCESSO. COMMIT PRINCIPAL 036c4e4 PRESERVADO.”**
29. A validação posterior confirmou **exatamente 6 arquivos modificados**, sem outros: README; `DU-F0.2-01_Walking_Skeleton_Django.md`; `plan.md`; `spec.md`; `tasks.md`; `traceability.md`. `git diff --check` passou. O diff-stat documental complementar foi **32 inserções e 11 deleções** (6 arquivos).
30. O assistente recomendou o segundo commit **`docs(f0): registra revisão visual do walking skeleton`** seguido de **Push origin** manual no GitHub Desktop e instruiu **não fazer merge** antes de reler a branch publicada. O usuário ainda **não devolveu os resultados** desses dois passos.
31. Em **26/10/2026**, uma consulta somente leitura ao endpoint de branch no GitHub retornou **404 Branch not found** para `feat/f0-walking-skeleton`. Portanto, **não há evidência de push/branch publicada** no momento desta exportação; o estado remoto poderia mudar depois e deve ser rechecado.

## 6. Código do backend implementado no commit principal

Esses trechos são a implementação revisada durante a conversa. **Compare com o repositório**; não sobrescrever cegamente.

### `backend/pyproject.toml`

```toml
# Dependências mínimas do Walking Skeleton Django.
# A política de lock será definida somente quando houver necessidade formal.

[dependency-groups]
runtime = [
    "Django==5.2.17",
]
```

### `backend/manage.py`

```python
"""Ponto de entrada dos comandos de gerenciamento do backend GATI."""

import os
import sys


def main() -> None:
    # Define explicitamente o módulo mínimo de settings desta DU.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

    # Importa o executor somente depois que o módulo de settings foi definido.
    from django.core.management import execute_from_command_line

    # Delega ao Django os argumentos recebidos pelo processo atual.
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    # Executa o bootstrap apenas quando este arquivo for chamado diretamente.
    main()
```

### `backend/config/settings/base.py`

```python
"""Configuração mínima comum do Walking Skeleton Django."""

# Usa um valor público e não secreto apenas para permitir o bootstrap desta DU.
SECRET_KEY = "django-insecure-gati-f0-walking-skeleton-non-secret-placeholder"

# Mantém debug desabilitado como padrão seguro mesmo durante o skeleton.
DEBUG = False

# Restringe o servidor inicial aos endereços locais previstos para desenvolvimento.
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Não registra apps de domínio antes das respectivas Development Units.
INSTALLED_APPS = []

# Não adiciona middleware antecipadamente antes dos requisitos que o justificam.
MIDDLEWARE = []

# Direciona a resolução HTTP para o módulo mínimo de URLs.
ROOT_URLCONF = "config.urls"

# Não configura templates antes de existir uma interface que os utilize.
TEMPLATES = []

# Expõe o ponto de entrada WSGI para compatibilidade com o deploy futuro.
WSGI_APPLICATION = "config.wsgi.application"

# Expõe o ponto de entrada ASGI sem introduzir servidor ASGI adicional.
ASGI_APPLICATION = "config.asgi.application"

# Mantém o banco deliberadamente não configurado até a DU-F0.2-02.
DATABASES = {}
```

### `backend/config/urls.py`

```python
"""Rotas mínimas do Walking Skeleton Django."""

from django.http import HttpRequest, HttpResponse
from django.urls import path


def walking_skeleton(request: HttpRequest) -> HttpResponse:
    # Retorna somente uma evidência técnica de que o ciclo HTTP está operacional.
    return HttpResponse("GATI Walking Skeleton\n", content_type="text/plain; charset=utf-8")


# Publica apenas a rota técnica mínima necessária à validação desta DU.
urlpatterns = [path("", walking_skeleton, name="walking-skeleton")]
```

### `backend/config/wsgi.py`

```python
"""Ponto de entrada WSGI do backend GATI."""

import os

from django.core.wsgi import get_wsgi_application

# Define os settings antes da construção da aplicação WSGI.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

# Constrói a aplicação WSGI consumida futuramente pelo servidor de aplicação.
application = get_wsgi_application()
```

### `backend/config/asgi.py`

```python
"""Ponto de entrada ASGI do backend GATI."""

import os

from django.core.asgi import get_asgi_application

# Define os settings antes da construção da aplicação ASGI.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

# Constrói a aplicação ASGI mantendo compatibilidade com evolução futura.
application = get_asgi_application()
```

### Setup/execução local documentada

Windows PowerShell, a partir da raiz do repositório:

```powershell
Set-Location 'C:\PROJETOS\G.A.T.I\backend'
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --group runtime
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Rota mínima `GET http://127.0.0.1:8000/`, status esperado **200**, corpo lógico **`GATI Walking Skeleton`**. A instância de desenvolvimento deve ficar restrita a loopback. Não há garantias de configuração para produção.

## 7. Evidências de testes e revisão de segurança

| Validação | Resultado histórico | Observação |
|---|---|---|
| Python 3.14.8 | Aprovado | Atualizado de 3.14.2 após validação de pacote oficial. |
| Django 5.2.17 | Aprovado | Pinned em `pyproject.toml`, instalado via grupo runtime. |
| `pip check` | Aprovado | Sem dependências quebradas. |
| `py_compile` | Aprovado | Módulos Python do Walking Skeleton. |
| `manage.py check` | Aprovado | `System check identified no issues (0 silenced)`. |
| Carregamento WSGI | Aprovado | `WSGIHandler`. |
| Carregamento ASGI | Aprovado | `ASGIHandler`. |
| `runserver --noreload` | Aprovado | Bind local em `127.0.0.1:8765` para smoke test. |
| HTTP GET `/` | Aprovado após correção | 200 e corpo `GATI Walking Skeleton` com newline Python correto. |
| Encerramento do processo temporário | Confirmado | Sem servidor de teste deixado em execução. |
| `git diff --check` | Aprovado | Usada opção `core.safecrlf=false` no Windows. |
| Ignorar `.venv` | Aprovado | Ambiente não versionado. |
| Scan delimitado do backend | Aprovado | Não houve antecipação das dependências/infra de DUs futuras. |
| Scan de segredo/credencial real | Aprovado | `SECRET_KEY` presente é valor placeholder **público**, não segredo operacional. |
| Correção vertical tab Markdown | Aprovado | Linha final do `test-plan.md` com `` `verify` ``. |
| Correção de code span literal `` `n `` | Aprovado | Corrigido nos dois documentos da regressão. |
| Verificação de 13 artefatos | Aprovado | Primeiro commit principal contém exatamente 13 arquivos. |
| Revisão visual no GitHub Desktop | Usuário informou realizada | Formalizada no incremento documental de 6 arquivos. |
| Incremento documental de 6 arquivos | Aprovado | Testes estruturais executados, **ainda sem prova de segundo commit**. |
| CI/pytest/coverage/`verify` | **Não executados/não implementados** | Planejados formalmente para F0.4/F0.5. |

### 7.1 Riscos e limitações conscientes

- `SECRET_KEY` literal, estática e intencionalmente **não secreta** deve ser substituída por configuração segura antes de usar autenticação, sessões assinadas, funcionalidades criptográficas e qualquer ambiente não local. Tratamento planejado na DU-F0.3-01. **Não promover este settings/base para produção.**
- `DATABASES={}` e ausência de `UsuarioTI` são **esperados** em F0.2-01, não falha; resolver na F0.2-02 com ORM/migration inicial.
- `DEBUG=False`, hosts de loopback e apps/middleware vazios atendem ao skeleton mínimo, mas **não representam aplicação pronta para operação**.
- Ausência de lock formal para dependências está registrada como decisão temporária; reavaliar em DU apropriada, sem inventar configuração.
- Avisos Git de conversão LF/CRLF em Markdown: risco baixo de higiene, sem falha de whitespace; não ampliar escopo atual por isso.
- Testes atuais são dirigidos/manualizados; automação pytest/coverage/verify é posterior. Não afirmar cobertura de regressão contínua.
- Não criar migrations, banco, DRF, usuários ou fluxos de negócio fora das respectivas DUs.

## 8. Artefatos modificados e documentação de governança

### 8.1 Primeiro commit principal — 13 arquivos

SHA local: `036c4e490c6abd5a219f8140aaa644003dde40b0`.

```text
M  README.md
M  backend/config/asgi.py
M  backend/config/settings/base.py
M  backend/config/urls.py
M  backend/config/wsgi.py
M  backend/manage.py
M  backend/pyproject.toml
A  specs/F0-bootstrap/DU-F0.2-01_Walking_Skeleton_Django.md
M  specs/F0-bootstrap/plan.md
M  specs/F0-bootstrap/spec.md
M  specs/F0-bootstrap/tasks.md
M  specs/F0-bootstrap/test-plan.md
M  specs/F0-bootstrap/traceability.md
```

Comparação entre SHA base `4340fdc...` e esse HEAD: **13 arquivos, +463/-34**. Mensagem `feat(f0): implementa walking skeleton django`.

Registros:
- `README.md`: agora explica Python/Django, venv, instalação, execução, endpoint, testes dirigidos e DUs pendentes.
- `spec.md`: status da DU evoluiu; critério “Django inicia corretamente” marcado `[x]` na F0. Outros critérios F0 pendentes.
- `plan.md`: Django local/WSGI/ASGI/HTTP 200 e limitações de escopo.
- `tasks.md`: tarefas de engenharia, revisão e publicação.
- `test-plan.md`: evidências dos testes dirigidos e duas regressões relacionadas ao payload/PowerShell.
- `traceability.md`: liga DU ao código e plano de teste.
- `DU-F0.2-01_Walking_Skeleton_Django.md`: registro técnico e de segurança detalhado. Em seu primeiro commit tinha estado “IMPLEMENTAÇÃO VALIDADA NA BRANCH — AGUARDANDO REVISÃO FINAL”, pois a documentação de aprovação humana ainda não fora comitada.

### 8.2 Incremento documental complementar — 6 arquivos, validado e ainda com estado de commit não confirmado

Última saída enviada pelo usuário (**após o script de escrita e sua validação**) mostrou:

```text
 M README.md
 M specs/F0-bootstrap/DU-F0.2-01_Walking_Skeleton_Django.md
 M specs/F0-bootstrap/plan.md
 M specs/F0-bootstrap/spec.md
 M specs/F0-bootstrap/tasks.md
 M specs/F0-bootstrap/traceability.md
```

Diff-stat desse incremento:

```text
README.md                                         |  7 +++----
DU-F0.2-01_Walking_Skeleton_Django.md             | 24 ++++++++++++++++++++--
plan.md                                           |  2 +-
spec.md                                           |  2 +-
tasks.md                                          |  6 ++++--
traceability.md                                   |  2 +-
6 files changed, 32 insertions(+), 11 deletions(-)
```

Após o segundo script, o usuário recebeu: **`INCREMENTO DOCUMENTAL VALIDADO`**; o assistente recomendou commit `docs(f0): registra revisão visual do walking skeleton` e instrução de Push origin manual.

Esse incremento:
- altera status em README/SPEC/PLAN/traceability e documento da DU para **`REVISÃO VISUAL APROVADA — AGUARDANDO COMMIT DOCUMENTAL COMPLEMENTAR E PUSH`**;
- marca a revisão visual em `tasks.md` como `[x]` **na seção da DU-F0.2-01** (havia uma linha semelhante já `[x]` na F0.1, que não deve ser confundida);
- registra em `tasks.md` o commit principal local `036c4e4`, adiciona tarefa de commit documental complementar e separa push como pendente;
- adiciona à DU a seção **`## 15. Revisão visual e estado do commit`**, com aprovação sem divergências reportadas, SHA, justificativa de preservar o commit principal e necessidade de publicação/releitura/merge;
- não altera os seis arquivos técnicos Django do primeiro commit;
- não encerra formalmente a DU.

**Ponto de atenção:** depois que o segundo commit e push efetivamente acontecerem, as linhas que dizem “aguardando commit documental complementar e push” ficarão historicamente defasadas até a atualização documental de fechamento. Isso deve ser tratado controladamente **após validar o remoto** (sem fazer commits repetitivos cegos). A sequência e branch de fechamento podem seguir o precedente F0.1, se necessário.

## 9. Incidentes técnicos e aprendizados — não repetir

### 9.1 Git com pager `less` indisponível

- `git diff --name-only` e `git branch -vv` acionaram pager e falharam com: `error: cannot spawn less: No such file or directory`.
- **Regra:** usar `& $GitExe --no-pager diff ...`, `& $GitExe --no-pager log ...`, e, quando necessário, `$env:GIT_PAGER='cat'` somente para leituras. Verificar `$LASTEXITCODE` imediatamente após cada comando de Git antes de interpretar dados.

### 9.2 Avisos LF→CRLF

- Múltiplos Markdown exibiram `warning: ... LF will be replaced by CRLF`.
- `git -c core.safecrlf=false --no-pager diff --check` passou. Avisos são não bloqueadores nesta etapa. Não adulterar `.gitattributes` sem análise de impacto e DU apropriada.

### 9.3 Escapes PowerShell e texto Python/Markdown

- Em string PowerShell, backticks são escapes; `` `n `` e `` `v `` podem gerar newline ou vertical tab, corrompendo strings Markdown/Python. O HTTP inicial teve um literal `` `n `` errado e o registro Markdown de `verify` teve vertical tab.
- **Regra:** conteúdo que contém Markdown com backticks deve preferir **aspas simples** no PowerShell; para trechos com aspas simples internas, dobrá-las ou usar outras estratégias seguras. Evitar strings expansíveis com code spans.
- Ao representar literalmente `` `n `` em code spans Markdown, utilizar delimitação dupla: `` ``GATI Walking Skeleton`n`` ``.
- Após scripts de escrita, verificar caracteres de controle C0 inesperados: regex `'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]'`; permitir TAB/LF/CR quando esperados.

### 9.4 PowerShell scripts extensos

- O PSReadLine apresentou erros de renderização ao colar comandos enormes, especialmente com muitos caracteres especiais. Preferir scripts compactos, etapas seguras e mensagens de erro explícitas.
- Um script histórico usou indevidamente escopo `$script:Content` e retornou conteúdo vazio; evitar funções/escopo confuso. Validar leitura e contagem antes de gravar.
- Não produzir falso positivo de sucesso após falha em Git: sempre conferir `$LASTEXITCODE` e evitar executar prints “SUCESSO” se uma etapa intermediária falhou.
- Um `ParserError` por aspas duplas e backticks dentro do texto `**Mensagem:**` abortou o script **antes** de alterar arquivos. A correção posterior usou aspas simples e funcionou.

### 9.5 Diferença entre working tree, staging e HEAD

- O primeiro script pós-revisão esperava 13 arquivos em `git diff`; retornou zero e abortou. A hipótese temporária de staging foi testada e descartada: `status`, staged, unstaged e untracked eram zero. Os arquivos tinham sido **comitados**.
- Antes de decidir entre patch de arquivos ou verificação de commit, consultar **branch, HEAD, `git status --porcelain`, `git diff`, `git diff --cached`, `git ls-files --others` e log**.
- Nunca fazer `git reset`, `amend` ou rebase apenas para forçar scripts históricos a encontrarem estados antigos.

### 9.6 Scans escopados e falsos positivos

- Um scan documental detectou referências a pytest/coverage em textos sobre fases futuras. Isso não significa dependências antecipadas. O scan corrigido restringiu a busca ao diff do backend e passou. Contextualizar escopo e critérios dos scans.

## 10. Estados por Development Unit

| DU | Título/responsabilidade | Última situação confiável |
|---|---|---|
| F0.1-01 | Inspeção do baseline/repo | **CONCLUÍDA**, integrada à main no encerramento F0.1. |
| F0.1-02 | Governança/baseline/remediação | **CONCLUÍDA**, PR #1 e #2 integradas. |
| F0.2-01 | Walking Skeleton Django | **Implementação/testes/revisão aprovados; commit principal criado localmente; incremento documental complementar validado, sem confirmação de commit/push; DU NÃO CONCLUÍDA.** |
| F0.2-02 | PostgreSQL 18 e UsuarioTI | **NÃO INICIADA**. |
| F0.3-01 | Ambientes, secrets/settings, fail-safe | **NÃO INICIADA**. |
| F0.4-01 | pytest, coverage, verify | **NÃO INICIADA**. |
| F0.5-01 | GitHub Actions/CI | **NÃO INICIADA**. |

As fases F1–F13 são evolução futura e não devem ser executadas antecipadamente. **A próxima DU só pode começar após encerramento formal da DU-F0.2-01.**

## 11. Estado Git exato no último checkpoint documentado

Saídas comprovadas pelo usuário antes dos seis arquivos documentais:

```text
BRANCH: feat/f0-walking-skeleton
HEAD: 036c4e490c6abd5a219f8140aaa644003dde40b0
commit: feat(f0): implementa walking skeleton django
main/origin/main observado: 4340fdcfaad786c9f129cac077f9eefa8f00747f
working tree naquele instante: limpo
commits da branch acima de origin/main: 1
```

Saídas comprovadas pelo usuário **depois** do script documental bem-sucedido:

```text
REVISÃO VISUAL REGISTRADA COM SUCESSO.
COMMIT PRINCIPAL 036c4e4 PRESERVADO.

STATUS:
 M README.md
 M specs/F0-bootstrap/DU-F0.2-01_Walking_Skeleton_Django.md
 M specs/F0-bootstrap/plan.md
 M specs/F0-bootstrap/spec.md
 M specs/F0-bootstrap/tasks.md
 M specs/F0-bootstrap/traceability.md

6 files changed, 32 insertions(+), 11 deletions(-)
INCREMENTO DOCUMENTAL VALIDADO.
COMMIT RECOMENDADO:
docs(f0): registra revisão visual do walking skeleton
```

Verificação remota **somente leitura** feita durante a compilação deste documento em **2026-10-26**:

```text
GET https://api.github.com/repos/Miranda-txt/G.A.T.I/branches/feat/f0-walking-skeleton
HTTP 404 — Branch not found
```

**Conclusão sobre o checkpoint:** não há evidência de que o usuário tenha executado o segundo commit ou push. O GitHub remoto não mostrou a branch na verificação efetuada; reconsultar antes de qualquer ação, pois o estado pode mudar entre chats.

## 12. Plano de retomada: próximos passos seguros e exatos

### Passo 0 — diagnosticar, sem alterar nada

No novo chat, começar por verificar HEAD/branch/status locais. Exemplo de comando PowerShell **somente leitura**:

```powershell
& {
    Set-Location -LiteralPath 'C:\PROJETOS\G.A.T.I'
    $GitExe = 'C:\Users\Rafael\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe'
    & $GitExe status --short --branch
    & $GitExe rev-parse HEAD
    & $GitExe --no-pager log -4 --oneline --decorate
    & $GitExe -c core.safecrlf=false --no-pager diff --stat
    & $GitExe -c core.safecrlf=false --no-pager diff --check
}
```

Verificação remota **sem escrever em Git local**:

```powershell
& {
    Set-Location -LiteralPath 'C:\PROJETOS\G.A.T.I'
    $GitExe = 'C:\Users\Rafael\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe'
    & $GitExe ls-remote --heads origin 'refs/heads/feat/f0-walking-skeleton'
    if ($LASTEXITCODE -ne 0) { throw 'Falha na consulta do remoto.' }
    & $GitExe --no-pager log --oneline '4340fdcfaad786c9f129cac077f9eefa8f00747f..HEAD'
}
```

Os comandos são **diagnósticos**, não comprovam automaticamente todos os requisitos de fechamento. Se a branch remota não existir, `ls-remote` pode retornar vazio com exit code 0: isso significa **sem ref encontrada**, não sucesso de publicação. Não executar `push` pelo terminal.

### Passo 1 — se ainda houver exatamente os seis documentos modificados

1. Conferir que a branch continua `feat/f0-walking-skeleton` e que o commit `036c4e4` é ancestral/local.
2. Comparar exatamente os seis arquivos permitidos e revisar o diff no GitHub Desktop. Não repetir ou reescrever o commit principal.
3. Usuário cria manualmente no GitHub Desktop o **segundo commit** com a mensagem:

   `docs(f0): registra revisão visual do walking skeleton`

4. Usuário aciona manualmente **Push origin** da branch.
5. **Não fazer merge ainda**.

### Passo 2 — depois de segundo commit e push confirmados

1. Verificar `git status --porcelain` vazio e `git log` incluindo **dois commits da DU**, com os temas `feat(f0)` e `docs(f0)`.
2. Verificar que o **SHA remoto de `refs/heads/feat/f0-walking-skeleton` coincide com o HEAD local** via `git ls-remote` (somente leitura).
3. Reler **diretamente do GitHub** a branch publicada usando conector read-only: SHA, commits, 13 arquivos do primeiro commit, seis documentos do complemento, ausência de arquivos secretos e integridade dos registros.
4. Comparar branch com `main` remota e checar divergências/conflitos antes de PR. A versão de `main` poderá ter mudado desde `4340fdc...`; não presumir estabilidade.
5. Confirmar que documentação/README apontam estado apropriado para pré-merge e que nenhuma DU posterior foi antecipada. Se precisar sincronizar status com evidência remota, fazer mudança mínima em `.md` e commit manual adicional com rastreabilidade; evitar ciclo interminável de commits documentais.
6. Só então orientar criação/revisão e merge de PR **manual**.

### Passo 3 — após merge manual

1. Consultar GitHub `main` novamente e conferir arquivos/histórico/commit de merge efetivos.
2. Confirmar integridade do Walking Skeleton na main e repetir testes proporcionais ao risco se o conteúdo tiver mudado.
3. Encerrar formalmente `DU-F0.2-01` nas fontes `.md` relevantes (SPEC/PLAN/TASKS/TRACEABILITY/README/DU), seguindo governança e eventual branch de encerramento documental, como foi feito na F0.1.
4. Integrar manualmente documentação de encerramento, reler a main e **somente então** declarar `DU-F0.2-01: CONCLUÍDA` e liberar `DU-F0.2-02`.

### Passo 4 — próximo incremento futuro, não iniciado

`DU-F0.2-02 — PostgreSQL 18 + UsuarioTI`. Antes de codar, reler fontes, definir SPEC/PLAN/TASKS/baseline, impactos no banco, migração inicial do custom user model, instalação/configuração local, segredos, testes, rollback e observabilidade. **Não começar até concluir a DU-F0.2-01.**

## 13. Checklist de continuidade para evitar perda de contexto

- [x] Objetivo original de migração para GitHub documentado neste handoff.
- [x] Regras de GitHub Desktop/manualidade preservadas.
- [x] Ambiente Windows/PowerShell e repositório identificados.
- [x] Fontes normativas e prioridades registradas.
- [x] Ordem das DUs de F0 e stack-alvo registrada.
- [x] Histórico F0.1, PRs e SHAs conhecidos registrado.
- [x] Código atual do Walking Skeleton transcrito.
- [x] Testes executados e limitações de segurança registrados.
- [x] Incidentes PowerShell/Git e correções registrados.
- [x] Primeiros 13 arquivos comitados e seis documentos de complemento identificados.
- [x] Segundo commit recomendado registrado.
- [ ] **Confirmar se o segundo commit foi executado após a última conversa.**
- [ ] **Confirmar se Push origin foi executado e se a branch remota existe agora.**
- [ ] Reler a branch publicada e comparar com `main`.
- [ ] Fazer PR/merge manual depois da revisão remota.
- [ ] Reler a main após merge e formalizar fechamento da DU.
- [ ] Iniciar F0.2-02 somente após a DU anterior estar formalmente encerrada.

## 14. Observações sobre confiabilidade desta exportação

**Fatos diretamente observados no histórico disponível:** saídas dos comandos compartilhadas pelo usuário, commits/SHAs e diff-stat, nomes dos arquivos, código técnico revisado, status, validações relatadas, falhas diagnosticadas, correções aprovadas e resposta 404 do GitHub na data da exportação.

**Informações sintetizadas do contexto anterior:** detalhes da etapa de baseline F0.1, parte da seleção da stack/arquitetura, diretrizes metodológicas e sequência do início da DU. Esses pontos foram consolidados a partir do histórico resumido disponível, mas **não reproduzem palavra por palavra todas as mensagens antigas**.

**Não incluído:** conteúdo integral dos PDFs/MD oficiais, histórico literal de todos os comandos longos e arquivos reais do repositório, tokens, credenciais, cópias de um checkout local, ou confirmação de ações após a última resposta do usuário. O arquivo não altera nem exporta o repositório Git: ele é um **manual de transferência de contexto**, não backup de código.

**Para máxima fidelidade no outro chat:** anexar este Markdown e, quando disponíveis, o PDF de requisitos, o `GATI_Fases_Desenvolvimento.md`, o `GATI_Arquitetura_Pastas_Arquivos.md`, a metodologia e os documentos atuais da pasta `specs/F0-bootstrap`; ou conectar a outra conta ao repositório com permissão somente leitura para diagnóstico. Jamais compartilhar arquivos `.env`, segredos ou credenciais.

## 15. Mensagem pronta para colar no novo chat

> Estou continuando o projeto G.A.T.I de uma conversa anterior, com contexto completo no arquivo `GATI_Exportacao_Contexto_Completo_Para_Novo_Chat_2026-10-26.md`. Leia o arquivo inteiro antes de responder. Mantenha as regras: atuar como engenheiro/arquiteto/DevSecOps/cybersecurity; alterações locais somente via comandos seguros Windows PowerShell no VS Code; commits, pushes, branches e merges exclusivamente manuais no GitHub Desktop; documentação e rastreabilidade por DU; testar e revisar antes de declarar conclusão; terminar as respostas com dois comandos completos e suas descrições curtas. Nosso último checkpoint é `feat/f0-walking-skeleton`, commit principal local `036c4e4`, mais seis documentos com revisão visual registrada e segundo commit/push ainda não comprovados. Primeiro quero uma checagem somente leitura do estado local e remoto; não avance para a DU-F0.2-02 e não faça operações destrutivas.

---

**Fim do documento de exportação.**
