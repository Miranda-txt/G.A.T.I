# GATI — Plano de Fases de Desenvolvimento

**Projeto:** Sistema de Gerenciamento de Ativos de TI — GATI  
**Objetivo:** organizar a implementação do MVP do mais simples e rápido ao mais complexo e demorado, respeitando a documentação técnica já aprovada.  
**Abordagem operacional:** desenvolvimento incremental por Fases, Subfases e Development Units (DUs), com validação contínua, testes, segurança e rastreabilidade.

---

## Princípio de execução

A ordem deste plano não segue simplesmente `RF-001 → RF-016`.

A sequência considera:

- dependências técnicas;
- risco;
- tempo estimado relativo;
- necessidade de fundações anteriores;
- capacidade de validar incrementos isoladamente;
- redução de retrabalho;
- segurança;
- testabilidade;
- reversibilidade.

Cada fase somente deve avançar após os critérios mínimos da fase anterior estarem atendidos.

---

# F0 — Bootstrap e Walking Skeleton

**Complexidade:** baixa  
**Objetivo:** estabelecer uma aplicação mínima integrada, executável, testável e versionada.

## Development Units

### DU-F0.1-01 — Inspeção do repositório
- analisar árvore de diretórios;
- identificar código existente;
- localizar dependências;
- localizar migrations;
- localizar configurações;
- localizar workflows;
- localizar testes;
- identificar divergências em relação à documentação.

### DU-F0.1-02 — Baseline do estado atual
- identificar comando oficial de verificação;
- executar baseline;
- registrar falhas preexistentes;
- bloquear implementação caso a baseline esteja quebrada, salvo se a própria tarefa for corrigir a falha.

### DU-F0.2-01 — Walking Skeleton Django
- estruturar o projeto Django;
- garantir inicialização local;
- manter arquitetura monolítica modular;
- preparar separação entre domínio, serviços, Views/DRF e templates.

### DU-F0.2-02 — PostgreSQL e migration inicial
- configurar PostgreSQL 18;
- criar `UsuarioTI` customizado desde a migration inicial;
- garantir Django ORM e migrations como fonte oficial do schema.

### DU-F0.3-01 — Estrutura de ambientes
Criar a estrutura conceitual de settings:

```text
base.py
development.py
test.py
staging.py
production.py
```

Com:

- `GATI_ENV`;
- fail-safe para ambiente inválido;
- segredos separados por ambiente;
- `ALLOWED_HOSTS` explícito;
- `CSRF_TRUSTED_ORIGINS` explícito.

### DU-F0.4-01 — Testes e verificação
- configurar pytest;
- configurar pytest-django;
- configurar coverage;
- definir comando agregador de verificação;
- criar testes mínimos do skeleton.

### DU-F0.5-01 — GitHub Actions inicial
- pipeline básico;
- migrations check;
- testes;
- coverage;
- build quando aplicável;
- branch `main` protegida conforme processo definido;
- CI reproduzível.

## Critério de saída

A aplicação deve:

- iniciar corretamente;
- conectar ao PostgreSQL;
- aplicar migrations;
- possuir `UsuarioTI` customizado;
- executar testes;
- possuir health checks mínimos;
- possuir pipeline inicial verde.

---

# F1 — Autenticação, RBAC, Auditoria e Fundação da API

**Complexidade:** baixa → média  
**Objetivo:** garantir a base de segurança antes do domínio funcional.

## Escopo

- login por username ou e-mail;
- Argon2id;
- sessões server-side Django;
- logout via POST;
- timeout de inatividade;
- duração absoluta de sessão;
- recuperação de senha;
- proteção contra força bruta;
- cookies seguros;
- CSRF;
- grupos `Administrador` e `Operador`;
- default deny;
- `LogAuditoria`;
- versionamento `/api/v1/`;
- RFC 9457 `application/problem+json`;
- paginação;
- filtros whitelistados;
- tratamento seguro de erros.

## Critério de saída

Atender os critérios transversais relacionados a:

- autenticação;
- autorização no backend;
- default deny;
- auditoria;
- erros seguros;
- proteção de credenciais.

---

# F2 — Cadastros Fundamentais

**Complexidade:** baixa → média  
**Objetivo:** entregar o primeiro núcleo funcional realmente utilizável.

## Escopo

- Departamentos;
- Categorias de Ativo;
- Status de Ativo;
- Localizações;
- Pessoas;
- Ativos;
- soft delete/inativação;
- unicidade de Patrimônio;
- unicidade de Service Tag;
- páginas Django Templates;
- HTMX onde aplicável;
- API DRF;
- autorização por perfil.

