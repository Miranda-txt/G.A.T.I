# GATI — Arquitetura de Pastas e Arquivos

**Projeto:** Sistema de Gerenciamento de Ativos de TI — GATI  
**Documento:** Arquitetura de Pastas e Arquivos do Repositório  
**Base:** Documento Consolidado de Requisitos e Projeto v1.0.0 + Plano de Fases de Desenvolvimento do GATI  
**Status:** arquitetura estrutural proposta para implementação  
**Escopo:** MVP

> Esta arquitetura organiza fisicamente o código e os artefatos do repositório sem alterar os requisitos, regras de negócio, stack ou decisões arquiteturais já aprovadas.
>
> Os nomes de diretórios e arquivos que não foram definidos explicitamente na baseline são convenções de implementação propostas. Se o repositório real já possuir uma convenção equivalente e coerente, ela deverá ser avaliada antes de qualquer reorganização.

---

# 1. Objetivos da arquitetura do repositório

A estrutura deve garantir:

- monorepo privado no GitHub;
- Django monolítico modular como aplicação principal;
- Django Templates + HTMX + Bootstrap no mesmo backend, sem SPA separada;
- Django REST Framework para a API `/api/v1/`;
- uma camada de serviços reutilizada por Views HTML e endpoints DRF;
- PostgreSQL como banco oficial;
- migrations Django como única fonte oficial de evolução do schema;
- Endpoint Windows em C#/.NET no mesmo monorepo;
- GATI Driver Executor separado do serviço principal do Endpoint;
- scraping como módulo do domínio de drivers, com execução isolável;
- infraestrutura e configurações operacionais versionadas;
- especificações, testes, segurança e rastreabilidade próximos do desenvolvimento;
- segregação clara entre código-fonte, configuração não sensível, secrets e dados persistentes;
- ausência de microsserviços, Kubernetes, Celery, Redis ou broker geral no MVP;
- facilidade para testes unitários, integração, contrato, E2E, segurança, recuperação e Windows Lab.

---

# 2. Arquitetura de alto nível do monorepo

Estrutura alvo:

```text
gati/
├── .github/
├── backend/
├── endpoint/
├── infra/
├── lab/
├── specs/
├── docs/
├── scripts/
├── .editorconfig
├── .gitignore
├── .gitattributes
├── README.md
├── GATI_Fases_Desenvolvimento.md
└── GATI_Arquitetura_Pastas_Arquivos.md
```

Responsabilidades:

| Diretório | Responsabilidade |
|---|---|
| `.github/` | CI/CD e automações do GitHub |
| `backend/` | Django, DRF, Templates, HTMX, domínio, banco e integrações server-side |
| `endpoint/` | Agente Windows e Driver Executor em C#/.NET |
| `infra/` | Docker, NGINX, systemd, observabilidade, backup e deploy |
| `lab/` | Windows Lab descartável e cenários privilegiados |
| `specs/` | SPEC, plano, tasks, testes e rastreabilidade por Development Unit/feature |
| `docs/` | arquitetura operacional, ADRs, segurança, LGPD e runbooks |
| `scripts/` | comandos reproduzíveis do repositório |
| `README.md` | setup, execução, validação e visão operacional do repositório |

---

# 3. Estrutura completa proposta

```text
gati/
│
├── .github/
│   └── workflows/
│       ├── ci-backend.yml
│       ├── ci-endpoint.yml
│       ├── security.yml
│       ├── build-images.yml
│       └── release.yml
│
├── backend/
│   ├── manage.py
│   ├── pyproject.toml
│   ├── .env.example
│   ├── Dockerfile
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   ├── env.py
│   │   └── settings/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── development.py
│   │       ├── test.py
│   │       ├── staging.py
│   │       └── production.py
│   │
│   ├── gati/
│   │   ├── __init__.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── urls.py
│   │   │   ├── pagination.py
│   │   │   ├── versioning.py
│   │   │   ├── exceptions.py
│   │   │   └── problem_details.py
│   │   │
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── constants.py
│   │   │   ├── validators.py
│   │   │   ├── hashing.py
│   │   │   ├── tokens.py
│   │   │   ├── time.py
│   │   │   ├── db.py
│   │   │   └── clamav.py
│   │   │
│   │   ├── observability/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── metrics.py
│   │   │   ├── logging.py
│   │   │   └── urls.py
│   │   │
│   │   ├── integrations/
│   │   │   ├── __init__.py
│   │   │   └── email/
│   │   │       ├── __init__.py
│   │   │       ├── backend.py
│   │   │       ├── messages.py
│   │   │       └── templates.py
│   │   │
│   │   └── apps/
│   │       ├── usuarios/
│   │       ├── auditoria/
│   │       ├── cadastros/
│   │       ├── pessoas/
│   │       ├── ativos/
│   │       ├── manutencoes/
│   │       ├── arquivos/
│   │       ├── importacoes/
│   │       ├── termos/
│   │       ├── movimentacoes/
│   │       ├── dashboard/
│   │       ├── endpoints/
│   │       └── drivers/
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── components/
│   │   └── errors/
│   │
│   ├── static/
│   │   └── gati/
│   │       ├── css/
│   │       ├── js/
│   │       └── img/
│   │
│   └── tests/
│       ├── api/
│       ├── contract/
│       ├── integration/
│       ├── e2e/
│       ├── security/
│       ├── performance/
│       ├── recovery/
│       └── fixtures/
│
├── endpoint/
│   ├── Gati.Endpoint.sln
│   │
│   ├── src/
│   │   ├── Gati.Agent/
│   │   │   ├── Program.cs
│   │   │   ├── Worker.cs
│   │   │   ├── Configuration/
│   │   │   ├── Orchestration/
│   │   │   ├── Identity/
│   │   │   ├── Collectors/
│   │   │   ├── State/
│   │   │   ├── Communication/
│   │   │   ├── Commands/
│   │   │   ├── Updates/
│   │   │   ├── Security/
│   │   │   └── Windows/
│   │   │
│   │   └── Gati.DriverExecutor/
│   │       ├── Program.cs
│   │       ├── Pipe/
│   │       ├── Authorization/
│   │       ├── Validation/
│   │       ├── Operations/
│   │       │   ├── Install/
│   │       │   └── Rollback/
│   │       └── Windows/
│   │
│   ├── tests/
│   │   ├── Gati.Agent.UnitTests/
│   │   ├── Gati.Agent.IntegrationTests/
│   │   ├── Gati.DriverExecutor.UnitTests/
│   │   └── Gati.DriverExecutor.IntegrationTests/
│   │
│   └── installer/
│       └── README.md
│
├── infra/
│   ├── compose/
│   │   ├── compose.staging.yml
│   │   └── compose.production.yml
│   │
│   ├── docker/
│   │   ├── backend/
│   │   ├── scraper/
│   │   └── observability/
│   │
│   ├── nginx/
│   │   ├── staging.conf.template
│   │   └── production.conf.template
│   │
│   ├── systemd/
│   │   ├── scraper/
│   │   ├── backup/
│   │   └── maintenance/
│   │
│   ├── observability/
│   │   ├── prometheus/
│   │   │   ├── prometheus.yml
│   │   │   └── rules/
│   │   └── grafana/
│   │       ├── provisioning/
│   │       └── dashboards/
│   │
│   ├── backup/
│   │   ├── README.md
│   │   ├── backup.sh
│   │   └── restore.sh
│   │
│   └── deploy/
│       ├── README.md
│       ├── staging/
│       └── production/
│
├── lab/
│   └── windows/
│       ├── README.md
│       ├── scenarios/
│       ├── fixtures/
│       └── scripts/
│
├── specs/
│   ├── F0-bootstrap/
│   ├── F1-auth-rbac-auditoria/
│   ├── F2-cadastros/
│   ├── F3-pesquisa-manutencoes/
│   ├── F4-arquivos/
│   ├── F5-importacoes/
│   ├── F6-termos/
│   ├── F7-movimentacoes/
│   ├── F8-assinatura-externa/
│   ├── F9-endpoint-minimo/
│   ├── F10-endpoint-coleta/
│   ├── F11-scraping/
│   ├── F12-drivers/
│   └── F13-go-live/
│
├── docs/
│   ├── requisitos/
│   ├── arquitetura/
│   ├── adr/
│   ├── api/
│   ├── seguranca/
│   ├── lgpd/
│   └── operacao/
│       ├── runbooks/
│       ├── deploy-rollback.md
│       ├── backup-restore.md
│       ├── troubleshooting.md
│       └── incidentes.md
│
├── scripts/
│   ├── verify.py
│   └── README.md
│
├── .editorconfig
├── .gitignore
├── .gitattributes
├── README.md
├── GATI_Fases_Desenvolvimento.md
└── GATI_Arquitetura_Pastas_Arquivos.md
```

