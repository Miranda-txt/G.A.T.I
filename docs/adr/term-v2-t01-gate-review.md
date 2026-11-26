# T01 — Parecer consolidado do gate de dependências e tecnologias

- Revisão: 2026-11-26, checkpoints do SHA af04340e5fda9ac44d27e0169fcb9320e77ea9fc.
- Autoridade: GATI-SPEC-TERM-002 v0.1.0 e plano de 2026-11-25, Task 01.
- Estado: **PARECER TÉCNICO PARCIAL; T01 NÃO APROVADA; T02 BLOQUEADA**.
- Escopo: evidências dos spikes, comparação/licenças, limites, riscos e ações de desbloqueio.
- Controle: não altera produção, migrations, lock, serviços, contas, CI ou visibilidade do repositório.

## 1. O que está comprovado no commit de referência

- [Núcleo patrimonial GREEN](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45837119927): 287 coletados, 285 aprovados, 2 ignorados (smoke ClamAV sem serviço real), 0 falhas; Python 3.14 e PostgreSQL 18; Ruff e build Docker aprovados; 88,77% linhas / 74,40% ramos (cobertura de toda a aplicação, não métricas isoladas dos spikes).
- [Segurança GREEN](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45837119978): scanners existentes SAST, SCA e segredos passaram. Scanner aprovado não elimina risco de novas dependências ou configurações futuras.
- Renderer simples: 4 combinações sintéticas (1 ou 100 ativos; 1 ou 10 signatários), 10 amostras por caso, CPU/RSS/latência/bytes/páginas, SHA-256 determinístico, fonte TrueType e texto pt-BR. [Artefato do benchmark](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45815496442/artifacts/15115656672). Perfis de páginas: 1, 3, 1, 3; latências medianas 3,413 / 11,721 / 3,779 / 12,095 ms; RSS máximo aproximado de 38 MiB em processos Linux isolados. Dados não provam SLA, imagens, anexos, tabelas ricas, concorrência ou grandes modelos.
- PDF/A-2b: **4/4 documentos experimentais não conformes** em validação veraPDF independente (cláusulas 6.1.7.1, 6.2.4.3 e 6.6.2.1). PDF comum é fallback permitido pela SPEC, mas **não** deve ser rotulado PDF/A.
- Editor experimental: schema JSON estrito, campos autorizados por classificação, proteção do bloco patrimonial, testes Python/Node e Chromium/CDP; colagem literal, navegação Tab, reflow 320/375/768/1366px e texto ampliado. Não testou editor Tiptap ou ProseMirror, imagens/tabelas ricas, undo/redo complexo, leitor de tela, IME, toque real ou preview paginado do backend.
- Storage: 26 testes com cliente S3/R2 **simulado** em memória, condicionais, idempotência, SHA-256, concorrência, corrupção, autorização simulada e falha remota. Não é teste de R2 real, bucket público, IAM, retenção, backup/restore ou SDK concreto.
- Worker: 10 testes novos contra PostgreSQL 18 de teste, com rollback, dedupe, claim SKIP LOCKED, lease/fencing, retries, expiração e sanitização de erros; tabela criada e descartada no fixture. Não há worker contínuo ou command produtivo, monitoramento, envio de e-mail ou execução em Render.
- Os testes e spikes ficam na árvore de backend/tests e backend/tests/fixtures/term_v2. O commit final contém ambos os arquivos de testes e suas implementações. Nenhuma dependência produtiva foi adicionada.

## 2. Matriz de decisão técnica — não equivale a aprovação