## Critério de saída

Concluir o núcleo de:

- RF-001 — Gestão de Inventário de Ativos;
- parte cadastral de RF-012 — Gestão Básica de Pessoas.

Ao final desta fase deve ser possível:

- autenticar;
- cadastrar Pessoa;
- cadastrar Ativo;
- editar;
- visualizar;
- inativar;
- consultar registros com autorização correta.

---

# F3 — Pesquisa, Filtros, Manutenção e Garantias

**Complexidade:** média  
**Objetivo:** ampliar o valor operacional sem introduzir ainda os fluxos mais acoplados.

## Escopo

### Pesquisa e filtros
- Patrimônio;
- Service Tag;
- Número de Série;
- MAC;
- IP;
- hostname;
- responsável;
- departamento;
- status;
- filtros whitelistados;
- paginação server-side;
- índices necessários.

### Manutenção e garantias
- eventos de manutenção;
- datas;
- fornecedor;
- nota fiscal/serviço;
- defeito;
- acompanhamento de garantia.

## Critério de saída

Concluir:

- RF-003 — Pesquisa e Filtragem Avançada;
- RF-005 — Gestão de Manutenção e Garantias.

Preparar o sistema para validação futura do RNF-009.

---

# F4 — Arquivos e Evidências

**Complexidade:** média  
**Objetivo:** implementar armazenamento privado e seguro.

## Escopo

- entidade de metadados de arquivo;
- storage privado;
- arquivos fora do webroot;
- limite de 25 MiB;
- allowlist:
  - PDF;
  - JPG;
  - JPEG;
  - PNG;
- quarentena;
- MIME real;
- SHA-256;
- ClamAV;
- fail-closed;
- promoção atômica;
- vínculos com:
  - Ativos;
  - Manutenções;
  - Processos;
- download autorizado;
- `X-Accel` quando aplicável;
- bytes imutáveis quando disponíveis;
- nomes físicos por UUID;
- nomes originais apenas como metadados.

## Critério de saída

Concluir RF-011.

Testar:

- arquivo válido;
- extensão inválida;
- MIME divergente;
- malware;
- ClamAV indisponível;
- tentativa de download sem autorização;
- integridade por hash.

---

# F5 — Importação de Pessoas e Ativos

**Complexidade:** média → alta  
**Objetivo:** implementar entrada massiva de dados com segurança e atomicidade.

## Escopo

### Formatos
- CSV;
- XLSX.

### Entidades
- Pessoas;
- Ativos.

### Regras
- somente `CREATE`;
- sem update;
- sem upsert;
- sem merge;
- sem reativação;
- referências devem existir;
- sem fuzzy matching;
- sem autocriar catálogos;
- máximo 10 MiB;
- máximo 5.000 linhas;
- uma entidade por arquivo;
- um arquivo por importação;
- XLSX expandido até 100 MiB;
- fórmulas/macros rejeitadas;
- ClamAV obrigatório;
- preview;
- confirmação explícita;
- revalidação;
- transação atômica;
- all-or-nothing;
- rollback em conflito concorrente;
- cleanup de temporários;
- auditoria agregada.

## Ordem interna

1. CSV;
2. validação;
3. preview;
4. confirmação;
5. transação atômica;
6. XLSX;
7. segurança adicional de XML/conteúdo ativo.

## Critério de saída

Atender:

- CA-IMP-001;
- CA-IMP-002;
- CA-IMP-003;
- CA-IMP-004;
- CA-IMP-005.

---

# F6 — Modelos de Termo e Termos Imutáveis

**Complexidade:** média → alta  
**Objetivo:** construir o núcleo documental antes dos processos de entrega e devolução.

## Escopo

### ModeloTermo
- Administrador:
  - consultar;
  - criar;
  - editar;
  - inativar;
- Operador:
  - consultar;
  - editar modelo existente;
  - não criar;
  - não inativar.

### Termo
Estados:

```text
EM_EDICAO
AGUARDANDO_ASSINATURAS
ASSINADO
CANCELADO
```

### Regras
- edição apenas quando permitida;
- resolução de tags;
- `TermoItem`;
- snapshots;
- signatários;
- papéis;
- payload canônico;
- SHA-256;
- congelamento na emissão;
- imutabilidade após emissão/assinatura;
- correção via cancelamento + novo Termo.

## Critério de saída

Concluir:

- RF-006;
- RF-014.

Termos congelados não podem ser alterados in-place.

---

# F7 — Responsabilidade, Movimentações, Entrega, Devolução e Assinatura Presencial