---

# 4. Backend Django

## 4.1 `backend/config/`

Responsável pela configuração técnica do Django, sem regras de negócio.

```text
backend/config/
├── __init__.py
├── urls.py
├── wsgi.py
├── asgi.py
├── env.py
└── settings/
    ├── __init__.py
    ├── base.py
    ├── development.py
    ├── test.py
    ├── staging.py
    └── production.py
```

### `base.py`

Somente configuração comum:

- `INSTALLED_APPS`;
- middlewares;
- templates;
- banco por parâmetros externos;
- autenticação;
- internacionalização;
- static;
- storage;
- logging base;
- DRF;
- segurança comum.

### `development.py`

Configuração local:

- dados sintéticos;
- e-mail fake;
- `DEBUG=True`;
- sem scraping periódico;
- sem driver real;
- HTTP apenas em loopback quando aplicável.

### `test.py`

Configuração automatizada:

- PostgreSQL efêmero;
- dados sintéticos;
- integrações controladas/fakes;
- sem acesso a produção.

### `staging.py`

Configuração de homologação:

- `DEBUG=False`;
- HTTPS;
- banco próprio;
- secrets exclusivos;
- banner de homologação;
- smoke de integrações apenas quando explicitamente habilitado.

### `production.py`

Configuração produtiva:

- `DEBUG=False`;
- cookies seguros;
- HTTPS;
- HSTS;
- secrets reais externos;
- configurações explícitas de hosts/origens;
- integrações oficiais.

### `env.py`

Responsável apenas por:

- leitura;
- validação;
- tipagem;
- falha explícita diante de configuração obrigatória ausente;
- rejeição de ambiente desconhecido.

Nenhum secret real deve ser hardcoded.

---

# 5. API transversal

```text
backend/gati/api/
├── urls.py
├── pagination.py
├── versioning.py
├── exceptions.py
└── problem_details.py
```

Responsabilidades:

### `urls.py`

Agrega exclusivamente as rotas:

```text
/api/v1/
```

Cada app registra suas próprias rotas e o agregador apenas as inclui.

### `pagination.py`

Centraliza:

- `PageNumberPagination`;
- tamanho padrão;
- limite máximo previsto.

### `versioning.py`

Centraliza a configuração de versionamento da API.

### `exceptions.py`

Traduz exceções conhecidas para respostas seguras.

Não pode retornar:

- SQL;
- stack trace;
- token;
- segredo;
- detalhes internos desnecessários.

### `problem_details.py`

Centraliza o contrato RFC 9457:

```text
type
title
status
detail
instance
code
errors
```

---

# 6. Código transversal do backend

## 6.1 `common/`

Somente código realmente reutilizável e independente do domínio.

```text
common/
├── constants.py
├── validators.py
├── hashing.py
├── tokens.py
├── time.py
├── db.py
└── clamav.py
```

Não utilizar `common/` como local para código sem dono.

Uma função só deve ir para `common/` se possuir uso transversal comprovado.

### Exemplos adequados

- geração criptograficamente segura de tokens;
- hashing genérico;
- validações comuns;
- integração básica com ClamAV;
- utilidades de tempo;
- helpers transacionais genéricos.

### Exemplos inadequados

- regra de emissão de Termo;
- regra de devolução;
- regra de instalação de driver;
- regra de enrollment;
- regra de manutenção.

Essas regras pertencem aos seus módulos de domínio.

---

# 7. Observabilidade no backend

```text
observability/
├── health.py
├── metrics.py
├── logging.py
└── urls.py
```

Responsabilidades:

### `health.py`

Endpoints:

```text
/health/live/
/health/ready/
```

### `metrics.py`

Instrumentação para:

```text
/internal/metrics/
```

Esse endpoint não é público.

### `logging.py`

Padroniza logs técnicos:

- JSON;
- correlação;
- request ID;
- sanitização;
- minimização de PII.

Nunca registrar:

- token;
- cookie;
- `Authorization`;
- senha;
- secrets;
- CPF/documento integral sem necessidade;
- SQL sensível.