| Domínio | Evidência / alternativa | Licença e compatibilidade | Parecer / insuficiências |
|---|---|---|---|
| Editor rico | Tiptap OSS 3.x baseado em ProseMirror, candidato preferencial para **PoC**; ProseMirror direto como alternativa; contenteditable nativo já testado | Núcleo Tiptap MIT; uso de extensões OSS depende de validar cada pacote e sua licença; nenhuma versão foi fixada | **Não selecionado**. A PoC deve provar schema restrito, bloco não editável, tabela longa, imagem autorizada, estilos, undo/redo, paste, acessibilidade e serialização estável pt-BR. Nenhuma extensão paga/Cloud autorizada. |
| PDF original | ReportLab 5.1.2 em requirements-spike.txt somente; WeasyPrint (HTML/CSS paginado) como segunda candidata | ReportLab BSD, suporta Python 3.14 no experimento; WeasyPrint BSD-3 e Python >=3.11 segundo projeto; dependências nativas, fontes e cadeia de licenças pendentes | **Somente PDF simples experimental validado**. Avaliar tabela com 100 ativos e páginas repetidas, rodapé, imagens, página A4, limites CPU/RSS, fonte redistribuível e bloqueio de URLs/arquivos; PDF/A apenas com resultado independente conforme. |
| PDF final | pypdf 6.21.4 já no lock; preservar original e acrescentar evidência | Licença/versão do lock existente, sem escolha nova | Final, hashes e manifesto T07 ainda não implementados. PDFs originais não podem ser regenerados silenciosamente. |
| Storage privado | API S3/R2 simulada; boto3 como candidato SDK para PoC autorizada | boto3 Apache-2.0, declara compatibilidade Python >=3.10 incluindo 3.14; sem lock/instalação | **Sem aprovação de integração** até prova de PUT condicional real (412/409), leitura SHA-256, política default-private, IAM, R2 Bucket Lock, recuperação de falhas, backup/restauração e custo. |
| Outbox/worker | Django + PostgreSQL 18, sem broker | Stack já no lock; nenhuma nova dependência | **Mecanismo de banco viável** em teste. **Operação não aprovada** sem local de execução contínua autorizado, restart, health/alerta, fila de falhas, integração outbox e teste de interrupção. Render Free não é garantia de worker. |