**Complexidade:** alta  
**Objetivo:** implementar o principal fluxo transacional do domínio.

## Escopo

### ResponsabilidadeAtivo
- vínculo controlado por fluxo;
- não permitir edição direta;
- respeitar regras de simultaneidade.

### Movimentacao
- append-only;
- cronológica;
- sem UPDATE/DELETE operacional;
- correções por novo evento.

### ProcessoMovimentacao
Wizard em sete etapas:

1. Contexto;
2. Responsável;
3. Ativos/acessórios;
4. Condições/observações;
5. Termo;
6. Signatários/método;
7. Revisão.

### Entrega
- um ou mais ativos;
- responsável;
- local;
- data;
- acessórios;
- acompanhantes;
- condições;
- Termo;
- signatários.

### Devolução
- conferência;
- divergências;
- avarias;
- participantes;
- assinatura;
- encerramento de responsabilidade;
- alteração automática de status conforme regra de negócio.

### Assinatura presencial
- interface isolada;
- sem shell administrativo;
- reautenticação ao retornar à área administrativa.

### Dashboard operacional
- ativos por status;
- garantias a vencer em 30 dias;
- Termos pendentes de assinatura.

## Critério de saída

Concluir:

- RF-004;
- RF-007;
- RF-008;
- RF-010;
- RF-013.

---

# F8 — Assinatura Externa por E-mail

**Complexidade:** alta  
**Objetivo:** adicionar aceite eletrônico externo sem alterar o núcleo de Termos.

## Escopo

- templates versionados;
- `password_reset`;
- `term_signature`;
- fake SMTP nos testes;
- Resend somente quando permitido;
- token individual de 256 bits;
- token one-time;
- validade de 48h;
- armazenamento somente por hash;
- token no fragmento;
- troca do segredo por sessão temporária via POST;
- remoção do fragmento;
- sessão externa isolada;
- confirmação dos últimos 4 dígitos;
- limite de 5 tentativas;
- aceite somente via POST explícito;
- operação transacional;
- idempotência;
- CSRF;
- evidências:
  - pessoa;
  - snapshots;
  - papel;
  - método;
  - hash;
  - UTC timestamp;
  - IP;
  - User-Agent;
  - e-mail quando aplicável.

## Critério de saída

Concluir RF-009.

O uso produtivo do Resend permanece condicionado às pendências jurídicas/documentais já previstas.

---

# F9 — Endpoint Mínimo Funcional

**Complexidade:** alta  
**Objetivo:** estabelecer a primeira comunicação segura real entre Windows e GATI.

## Walking Slice

```text
Windows Service
    ↓
Enrollment
    ↓
Credencial
    ↓
Heartbeat
    ↓
Servidor GATI
```

## Escopo

### Servidor
- Endpoint;
- EndpointEnrollment;
- EndpointCredential;
- enrollment pré-autorizado;
- vinculação a Ativo;
- bootstrap token;
- armazenamento por hash;
- revogação;
- consulta por RBAC.

### Agente Windows
- C# 14;
- .NET 10.x LTS;
- Worker Service;
- Windows Service;
- sem GUI obrigatória;
- sem porta inbound;
- `agent_instance_id`;
- `endpoint_id`;
- DPAPI;
- ACL;
- heartbeat.

### Estados
- ONLINE;
- DEGRADED;
- OFFLINE.

## Critério de saída

Um Endpoint de laboratório deve:

- instalar;
- realizar enrollment;
- receber credencial;
- autenticar;
- enviar heartbeat;
- ser exibido corretamente no GATI;
- poder ser revogado.

---

# F10 — Coleta Técnica e Protocolo Completo do Endpoint

**Complexidade:** alta → muito alta  
**Objetivo:** concluir o RF-002 e tornar o agente resiliente.

## Escopo

### Coleta
- IP;
- MAC;
- hostname;
- SO;
- hardware;
- drivers;
- demais dados definidos.

### Protocolo
- `collection_id` UUID;
- `sequence` monotônico;
- precedência de dados do Endpoint;
- idempotência;
- rejeição de snapshot antigo;
- polling;
- heartbeat;
- offline;
- coalescing;
- outbox durável;
- quota;
- retry com jitter;
- timeouts;
- rotação de credenciais;
- sobreposição de credenciais;
- revogação;
- comandos at-least-once;
- `command_id`;
- deduplicação;
- estados de comando;
- atualização segura do agente.

## Critério de saída

Concluir RF-002.

Testar:

- enrollment;
- rotação;
- revogação;
- reconexão;
- offline;
- duplicação;
- sequence fora de ordem;
- replay;
- agente atualizado;
- credencial inválida.