---

# 8. Integrações externas

```text
integrations/
└── email/
    ├── backend.py
    ├── messages.py
    └── templates.py
```

O módulo de e-mail deve ser um adapter.

O domínio de Termos não deve conhecer detalhes específicos do Resend além do contrato necessário para solicitar o envio.

### `backend.py`

Integração SMTP através do backend de e-mail do Django.

### `messages.py`

Orquestra mensagens aprovadas:

- recuperação de senha;
- assinatura de Termo.

### `templates.py`

Resolve templates versionados.

Templates HTML/texto permanecem na estrutura de templates da aplicação.

---

# 9. Padrão interno de um Django App

Nem todo app precisa de todos os arquivos no primeiro dia.

A estrutura deve crescer conforme a necessidade real.

Padrão recomendado:

```text
<app>/
├── __init__.py
├── apps.py
├── models.py
├── admin.py
├── permissions.py
├── services/
│   ├── __init__.py
│   └── ...
├── api/
│   ├── __init__.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── web/
│   ├── __init__.py
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── templates/
│   └── <app>/
├── migrations/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    ├── test_api.py
    └── test_permissions.py
```

## Regra principal

```text
HTML View ─┐
           ├──> Service ───> Models / ORM
DRF View ──┘
```

Regras críticas não devem ser duplicadas em:

- formulário;
- serializer;
- View HTML;
- ViewSet;
- template.

Formulários e serializers validam a entrada da respectiva fronteira.

A camada de serviço aplica as invariantes do negócio.

---

# 10. Apps Django e respectivas entidades

## 10.1 `usuarios`

```text
apps/usuarios/
```

Responsável por:

- `UsuarioTI`;
- login;
- recuperação de senha;
- sessão;
- Groups;
- Permissions;
- associação de perfil;
- gerenciamento de usuários de TI.

Entidade principal:

```text
UsuarioTI
```

Regras:

- um perfil funcional por usuário;
- Administrador ou Operador;
- Admin funcional não equivale a `is_superuser`.

---

## 10.2 `auditoria`

```text
apps/auditoria/
```

Entidade:

```text
LogAuditoria
```

Responsável por:

- gravação de ações críticas;
- leitura Admin-only;
- proteção contra alteração/exclusão;
- sanitização do contexto;
- eventos de autenticação.

O módulo oferece uma API interna simples para os demais serviços registrarem eventos.

---

## 10.3 `cadastros`

```text
apps/cadastros/
```

Entidades:

```text
Departamento
CategoriaAtivo
StatusAtivo
Localizacao
```

Esses registros são referências estruturais consumidas por outros módulos.

O app não deve acumular regras de Ativo ou Pessoa.

---

## 10.4 `pessoas`

```text
apps/pessoas/
```

Entidade:

```text
Pessoa
```

Responsável por:

- cadastro;
- edição;
- inativação;
- dados mínimos;
- mascaramento;
- consulta;
- desidentificação quando elegível;
- relatório relativo ao titular quando implementado.

A responsabilidade sobre um Ativo não deve ser editada diretamente aqui.

Esse vínculo pertence ao fluxo de `movimentacoes`.

---

## 10.5 `ativos`

```text
apps/ativos/
```

Entidades:

```text
Ativo
AtivoTecnico
InterfaceRede
DriverInstalado
```

Responsável por:

- inventário;
- estado atual;
- cadastro administrativo;
- unicidade de Patrimônio;
- unicidade de Service Tag;
- pesquisa;
- filtros;
- detalhe do Ativo;
- dados técnicos recebidos do Endpoint.

Dados técnicos autoritativos do Endpoint não devem possuir bypass manual de edição.

---

## 10.6 `manutencoes`

```text
apps/manutencoes/
```

Entidade:

```text
Manutencao
```

Responsável por:

- eventos de manutenção;
- datas;
- fornecedor;
- nota fiscal/serviço;
- defeito;
- garantia;
- histórico associado ao Ativo.

---

## 10.7 `arquivos`

```text
apps/arquivos/
```

Entidades:

```text
Arquivo
AtivoArquivo
ManutencaoArquivo
ProcessoArquivo
```

Estrutura interna sugerida:

```text
arquivos/
├── models.py
├── storage.py
├── security.py
├── services/
│   ├── upload.py
│   ├── download.py
│   └── cleanup.py
└── ...
```

### `storage.py`

Implementa a abstração Django Storage para filesystem privado.

### `security.py`

Pipeline:

```text
tamanho/extensão
    ↓
quarentena
    ↓
MIME real
    ↓
SHA-256
    ↓
ClamAV
    ↓
promoção atômica
    ↓
vínculo funcional
```

### Regras

- fora do webroot;
- um arquivo por request;
- download sempre autorizado pela aplicação;
- bytes disponíveis imutáveis;
- nome físico por UUID;
- nome original somente como metadado;
- sem preview inline no MVP.

---

## 10.8 `importacoes`

```text
apps/importacoes/
```

Entidade:

```text
ImportacaoExecucao
```

Estrutura:

```text
importacoes/
├── models.py
├── parsers/
│   ├── __init__.py
│   ├── csv_parser.py
│   └── xlsx_parser.py
├── validators/
│   ├── __init__.py
│   ├── pessoas.py
│   └── ativos.py
├── services/
│   ├── preview.py
│   ├── confirm.py
│   └── cleanup.py
└── tests/
```

Fluxo:

```text
upload temporário
    ↓
segurança
    ↓
parsing
    ↓
validação
    ↓
preview
    ↓
confirmação explícita
    ↓
revalidação
    ↓
transação atômica
```

O parser não cria registros diretamente.

A criação ocorre somente na camada de serviço após confirmação.

---

## 10.9 `termos`

```text
apps/termos/
```

Entidades:

```text
ModeloTermo
Termo
TermoItem
AssinaturaTermo
```

Estrutura:

```text
termos/
├── models.py
├── permissions.py
├── services/
│   ├── modelos.py
│   ├── geracao.py
│   ├── emissao.py
│   ├── cancelamento.py
│   ├── assinatura.py
│   ├── assinatura_presencial.py
│   └── assinatura_externa.py
├── api/
├── web/
├── templates/
│   └── termos/
│       ├── ...
│       └── assinatura/
└── tests/
```

Responsável por:

- ModeloTermo;
- edição de Termo;
- snapshots;
- TermoItem;
- payload canônico;
- hash;
- congelamento;
- cancelamento;
- AssinaturaTermo;
- assinatura presencial;
- assinatura externa;
- evidências.

Estados:

```text
EM_EDICAO
AGUARDANDO_ASSINATURAS
ASSINADO
CANCELADO
```

A imutabilidade deve ser defendida em aplicação e banco.

---

## 10.10 `movimentacoes`

```text
apps/movimentacoes/
```

Entidades:

```text
ResponsabilidadeAtivo
Movimentacao
ProcessoMovimentacao
ProcessoItem
```

Estrutura:

```text
movimentacoes/
├── models.py
├── state.py
├── services/
│   ├── responsabilidades.py
│   ├── entrega.py
│   ├── devolucao.py
│   └── historico.py
├── api/
├── web/
└── tests/
```

### `state.py`

Somente transições de estado e regras determinísticas claramente delimitadas.

### `entrega.py`

Orquestra:

- responsável;
- ativos;
- acessórios;
- condições;
- Termo;
- signatários;
- emissão.

### `devolucao.py`

Orquestra:

- conferência;
- divergências;
- avarias;
- assinatura;
- encerramento da responsabilidade;
- mudança de status.

### `historico.py`

Cria eventos append-only.

Não permite correção por UPDATE de evento histórico.

---

## 10.11 `dashboard`

```text
apps/dashboard/
```

Sem entidade própria obrigatória.

Responsável apenas por consultas agregadas para:

- ativos por status;
- garantias próximas do vencimento;
- Termos pendentes.

O dashboard não deve possuir regras de domínio próprias nem substituir Grafana.

---

## 10.12 `endpoints`

```text
apps/endpoints/
```

Entidades:

```text
Endpoint
EndpointEnrollment
EndpointCredential
EndpointCommand
EndpointAgentRelease
```

Estrutura:

```text
endpoints/
├── models.py
├── authentication.py
├── permissions.py
├── services/
│   ├── enrollment.py
│   ├── credentials.py
│   ├── heartbeat.py
│   ├── collection.py
│   ├── commands.py
│   └── agent_updates.py
├── api/
└── tests/
```

### `authentication.py`

Autenticação do agente é separada da autenticação humana.

Responsável por:

- Bearer opaco;
- hash server-side;
- validação da credencial;
- revogação;
- rotação.

### `enrollment.py`

Bootstrap one-time vinculado ao Ativo.

### `heartbeat.py`

Atualiza `last_seen` e estado operacional.

### `collection.py`

Processa:

- `collection_id`;
- `sequence`;
- snapshot;
- precedência do Endpoint;
- idempotência.

### `commands.py`

Gerencia:

```text
PENDING
RECEIVED
STARTED
SUCCEEDED
FAILED
EXPIRED
CANCELLED
```

---

## 10.13 `drivers`

```text
apps/drivers/
```

Entidades:

```text
DriverAtualizacao
AgendamentoInstalacao
DriverPacote
ScrapingProvider
ScrapingExecucao
```

Estrutura:

```text
drivers/
├── models.py
├── services/
│   ├── candidatos.py
│   ├── pacotes.py
│   ├── autorizacao.py
│   ├── agendamento.py
│   └── rollback.py
├── scraping/
│   ├── __init__.py
│   ├── base.py
│   ├── dell.py
│   ├── lenovo.py
│   ├── http.py
│   └── browser.py
├── management/
│   └── commands/
│       └── scrape_drivers.py
├── api/
└── tests/
    └── fixtures/
        └── html/
```

### Regra fundamental

```text
scraping != instalação
```

O scraper:

- coleta metadados;
- normaliza;
- deduplica;
- registra candidato;
- registra falha.

O scraper nunca:

- autoriza;
- agenda;
- instala;
- chama o Driver Executor.

---

# 11. Dependências entre módulos

Direção recomendada:

```text
common
  ↑
  ├── usuarios
  ├── auditoria
  ├── cadastros
  │     ├── pessoas
  │     └── ativos
  │           ├── manutencoes
  │           └── endpoints
  │
  ├── arquivos
  ├── termos
  │
  ├── movimentacoes
  │     ├── pessoas
  │     ├── ativos
  │     └── termos
  │
  ├── importacoes
  │     ├── cadastros
  │     ├── pessoas
  │     └── ativos
  │
  ├── dashboard
  │     ├── ativos
  │     ├── manutencoes
  │     └── termos
  │
  └── drivers
        ├── ativos
        └── endpoints
```

Regras:

1. `common` não importa módulos de domínio.
2. `dashboard` pode consultar outros módulos, mas nenhum módulo depende de `dashboard`.
3. `drivers` depende de `endpoints`; `endpoints` não depende de `drivers` para suas funções básicas.
4. `movimentacoes` orquestra Ativo, Pessoa e Termo.
5. `termos` não deve controlar diretamente o ciclo de vida do Ativo.
6. `importacoes` usa serviços de domínio; não contorna invariantes.
7. Views e serializers não acessam tabelas de outros módulos para executar regras críticas de forma ad hoc.

---

# 12. Templates e HTMX

Não será criado um projeto frontend separado.

Estrutura global:

```text
backend/templates/
├── base.html
├── components/
│   ├── navbar.html
│   ├── pagination.html
│   ├── alerts.html
│   ├── filters.html
│   └── form_errors.html
└── errors/
    ├── 400.html
    ├── 403.html
    ├── 404.html
    └── 500.html
```

Estrutura por app:

```text
apps/ativos/templates/ativos/
├── list.html
├── detail.html
├── form.html
└── _partials/
    ├── table.html
    ├── filters.html
    └── status.html
```

Convenção:

- página completa: nome normal;
- fragmento HTMX: `_partials/`;
- URLs importantes permanecem estáveis;
- validação server-side é a autoridade;
- HTMX melhora interação, mas não implementa autorização.

---

# 13. Static

```text
backend/static/gati/
├── css/
│   └── gati.css
├── js/
│   └── gati.js
└── img/
```

Regras:

- JavaScript deve permanecer pequeno e complementar;
- não criar framework SPA;
- lógica de autorização não fica no JavaScript;
- não armazenar token sensível no frontend;
- não usar `innerHTML` com entrada não confiável;
- estados críticos não dependem exclusivamente de toast.

---

# 14. Testes do backend

## 14.1 Testes locais de cada app

Dentro de cada app:

```text
tests/
├── test_models.py
├── test_services.py
├── test_api.py
└── test_permissions.py
```

Uso principal:

- unidade;
- regras determinísticas;
- autorização;
- validações;
- state machines.

---

## 14.2 Testes transversais

```text
backend/tests/
├── api/
├── contract/
├── integration/
├── e2e/
├── security/
├── performance/
├── recovery/
└── fixtures/
```

### `api/`

- RFC 9457;
- paginação;
- filtros;
- autenticação;
- idempotência.

### `contract/`

- OpenAPI;
- compatibilidade de contratos;
- schemas importantes.

### `integration/`

Django + PostgreSQL real:

- migrations;
- constraints;
- imutabilidade;
- transações;
- ClamAV/fakes controlados;
- integrações.

### `e2e/`

Playwright sobre:

- login;
- inventário;
- entrega;
- devolução;
- Termos;
- assinatura.

### `security/`

- auth;
- RBAC;
- CSRF;
- upload;
- SSRF;
- BOLA/IDOR;
- mass assignment;
- redaction;
- secrets.

### `performance/`

RNF-009 e demais medições aprovadas.

### `recovery/`

- backup;
- restore;
- integridade;
- reconciliação pós-restore.

### `fixtures/`

Somente dados sintéticos.

Dados reais de produção não entram no repositório.

---

# 15. Endpoint Windows

O Endpoint é um produto separado dentro do mesmo monorepo.

```text
endpoint/
├── Gati.Endpoint.sln
├── src/
│   ├── Gati.Agent/
│   └── Gati.DriverExecutor/
├── tests/
└── installer/
```

---

# 16. `Gati.Agent`

```text
Gati.Agent/
├── Program.cs
├── Worker.cs
├── Configuration/
├── Orchestration/
├── Identity/
├── Collectors/
├── State/
├── Communication/
├── Commands/
├── Updates/
├── Security/
└── Windows/
```

Correspondência com a baseline:

| Pasta | Responsabilidade |
|---|---|
| `Orchestration/` | Agent Orchestrator |
| `Identity/` | Identity Provider, `agent_instance_id`, credencial |
| `Collectors/` | hardware, rede, SO e drivers |
| `State/` | estado local, sequence e outbox |
| `Communication/` | HTTPS, heartbeat, polling, retry e timeouts |
| `Commands/` | recepção, deduplicação e estados dos comandos |
| `Updates/` | atualização segura do próprio agente |
| `Security/` | DPAPI, ACL e validações |
| `Windows/` | integração específica com APIs Windows/CIM/WMI |

Subestrutura possível dos collectors:

```text
Collectors/
├── Hardware/
├── Network/
├── OperatingSystem/
└── Drivers/
```

---

# 17. `Gati.DriverExecutor`

```text
Gati.DriverExecutor/
├── Program.cs
├── Pipe/
├── Authorization/
├── Validation/
├── Operations/
│   ├── Install/
│   └── Rollback/
└── Windows/
```

Regras estruturais:

- executável/processo separado do Agent;
- LocalSystem apenas onde necessário;
- sem HTTP;
- sem Bearer;
- sem scraping;
- sem acesso administrativo ao GATI;
- comunicação local via named pipe;
- ACL restritiva;
- operações enumeradas;
- sem shell arbitrário.

---

# 18. Installer

```text
endpoint/installer/
└── README.md
```

O MVP exige MSI per-machine.

A ferramenta específica para gerar o MSI não está definida neste documento.

Portanto:

- não escolher WiX, Advanced Installer ou outra ferramenta apenas pela arquitetura de pastas;
- registrar a decisão quando a DU de empacotamento for iniciada;
- se a escolha tiver impacto estrutural relevante, avaliar ADR.

---

# 19. Windows Lab

```text
lab/windows/
├── README.md
├── scenarios/
├── fixtures/
└── scripts/
```

Uso:

- MSI real;
- instalação/remoção;
- serviço;
- reboot;
- atualização;
- driver;
- rollback;
- falhas privilegiadas.

Regras:

- ambiente descartável;
- snapshot/VM ou workstation controlada;
- dados sintéticos;
- nunca usar Ativo/Endpoint real de produção.

Exemplos de cenários:

```text
scenarios/
├── agent-install/
├── enrollment/
├── credential-rotation/
├── offline-recovery/
├── driver-install/
├── driver-reboot/
└── driver-rollback/
```

---

# 20. Scraping

O código do scraping permanece no backend:

```text
backend/gati/apps/drivers/scraping/
```

A execução pode ocorrer em container isolado através de configuração em:

```text
infra/docker/scraper/
```

Isso preserva:

- monólito modular;
- management command oficial;
- isolamento operacional do browser headless.

Fluxo:

```text
systemd timer
    ↓
management command scrape_drivers
    ↓
provider
    ↓
HTTP-first
    ↓
Playwright somente se necessário
    ↓
normalização
    ↓
persistência do candidato
```

---

# 21. Infraestrutura

## 21.1 `infra/compose/`

```text
infra/compose/
├── compose.staging.yml
└── compose.production.yml
```

Somente configurações não sensíveis devem ser versionadas.

Secrets são fornecidos externamente.

Não manter credenciais diretamente no YAML.

---

## 21.2 `infra/docker/`

```text
infra/docker/
├── backend/
├── scraper/
└── observability/
```

### `backend/`

Configura build reproduzível da aplicação homologável/promovível por digest.

### `scraper/`

Isola dependências de Playwright/Chromium.

### `observability/`

Somente customizações realmente necessárias para a stack de observabilidade.

Evitar criar imagens customizadas quando a imagem oficial atende o requisito.

---

# 22. NGINX

```text
infra/nginx/
├── staging.conf.template
└── production.conf.template
```

Responsabilidades:

- única fronteira pública HTTP/HTTPS;
- TLS;
- headers;
- HSTS em produção;
- proxy para Gunicorn;
- request ID;
- `/internal/` não público;
- downloads privados via `internal` / `X-Accel` quando utilizado.

Hostnames concretos são configurados somente quando definidos.

---

# 23. systemd

```text
infra/systemd/
├── scraper/
├── backup/
└── maintenance/
```

Uso previsto:

- execução diária do scraping;
- backup diário;
- tarefas periódicas apropriadas;
- cleanup operacional quando necessário.

Não introduzir Celery/Redis para essas tarefas no MVP.

Arquivos `.service` e `.timer` somente devem ser adicionados quando a respectiva tarefa existir.