**Fontes oficiais consultadas em 26/11/2026:** [Tiptap OSS](https://tiptap.dev/), [extensões Tiptap](https://tiptap.dev/docs/editor/extensions/overview), [tabelas Tiptap](https://tiptap.dev/docs/editor/extensions/tables), [ReportLab 5.1.2](https://pypi.org/project/reportlab/5.1.2/), [WeasyPrint licença](https://github.com/Kozea/WeasyPrint/blob/main/LICENSE), [WeasyPrint API de variante PDF](https://doc.courtbouillon.org/weasyprint/latest/api_reference.html), [boto3](https://pypi.org/project/boto3/), [R2 condicionais](https://developers.cloudflare.com/r2/api/s3/conditional-operations/), [R2 matriz S3](https://developers.cloudflare.com/r2/api/s3/api/), [R2 Bucket Locks](https://developers.cloudflare.com/r2/buckets/bucket-locks/), [R2 acesso público](https://developers.cloudflare.com/r2/buckets/public-buckets/), [Render Free](https://render.com/docs/free), [Render Workers](https://render.com/docs/background-workers). Conferir advisories e versões novamente quando o conjunto exato de dependências for escolhido; não deduzir ausência de CVE do GREEN do lock atual.

## 3. Rulings explícitos e trade-offs

**D-01 Editor:** priorizar PoC isolada de Tiptap OSS, sem instalação definitiva. O protótipo nativo não cobre autoria rica exigida em CA-TERM-05. Risco se errado: quebrar roundtrip ou tornar o bloco patrimonial editável.

**D-02 Renderer:** manter ReportLab apenas como candidato para PDFs simples. Testar WeasyPrint com entrada controlada (jamais HTML/CSS livre, fontes ou URLs externas), página A4, tabela quebrando página, cabeçalho/rodapé e recursos internos allowlistados. Embora a documentação de WeasyPrint descreva saída com variante PDF/A, a conformidade de qualquer arquivo GATI dependerá de veraPDF independente. Risco: dependências nativas, SSRF/file fetch, paginação e inconsistência visual.

**D-03 PDF/A:** aceitar tecnicamente **PDF comum como fallback da SPEC**, registrando o formato com precisão; não tentar reparar à força nem declarar PDF/A-2b. Risco: arquivo não satisfaz política arquivística que eventualmente exija PDF/A; antes do uso real validar com o responsável pelo acervo.

**D-04 R2:** manter R2 como storage previsto na SPEC, mas não selecionar SDK ou configurar bucket agora. A API S3 não implementa cabeçalhos S3 Object Lock, **porém R2 possui Bucket Lock por regras de prefixo/retention** (controle separado), com retorno 409 ObjectLockedByBucketPolicy; 412 é esperado em conflito de PUT condicional sem bloqueio por regra. Como regras podem ser geridas/removidas por contas autorizadas, não alegar equivalência WORM regulatória sem revisão jurídica/segregação IAM, auditoria e retenção. Risco: exclusão precoce ou indisponibilidade de dados; impedir exclusão operacional de evidências retidas.

**D-05 Worker:** manter sem Redis/Celery; a PoC demonstrou at-least-once, não exactly-once dos efeitos externos. Render Free pode suspender web services após 15 minutos ociosos e não constitui hospedagem de worker contínuo; não provisionar serviço pago, cron ou manter web service artificialmente ativo. Risco: convites/arquivamento demorarem e filas pararem silenciosamente.

**D-06 Segurança e governança:** repo atualmente **público** conforme GitHub (em conflito com a expectativa documental de privado); as alterações já autorizadas na branch não autorizam mudança de visibilidade, dados reais, novas credenciais, merge ou deploy. Avaliação institucional de LGPD, retenção e transferência internacional é gate de homologação produtiva; decidir quais permissões e políticas são exigidas antes de objetos reais.

## 4. Gates de decisão e plano de desbloqueio

| Prioridade | Gate pendente | Como verificar sem alterar produção | Evidência exigida para decisão |
|---|---|---|---|
| P0 | Editor rico OSS | PoC isolada com pacote pinado e SCA/licença; JSON ↔ schema Python, nó patrimonial travado, tabela longa, imagens internas, clipboard, undo/redo, Tab/IME e reflow | Tests RED/GREEN no CI + demonstração navegador; relação exata pacote/licença, sem Pro/Cloud |
| P0 | Renderer completo | PoC isolada comparando ReportLab/WeasyPrint com tabela longa, header/footer, recursos internos, 100 ativos, 10 signatários; canary e sandbox de rede/arquivo; medir p50/p95, CPU/RSS/páginas/bytes e imagens | PDF fixture revisado visualmente, hash, licença de fontes, consumo medido e resultado veraPDF se reivindicado |
| P0 | Execução contínua | Prova de ciclo de vida em ambiente **autorizado**, restart, failover/lease, scheduler, falha de SMTP, idade da fila e alertas, sem contratação implícita | Escolha operacional escrita + resultado de carga/recuperação e orçamento aprovado se houver custo |
| P0 | Storage privado de verdade | Ambiente R2 **descartável autorizado**, sem dados reais; testar IAM, negação anônima, PUT concorrente, 412/409, Bucket Lock, read-after-write, replay e hash; plano PostgreSQL ↔ R2 | Logs e política anonimizada, acesso público negado, retenção/proteção definida, restore verificado |
| P1 | Limites de produto | Reconciliar guardas experimentais (20 páginas renderer, 800 nós/64 KiB editor, 25 MiB storage, 100 ativos, 10 signatários) com os limites realmente aceitos pela SPEC | SLOs/limites validados com medições reproduzíveis e decisão registrada; não introduzir limites arbitrários como política |
| P1 | Licenças e segurança finais | Revisar licenças de fonte Bitstream Vera e extensões, transitive deps, SCA/SBOM e suporte Python 3.14, assets embutidos | Registro das versões e licenças efetivas; advisories e instalação reprodutível com lock apenas após aprovação |
| Governança | Aceite de ADR e visibilidade do repo | Revisão institucional do resultado e manutenção de branch isolada; confirmar autorização de visibilidade e tratamento de dados | Aprovadores, data e decisão explícita. Nenhuma aprovação tácita derivada do CI. |

**Nota de fronteira:** restore coordenado com dados reais, análise jurídica/LGPD e ensaios de produção completos também são gates das tarefas posteriores (especialmente T12–T14). A T01 deve definir arquitetura/risco e estratégia verificável; não afirmar que toda a homologação final já ocorreu neste spike.

## 5. Resultado do parecer e próximos incrementos

- **GO**: continuar ensaios controlados de editor rico e renderização paginada, aprovar desenho de contratos condicionais e levantar opção de hospedagem autorizada.
- **NO-GO**: declarar a T01 aprovada, iniciar T02, importar dependências definitivas, habilitar flag produtiva, tratar PDF como PDF/A, contratar recurso, alterar repo/infra, realizar merge ou deploy.
- Ordem sugerida: (1) PoC OSS do editor e renderer; (2) critérios/limites mensurados; (3) autorização para R2 e teste de storage com política; (4) decisão de runtime do worker; (5) registro de aprovação do ADR; (6) só então T02 de acordo com plano.
- Revalidar as referências e a evidência GREEN em SHA específico após qualquer commit. Este documento não constitui aceite pelo usuário nem laudo de conformidade WCAG, PDF/A, LGPD ou retenção.

Assinaturas/decisão: **PENDENTES** — responsável técnico, responsável de operação, responsável institucional por retenção e patrocinador do escopo conforme governança do GATI.