---

# F11 — Web Scraping Dell e Lenovo

**Complexidade:** muito alta  
**Objetivo:** descobrir candidatos de drivers sem iniciar instalação automática.

## Escopo

### Providers
- `DellScrapingProvider`;
- `LenovoScrapingProvider`.

### Estratégia
- HTTP-first;
- requests;
- BeautifulSoup;
- Playwright somente quando necessário;
- Chromium headless isolado.

### Segurança e resiliência
- hosts em allowlist;
- redirects em allowlist;
- DOM tratado como não confiável;
- sem segredos da aplicação no browser;
- retry apenas transitório;
- respeitar `Retry-After`;
- suspender provider em:
  - CAPTCHA;
  - WAF;
  - 403 persistente;
  - quebra estrutural;
- proibir:
  - captcha solver;
  - proxy rotation;
  - stealth;
  - spoofing de fingerprint;
  - APIs privadas não documentadas.

### Execução
- management command `scrape_drivers`;
- agendamento por systemd timer;
- execução controlada;
- sem paralelismo agressivo.

## Critério de saída

Concluir RF-015.

Testar:

- fixtures determinísticas;
- mudanças de DOM;
- provider indisponível;
- CAPTCHA/WAF;
- URLs fora da allowlist;
- deduplicação;
- smoke live controlado.

---

# F12 — Pacotes, Autorização e Instalação de Drivers

**Complexidade:** muito alta / crítica  
**Objetivo:** implementar a feature tecnicamente mais sensível do MVP.

## Fluxo oficial

```text
Candidato
    ↓
Download controlado pela VPS
    ↓
SHA-256 congelado
    ↓
Pacote privado
    ↓
Autorização humana
    ↓
Agendamento
    ↓
Download autenticado pelo Endpoint
    ↓
Trust / Preflight Windows
    ↓
Executor privilegiado restrito
    ↓
Instalação
    ↓
Post-check
    ↓
Rollback controlado quando aplicável
```

## Development Units sugeridas

### DU-F12.1 — Preparação do pacote
- URL HTTPS;
- allowlist;
- streaming;
- limite de 2 GiB;
- SHA-256;
- storage privado;
- pacote `PRONTO`.

### DU-F12.2 — Autorização e agendamento
- ação humana autenticada;
- janela de execução;
- `not_before`;
- `expires_at`;
- auditabilidade.

### DU-F12.3 — Download pelo Endpoint
- somente pela API GATI;
- validar tamanho;
- validar SHA-256;
- validar target.

### DU-F12.4 — Preflight
- OS;
- arquitetura;
- `device_instance_id`;
- hardware IDs;
- aplicabilidade;
- assinatura;
- publisher.

### DU-F12.5 — Driver Executor
- Windows Service separado;
- LocalSystem;
- sem rede;
- sem Bearer;
- named pipe;
- ACL restritiva;
- operações enumeradas;
- sem shell arbitrário.

### DU-F12.6 — Instalação
Perfis fechados:

```text
PNP_INF
DELL_DUP_DRIVER
LENOVO_PROFILED_DRIVER
MANUAL_ONLY
```

Proibido:

- force;
- downgrade;
- raw shell arguments;
- BIOS;
- firmware;
- apps OEM;
- boot/storage critical automatizados.

### DU-F12.7 — Post-check e reboot
- saúde mínima;
- dispositivo;
- driver;
- `reboot_policy = NEVER_AUTO`;
- estado `AGUARDANDO_REINICIO`.

### DU-F12.8 — Rollback
- best-effort;
- `DiRollbackDriver` quando possível;
- sem remoção destrutiva automática;
- estados de erro visíveis;
- intervenção humana quando necessária.

## Critério de saída

Concluir RF-016 em Windows Lab descartável.

Validar:

- sucesso;
- falha;
- timeout;
- reboot;
- reinício de serviço;
- comando duplicado;
- perda de comunicação;
- trust failure;
- rollback;
- falha de rollback;
- intervenção manual.

---

# F13 — Hardening, Staging, Homologação e Go-Live

**Complexidade:** muito alta / longa  
**Objetivo:** validar o sistema completo em ambiente representativo antes da produção.

## Escopo

### Observabilidade
- Prometheus;
- Grafana;
- node_exporter;
- postgres_exporter;
- métricas da aplicação;
- dashboards;
- alertas;
- health checks.

### Backup e restore
- PostgreSQL;
- arquivos permanentes;
- snapshots;
- manifests;
- hashes;
- restore mensal;
- simulação trimestral;
- backup pré-deploy quando necessário.