---

# 24. Observabilidade

```text
infra/observability/
├── prometheus/
│   ├── prometheus.yml
│   └── rules/
└── grafana/
    ├── provisioning/
    └── dashboards/
```

Dashboards previstos:

```text
GATI Overview
VPS & Containers
PostgreSQL
Integrations
Endpoints & Drivers
```

Alertas previstos incluem:

- backup falho;
- storage baixo;
- ClamAV indisponível;
- scraping suspenso;
- Endpoint offline relevante;
- falha de rollback;
- intervenção manual;
- trust failure;
- timeout;
- reinício pendente.

---

# 25. Backup e restore

```text
infra/backup/
├── README.md
├── backup.sh
└── restore.sh
```

### `backup.sh`

Deve ser projetado para:

- lock exclusivo;
- `.partial`;
- `pg_dump` custom;
- `pg_dumpall` globals;
- arquivos permanentes;
- manifest;
- SHA;
- promoção após sucesso.

### `restore.sh`

Deve:

- exigir parâmetros explícitos;
- validar backup;
- possuir passos verificáveis;
- não executar restore destrutivo silenciosamente;
- suportar o procedimento documentado.

Scripts destrutivos exigem cuidado operacional e documentação de rollback.

---

# 26. Deploy

```text
infra/deploy/
├── README.md
├── staging/
└── production/
```

Regras:

- build once;
- promote by digest;
- sem rebuild diferente entre staging e produção;
- deploy de produção manual/autorizado;
- sem self-hosted GitHub runner na VPS de produção;
- backup pré-migration quando houver risco de schema/dados;
- validar health/readiness após deploy.

---

# 27. GitHub Actions

```text
.github/workflows/
├── ci-backend.yml
├── ci-endpoint.yml
├── security.yml
├── build-images.yml
└── release.yml
```

Os arquivos são criados progressivamente conforme as fases.

## `ci-backend.yml`

Previsto para:

- instalação;
- verificação de formatação quando configurada;
- lint quando configurado;
- testes;
- coverage;
- migration checks;
- integração PostgreSQL;
- build.

## `ci-endpoint.yml`

Runner Windows quando necessário:

- restore;
- build;
- testes .NET;
- coverage.

## `security.yml`

Quando scanners estiverem configurados:

- SAST;
- SCA;
- secret scanning;
- IaC/container scanning proporcional ao risco.

## `build-images.yml`

- build reproduzível;
- publicação no GHCR;
- digest como identidade de promoção.

## `release.yml`

- artefatos de release;
- tags SemVer;
- retenção conforme política;
- sem auto-deploy irrestrito de produção.

---

# 28. SPECs

Estrutura oficial:

```text
specs/
└── <fase-ou-feature>/
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    ├── test-plan.md
    └── traceability.md
```

Exemplo:

```text
specs/
└── F2-cadastros/
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    ├── test-plan.md
    └── traceability.md
```

Para uma fase grande, subdividir:

```text
specs/F12-drivers/
├── F12.1-pacotes/
│   ├── spec.md
│   ├── plan.md
│   ├── tasks.md
│   ├── test-plan.md
│   └── traceability.md
├── F12.2-autorizacao/
└── F12.3-executor/
```

Não criar uma SPEC gigante para toda a aplicação.

---

# 29. Documentação

```text
docs/
├── requisitos/
├── arquitetura/
├── adr/
├── api/
├── seguranca/
├── lgpd/
└── operacao/
```

## `docs/requisitos/`

Somente documentos normativos do GATI.

Não copiar documentação de outro projeto como se fosse norma do GATI.

---

## `docs/arquitetura/`

Documentação operacional complementar, por exemplo:

```text
docs/arquitetura/
├── components.md
├── data-model.md
├── security-boundaries.md
└── deployment-view.md
```

Esses arquivos não substituem a baseline consolidada.

---

## `docs/adr/`

Formato:

```text
ADR-001-<titulo>.md
ADR-002-<titulo>.md
...
```

Criar ADR apenas quando existir uma decisão arquitetural nova ou revisão significativa.

---

## `docs/api/`

Pode conter:

- políticas de compatibilidade;
- documentação complementar;
- exemplos de erro;
- processo de geração OpenAPI.

O OpenAPI oficial continua derivado do código via `drf-spectacular`.

---

## `docs/seguranca/`

Exemplos:

```text
threat-model.md
security-testing.md
secrets-management.md
incident-response.md
```

Somente criar quando o conteúdo existir.

---

## `docs/lgpd/`

Documentos técnicos/organizacionais quando fornecidos/aprovados:

```text
ROPA
matriz de retenção
Aviso de Privacidade
procedimento de direitos
procedimento de incidentes
```

Prazos jurídicos não devem ser inventados pelo software.

---

## `docs/operacao/`

```text
operacao/
├── runbooks/
├── deploy-rollback.md
├── backup-restore.md
├── troubleshooting.md
└── incidentes.md
```

Runbooks devem ser acionáveis e verificáveis.

---

# 30. Scripts reproduzíveis

```text
scripts/
├── verify.py
└── README.md
```

## `verify.py`

Ponto de entrada lógico para validação completa.

O script deve orquestrar somente ferramentas realmente configuradas.

Conceitualmente:

```text
config/check
    ↓
migrations check
    ↓
tests
    ↓
coverage
    ↓
security checks configurados
    ↓
build/checks aplicáveis
```

O arquivo não deve simular ferramentas inexistentes.

Se futuramente o repositório possuir um comando mais adequado, `verify.py` pode ser substituído formalmente.

---

# 31. Arquivos da raiz

## `.gitignore`

Deve excluir no mínimo classes de artefatos como:

- ambientes virtuais;
- caches;
- coverage local;
- arquivos temporários;
- `.env` real;
- secrets;
- build local;
- binários .NET;
- estado de IDE;
- storage local;
- quarentena;
- backups;
- banco local temporário quando existir.

Não ignorar migrations.

---

## `.editorconfig`

Padronização básica:

- encoding;
- newline;
- indentação;
- whitespace.

---

## `.gitattributes`

Padronização de:

- line endings;
- arquivos texto;
- tratamento de artefatos especiais quando necessário.

Particularmente importante porque o monorepo contém Windows/.NET e Linux/Python.

---

## `README.md`

Deve responder, no mínimo:

1. o que é o GATI;
2. pré-requisitos;
3. estrutura do repositório;
4. configuração local;
5. banco;
6. como executar backend;
7. como executar testes;
8. como executar `verify`;
9. como trabalhar com Endpoint;
10. como trabalhar com specs;
11. regras de secrets;
12. processo de commit/publicação;
13. referências normativas.

Não adicionar instruções de funcionalidades que ainda não existem.

---

# 32. Arquivos que NÃO pertencem ao Git

Nunca versionar:

```text
.env
secrets reais
senhas
tokens
chaves privadas
certificados privados
credenciais SMTP
credenciais PostgreSQL
credenciais Endpoint
bootstrap tokens
dados reais de produção
uploads permanentes
quarentena
backups reais
pacotes privados de drivers
dados Prometheus
dados Grafana
logs de produção
dumps de banco
```

---

# 33. Diretórios externos ao repositório em produção

A baseline prevê dados operacionais fora do Git.

Estrutura conceitual:

```text
/etc/gati/secrets/
/var/lib/gati/
/var/backups/gati/
/opt/gati/deploy/
```

## `/etc/gati/secrets/`

Somente secrets e arquivos sensíveis.

## `/var/lib/gati/`

Dados mutáveis:

- uploads permanentes;
- storage privado;
- quarentena;
- pacotes/cache quando aplicável;
- estado operacional necessário.

## `/var/backups/gati/`

Backups oficiais locais do MVP.

## `/opt/gati/deploy/`

Artefatos/configuração operacional do deploy.

Nenhum desses diretórios deve ser confundido com o checkout Git.

---

# 34. Migrations

Cada app com models mantém:

```text
<app>/migrations/
```

Regras:

- versionadas em Git;
- não reescrever migration aplicada silenciosamente;
- testadas em banco real;
- promoção:

```text
test
  ↓
staging
  ↓
production
```

Alterações de alto risco devem usar estratégia compatível com:

```text
expand
  ↓
migrate
  ↓
new code
  ↓
contract
```

Constraints e mecanismos de imutabilidade relevantes devem ser entregues por migrations rastreáveis.

---

# 35. Matriz de fase → estrutura afetada

| Fase | Diretórios/arquivos principais |
|---|---|
| F0 | `backend/config/`, `backend/gati/common/`, `observability/`, `backend/tests/`, `.github/`, `scripts/` |
| F1 | `usuarios/`, `auditoria/`, `gati/api/`, settings de segurança |
| F2 | `cadastros/`, `pessoas/`, `ativos/`, templates/static |
| F3 | `ativos/`, `manutencoes/`, testes de pesquisa/performance |
| F4 | `arquivos/`, `common/clamav.py`, storage e infra ClamAV |
| F5 | `importacoes/`, parsers, validators, fixtures |
| F6 | `termos/` |
| F7 | `movimentacoes/`, `dashboard/`, templates de wizard |
| F8 | `termos/`, `integrations/email/`, templates de assinatura |
| F9 | `endpoints/`, `endpoint/src/Gati.Agent/` |
| F10 | `endpoints/`, `Gati.Agent/Collectors`, `Communication`, `Commands`, `Updates` |
| F11 | `drivers/scraping/`, `scrape_drivers.py`, `infra/docker/scraper/`, `infra/systemd/scraper/` |
| F12 | `drivers/`, `Gati.DriverExecutor/`, `lab/windows/` |
| F13 | `infra/`, `.github/workflows/`, `backend/tests/security`, `performance`, `recovery`, `docs/operacao/` |

---

# 36. Ordem de criação das pastas

A árvore completa representa o estado alvo.

Ela não deve ser criada vazia de uma única vez.

Aplicar YAGNI e criar apenas o necessário em cada fase.

## F0

Criar:

```text
.github/
backend/
backend/config/
backend/gati/
backend/gati/api/
backend/gati/common/
backend/gati/observability/
backend/gati/apps/usuarios/
backend/tests/
specs/F0-bootstrap/
docs/
scripts/
```

## F1

Adicionar:

```text
backend/gati/apps/auditoria/
```

E completar:

```text
usuarios/
api/
security settings
```

## F2

Adicionar:

```text
cadastros/
pessoas/
ativos/
templates/
static/
```

## F3

Adicionar:

```text
manutencoes/
```

## F4

Adicionar:

```text
arquivos/
```

## F5

Adicionar:

```text
importacoes/
```

## F6

Adicionar:

```text
termos/
```

## F7

Adicionar:

```text
movimentacoes/
dashboard/
```

## F8

Adicionar/completar:

```text
integrations/email/
termos/templates/.../assinatura/
```

## F9

Adicionar:

```text
backend/gati/apps/endpoints/
endpoint/
```

## F10

Expandir:

```text
endpoint/src/Gati.Agent/
```

## F11

Adicionar:

```text
backend/gati/apps/drivers/scraping/
infra/docker/scraper/
infra/systemd/scraper/
```

## F12

Adicionar:

```text
endpoint/src/Gati.DriverExecutor/
lab/windows/
```

## F13

Completar:

```text
infra/
docs/operacao/
docs/seguranca/
.github/workflows/
backend/tests/security/
backend/tests/performance/
backend/tests/recovery/
```

---

# 37. Estrutura inicial recomendada para F0

A primeira implementação não precisa criar todos os módulos futuros.

Estrutura mínima:

```text
gati/
├── .github/
│   └── workflows/
│       └── ci-backend.yml
│
├── backend/
│   ├── manage.py
│   ├── pyproject.toml
│   ├── .env.example
│   ├── Dockerfile
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   ├── env.py
│   │   └── settings/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── development.py
│   │       ├── test.py
│   │       ├── staging.py
│   │       └── production.py
│   │
│   ├── gati/
│   │   ├── __init__.py
│   │   ├── api/
│   │   ├── common/
│   │   ├── observability/
│   │   └── apps/
│   │       └── usuarios/
│   │
│   ├── templates/
│   ├── static/
│   └── tests/
│
├── specs/
│   └── F0-bootstrap/
│       ├── spec.md
│       ├── plan.md
│       ├── tasks.md
│       ├── test-plan.md
│       └── traceability.md
│
├── docs/
│   ├── requisitos/
│   ├── arquitetura/
│   └── adr/
│
├── scripts/
│   ├── verify.py
│   └── README.md
│
├── .editorconfig
├── .gitignore
├── .gitattributes
├── README.md
├── GATI_Fases_Desenvolvimento.md
└── GATI_Arquitetura_Pastas_Arquivos.md
```

Essa é a árvore que deve ser validada contra o repositório real antes de começar a criação/modificação de código.

---

# 38. Regras para evitar acoplamento estrutural

## Não fazer

```text
View -> alteração direta em múltiplas tabelas críticas
Serializer -> regra completa de negócio
Template -> autorização
Endpoint -> tabela do Driver por acoplamento indevido
Scraper -> instalação
Driver Executor -> internet
Dashboard -> atualização de domínio
Import parser -> criação direta
```

## Fazer

```text
View/Serializer
      ↓
Service
      ↓
Invariantes / transação
      ↓
ORM
```

Integração externa:

```text
Domain Service
      ↓
Adapter
      ↓
Serviço externo
```

Operação Windows:

```text
Gati.Agent
      ↓
Named Pipe restrito
      ↓
Gati.DriverExecutor
```

---

# 39. Segurança estrutural

A organização de pastas deve ajudar a reforçar fronteiras de segurança.

## Fronteira humana

```text
usuarios/
permissions.py
sessions
CSRF
```

## Fronteira Endpoint

```text
endpoints/authentication.py
endpoints/services/credentials.py
```

Não reutilizar autenticação humana para agentes.

## Fronteira de arquivos

```text
arquivos/security.py
arquivos/storage.py
```

Nenhum upload vai direto para storage permanente.

## Fronteira de scraping

```text
drivers/scraping/
```

Sem secrets da aplicação no browser context.

## Fronteira privilegiada Windows

```text
Gati.DriverExecutor/
```

Separada do serviço de comunicação com a rede.

---

# 40. Rastreabilidade por Development Unit

Cada DU deve poder mapear:

```text
DU
 ↓
SPEC
 ↓
arquivos alterados
 ↓
testes
 ↓
requisito
 ↓
commit recomendado
```

Exemplo:

```text
DU-F2.1-01
├── specs/F2-cadastros/...
├── backend/gati/apps/ativos/models.py
├── backend/gati/apps/ativos/services/...
├── backend/gati/apps/ativos/api/...
├── backend/gati/apps/ativos/tests/...
└── traceability.md
```

A rastreabilidade não deve depender apenas do histórico do Git.

---

# 41. Regras de evolução da arquitetura

Esta estrutura não autoriza criar antecipadamente todas as abstrações.

Ao evoluir:

1. criar somente diretórios necessários à DU atual;
2. preservar os módulos e contratos existentes;
3. não mover código entre apps sem avaliar impacto;
4. não criar `utils.py` genérico para código sem domínio claro;
5. não criar microserviço para separar código que cabe em um Django app;
6. não criar repositório separado para frontend;
7. não criar broker/fila sem necessidade formal;
8. não criar Kubernetes;
9. não criar novo banco;
10. não introduzir cache compartilhado sem medição/necessidade;
11. avaliar ADR para mudança estrutural duradoura.

---

# 42. Pontos deliberadamente não definidos

A documentação atual não exige que esta arquitetura escolha antecipadamente:

- ferramenta específica de gerenciamento/lock de dependências Python;
- ferramenta de lint/format Python;
- ferramenta de typecheck Python;
- tecnologia do instalador MSI;
- ferramenta específica de IaC;
- firewall concreto (`ufw`, `nftables` etc.);
- solução externa de secrets;
- object storage;
- broker;
- Redis;
- Celery;
- Kubernetes;
- SIEM.

Essas escolhas não devem ser inventadas durante a simples criação da árvore.

Quando uma delas se tornar necessária:

```text
necessidade
   ↓
análise
   ↓
SPEC/DU
   ↓
decisão
   ↓
ADR, se aplicável
   ↓
implementação
```

---

# 43. Resultado arquitetural esperado

No estado completo do MVP, o repositório deve apresentar as seguintes fronteiras claras:

```text
GitHub / CI
    │
    ├── Backend Django modular
    │      ├── HTML/HTMX
    │      ├── API DRF
    │      ├── PostgreSQL
    │      ├── arquivos privados
    │      ├── e-mail
    │      └── scraping
    │
    ├── Endpoint Windows
    │      ├── Gati.Agent
    │      └── Gati.DriverExecutor
    │
    ├── Infraestrutura
    │      ├── NGINX
    │      ├── Docker/Compose
    │      ├── systemd
    │      ├── Prometheus
    │      ├── Grafana
    │      └── backup/restore
    │
    ├── Windows Lab
    │
    ├── SPECs
    │
    └── Documentação
```

A estrutura mantém o MVP como um **monólito modular com componentes auxiliares claramente separados**, sem transformar o sistema em uma arquitetura distribuída desnecessária.

---

# 44. Próxima ação antes da implementação

Antes de criar ou mover qualquer pasta no repositório real:

1. obter o código-fonte atual;
2. listar a árvore existente;
3. localizar manifests/dependências;
4. localizar configuração Django existente;
5. localizar migrations;
6. localizar testes;
7. localizar workflows GitHub;
8. executar baseline;
9. comparar estrutura atual com este documento;
10. classificar cada item como:
   - `IMPLEMENTADO`;
   - `PARCIAL`;
   - `AUSENTE`;
   - `CONFLITANTE`;
   - `BLOQUEADO`;
11. adaptar a arquitetura preservando o que já estiver correto;
12. iniciar somente a menor DU necessária.

---

# 45. Resumo da arquitetura

```text
MONOREPO GATI
│
├── .github/            CI/CD
│
├── backend/            Django + DRF + Templates + HTMX
│   ├── config/         settings e bootstrap
│   ├── gati/api/       infraestrutura da API
│   ├── gati/common/    utilidades transversais reais
│   ├── observability/  health, métricas e logging
│   ├── integrations/   adapters externos
│   └── gati/apps/      módulos de domínio
│
├── endpoint/           C#/.NET Windows
│   ├── Gati.Agent
│   └── Gati.DriverExecutor
│
├── infra/              execução e operação
│
├── lab/windows/        testes privilegiados descartáveis
│
├── specs/              SDD por fase/feature
│
├── docs/               ADR, segurança, LGPD e operação
│
└── scripts/            validação reproduzível
```

---

**Documento:** GATI — Arquitetura de Pastas e Arquivos  
**Versão inicial:** 1.0  
**Finalidade:** orientar a implementação progressiva das fases F0 a F13 sem alterar a arquitetura funcional e técnica aprovada.