### Segurança
- revisão OWASP ASVS 5.0 L2 aplicável;
- ZAP baseline;
- autenticação;
- RBAC;
- CSRF;
- uploads;
- SSRF;
- redaction;
- proteção de secrets;
- verificação de logs.

### Staging
- ambiente separado;
- dados sintéticos;
- HTTPS;
- `DEBUG=False`;
- PostgreSQL próprio;
- capacidade representativa;
- texto persistente de homologação.

### Performance
- RNF-009;
- dataset sintético representativo;
- perfil de carga documentado.

### Windows Lab
- MSI;
- Endpoint;
- drivers;
- reboot;
- rollback;
- falhas privilegiadas.

### Produção
- VPS Hostinger;
- NGINX;
- TLS;
- firewall;
- Gunicorn;
- PostgreSQL;
- ClamAV;
- scraper;
- observabilidade;
- secrets;
- migrations;
- backup;
- promoção do mesmo digest homologado;
- deploy manual/autorizado.

## Critério de saída

O go-live somente ocorre quando:

- todos os critérios de aceite aplicáveis estiverem atendidos;
- pendências pré-go-live estiverem resolvidas;
- staging estiver homologado;
- performance estiver validada;
- Windows Lab estiver aprovado;
- backup/restore estiver testado;
- segurança estiver revisada;
- produção estiver autorizada.

---

# Ordem consolidada

```text
F0  Bootstrap / Walking Skeleton
 ↓
F1  Autenticação / RBAC / Auditoria / API Base
 ↓
F2  Pessoas / Ativos / Catálogos
 ↓
F3  Pesquisa / Manutenção / Garantias
 ↓
F4  Arquivos / Evidências / ClamAV
 ↓
F5  Importação CSV/XLSX
 ↓
F6  Modelos de Termo / Termos / Imutabilidade
 ↓
F7  Responsabilidade / Movimentações / Entrega / Devolução / Presencial
 ↓
F8  Assinatura Externa / E-mail
 ↓
F9  Endpoint: Enrollment + Heartbeat
 ↓
F10 Endpoint: Coleta + Resiliência + Comandos
 ↓
F11 Scraping Dell / Lenovo
 ↓
F12 Pacotes / Instalação / Rollback de Drivers
 ↓
F13 Hardening / Staging / Homologação / Go-Live
```

---

# Regras obrigatórias para todas as fases

Cada Development Unit deverá seguir:

```text
SPEC
 ↓
PLAN
 ↓
TASKS
 ↓
BASELINE
 ↓
IMPLEMENTAÇÃO
 ↓
TESTES DIRECIONADOS
 ↓
VERIFY
 ↓
REVISÃO DE SEGURANÇA
 ↓
REGRESSÃO
 ↓
DOCUMENTAÇÃO
 ↓
RASTREABILIDADE
 ↓
AVALIAÇÃO DO README
 ↓
COMMIT RECOMENDADO
```

## Antes da implementação

Confirmar:

- Fase/Subfase/DU;
- requisito;
- dependências;
- contratos;
- banco;
- API;
- segurança;
- testes;
- README;
- necessidade de ADR;
- baseline.

## Depois da implementação

Confirmar:

- testes direcionados;
- lint;
- typecheck quando aplicável;
- build;
- verify;
- segurança;
- regressões;
- documentação;
- rastreabilidade;
- README;
- status do commit.

---

# Primeira sequência de execução

A implementação deve começar por:

```text
DU-F0.1-01 — Inspeção completa do repositório
DU-F0.1-02 — Baseline do estado atual
DU-F0.2-01 — Walking Skeleton Django
DU-F0.2-02 — PostgreSQL + Migration Inicial + UsuarioTI
DU-F0.3-01 — Estrutura de Ambientes
DU-F0.4-01 — Testes + Verify
DU-F0.5-01 — GitHub Actions Inicial
```

Somente após esse conjunto estar saudável deve ser iniciada a F1.

---

# Observação sobre a fonte do projeto

Antes de modificar código, o repositório real do GATI deverá ser inspecionado.

Para cada item deste plano, o estado do código deverá ser classificado como:

- **IMPLEMENTADO**;
- **PARCIAL**;
- **AUSENTE**;
- **CONFLITANTE**;
- **BLOQUEADO**.

Nenhum requisito deve ser considerado implementado apenas por existir na documentação.

---

**Documento:** Plano de Fases de Desenvolvimento do GATI  
**Status:** Plano de implementação baseado na baseline documental do projeto
