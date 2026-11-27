# T01 — Parecer consolidado do gate de dependências e tecnologias

- Revisão inicial: 2026-11-26, checkpoints do SHA af04340e5fda9ac44d27e0169fcb9320e77ea9fc.
- Atualização de evidências: 2026-11-27, SHA `e78af56bde743d0cd87d88ded95032296c8ba756`; ver seção 8 (prevalece sobre estados históricos de CI).
- Autoridade: GATI-SPEC-TERM-002 v0.1.0 e plano de 2026-11-25, Task 01.
- Estado: **PARECER TÉCNICO PARCIAL; T01 NÃO APROVADA; T02 BLOQUEADA**.
- Escopo: evidências dos spikes, comparação/licenças, limites, riscos e ações de desbloqueio.
- Controle: não altera produção, migrations, dependências produtivas, serviços, contas ou visibilidade do repositório. A seção 8 registra apenas lock e CI do laboratório.

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

## 6. Incremento controlado — PoC Tiptap OSS 3.35.0 e dois motores PDF ricos (26/11/2026)

### Editor Tiptap headless (SEM integração produtiva)
- Componentes experimentais em `backend/tests/fixtures/term_v2/tiptap_poc/`: schema Tiptap/ProseMirror real, versão de documento 2, tabela com 100 linhas, heading/paragraph, marcas bold/italic/underline, variável selecionada do catálogo, nó patrimonial atômico, isolado e não arrastável, imagem apenas com UUID de recurso **explicitamente autorizado**, sem URL/src e sem HTML/CSS livre.
- Testes Node: **10 casos** de serialização, preservação do bloco, edição no entorno, exclusão/duplicação, recursos aprovados, tentativa de SSRF e catálogo por classificação. [RED pela ausência do módulo](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45841371577), [GREEN dos testes no código corrigido](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45842106373). Estes são testes de schema/headless, **não** prova visual de WYSIWYG, colagem complexa, acessibilidade de leitor de tela ou imagem renderizada no editor.
- Pacotes Tiptap OSS na versão exata `3.35.0` (core, PM e extensões modulares, incluindo TableKit); registro de 26 pacotes transitivos MIT no lock experimental do runner, artefato Actions. O SHA-256 do lock gerado é checado pelo CI; **o lock completo ainda não está versionado no Git** e precisa ser incorporado antes de escolher dependência definitiva. Nenhum recurso Pro/Cloud ou licença paga foi instalado. Auditar licenças e CVEs do conjunto efetivo ao decidir.
- Ruling: esquema do editor rico **não substitui** `editor_spike/schema.py` v1 (a aplicação não o utiliza). Evolução para schema v2 exigirá migrations/versões, roundtrip com validador Python do lado do servidor, imagens após scanner/quarentena, validação de estados de publicação e E2E navegador; bloco patrimonial deve sempre ser regenerado de snapshot autorizado na emissão. O guard cliente só reduz edições acidentais.

### Renderização paginada: ReportLab × WeasyPrint (SEM integração produtiva)
- Código em `backend/tests/fixtures/term_v2/rich_pdf_spike.py`, 5 testes de PDF rico em `tests/test_term_v2_rich_pdf_spike.py` e 2 testes de métricas em `tests/test_term_v2_rich_pdf_benchmark.py`. Comparação de A4 com **100 ativos, 10 signatários**, tabela dividida entre páginas, imagem PNG sintética embutida e rodapé com contagem. A entrada é uma estrutura explicitamente permitida; não interpreta HTML fornecido pelo usuário.
- Validação local de laboratório em Python 3.13.5: **5/5 testes básicos aprovados**, ReportLab 4.4.9 gerou 5 páginas (7.780 bytes), WeasyPrint 68.0 gerou 6 páginas (19.561 bytes); inspeção visual pontual da primeira e última páginas mostrou cabeçalho, tabela e rodapé legíveis. **Não são resultados do CI oficial**, nem ensaio de concorrência, longa duração, PDF/A ou aprovação de layout final. A versão do runner CI está fixada em WeasyPrint `70.0`, sujeita a evidência própria.
- O código WeasyPrint constrói HTML exclusivamente com textos escapados e CSS embutido fixo; o `URLFetcherResponse` customizado só retorna uma imagem PNG aprovada por ID opaco e URI exata. Não chama `default_url_fetcher`, rejeita `http(s)`, `file:`, campos desconhecidos e ausência de imagem aprovada. O ReportLab usa `Paragraph` com escape e `LongTable(repeatRows=1)`. Isso é defesa do PoC; ameaças de conversão de SVG, fontes, recursos de modelo e upload ainda exigem revisão antes de produção.
- O CI mede CPU, pico RSS, latência e páginas em processos Linux separados, registra PDF e JSON para cada motor e submete ambos à classificação PDF/A-2b independente com veraPDF. **Não declarar esses resultados ou conformidade antes de concluir o workflow**.
- A validação PDF/A vigente dos quatro PDFs simples ainda é **não conforme**. Mesmo que um dos PDFs ricos alcance conformidade, exigir contrato de metadados/retention e repetição independente antes de tomar decisão sobre PDF/A.

### Estado e próximo gate
**T01 EM AVALIAÇÃO; T02 BLOQUEADA.** Critérios ainda abertos: CI completo do último SHA, integração Tiptap real em navegador e servidor, comparação visível de todos os PDFs, benchmark de concorrência/limites, formato de PDF escolhido/licenças finais, storage R2 real com política aprovada, infraestrutura do worker, governança e aceite. Nenhum merge/deploy/provisionamento executado.

## 7. PoC visual Tiptap — Chromium real e contrato Python isolado (26/11/2026)

**Evidência GREEN:** [Núcleo Patrimonial, commit `927b0f0`, execução #45863153297](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45863153297): 299 testes coletados, **297 aprovados, 2 ignorados, 0 falhas**, com 1 aviso conhecido do WeasyPrint; Ruff, checks/migrations, Docker e medição PDF mantidos. [Segurança GREEN, execução #45863153300](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45863153300). Cobertura da aplicação 88,77% linhas e 74,40% ramificações. Ambos os PDFs ricos seguem **não conformes** ao PDF/A-2b.

**Implementação isolada:** `backend/tests/fixtures/term_v2/tiptap_poc/visual.html`, `visual.css`, `visual_app.mjs` e `rich_schema.py`; harness em `backend/tests/test_term_v2_tiptap_visual_browser.py`. Um bundle local do Tiptap 3.35.0 é gerado com esbuild 0.27.0 no CI, injetado no Chromium/CDP com URLs HTTP(S) bloqueadas. O HTML/CSS seguem Enterprise Blue. O screenshot real do CI foi inspecionado em **375 e 1366 px**; campos dinâmicos e bloco patrimonial são visualmente distintos, com folha A4 e barra de edição. O teste verifica layout em **320, 375 e 1366 px**, incluindo fonte raiz a **200%**, foco e botões nomeados.

**TDD com falhas observadas:** no primeiro código visual, [execução #45861514017](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45861514017), 295 testes passaram e dois falharam no E2E: overflow da página a 320 px/200% e imagem não inserida depois da tabela. A correção de inserção no final do documento revelou um segundo defeito, serialização de atributos padrão de células; as execuções [#45861945790](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45861945790) e [#45862294103](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45862294103) reproduziram os problemas. Diagnósticos medidos isolaram o overflow no `H1` da página (309 px de conteúdo para 273 px disponíveis), e o atributo ProseMirror `align: null`; [commit 927b0f0](https://github.com/Miranda-txt/G.A.T.I/commit/927b0f0828e97a27245014a16194897c862c268d) resolve ambos sem suprimir testes nem mascarar overflow, e mantém a rejeição de atributos fora da allowlist.

**Capacidades comprovadas:** editor Tiptap real com marcação bold, undo/redo, inserção de tabela e nó de recurso com UUID aprovado, nenhum `src` remoto, bloqueio de deleção do bloco patrimonial pelo filtro ProseMirror, JSON estruturado v2 e roundtrip contra validador Python de testes. O recurso é representado por placeholder; **não há busca, renderização de imagem real ou autorização Django**. A serialização omite apenas atributos padrão conhecidos das células, e o servidor experimental recusa atributos desconhecidos, imagens não autorizadas e bloco duplicado.

**Limitações decisivas:** não implementa o editor da aplicação nem integra Django; não há autenticação/autorização do usuário, banco de dados, persistência, workflow de assinaturas, emissão ou deploy. Não há certificação WCAG, teste de leitores de tela, IME, toque real, modelagem de conteúdo arbitrário, redimensionamento de tabela, validação completa de clipboard rico nem reconciliação com o schema v1. Capturas são evidência visual pontual, não aprovação de acessibilidade. esbuild é fixado no comando mas não bloqueado em lock transitivo definitivo. Testes externos seguem exigindo Python 3.14/PostgreSQL 18 e dependências de laboratório.

**Ruling:** a PoC visual de Tiptap OSS passou seus gates de laboratório; **não aprovar Tiptap para T04 apenas com esses resultados**. Próximos gates: serialização rica compatível com backend e classes de conteúdo reais, sanitização cross-browser, acesso a recursos com scanner/quarentena, ergonomia de edição complexa, licença/SCA e build fixo, teste com tecnologia assistiva, aceitação de runtime/storage e assinatura do ADR. **T01 em avaliação; T02 bloqueada**.

## 8. Contrato adversarial GREEN, revisão e lock experimental — 27/11/2026

**Referência verificável:** `e78af56bde743d0cd87d88ded95032296c8ba756`.
[Núcleo Patrimonial #45995627126](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45995627126)
e [Segurança #45995627009](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45995627009)
concluídos com sucesso. Python 3.14.10 / PostgreSQL 18.6; 322 coletados,
320 aprovados, 2 smoke ClamAV real ignorados, 1 aviso, 0 falhas;
33/33 testes Node Tiptap (23 casos do corpus compartilhado) e 4/4 Node
do editor inicial; 193 arquivos formatados; Ruff lint, Chromium, Django
check/migrations, OpenAPI, build Docker e scanners aprovados. Cobertura
global 88,77% linhas / 74,40% ramificações.

- RED: `30c7cdc` e `a71b539` (ampliação para 23 casos; [CI #45994004106](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45994004106), 24/33 Node, 9 falhas).
- Correção autorizada: `8699fcf` (33/33 Node; CI interrompido por formatação, [#45995238715](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45995238715)).
- GREEN integral: `e78af56`, ajuste exclusivo de formatação. O contrato exige raiz doc, UUID v4 canônico, ausência distinta de null, pontos de código Unicode, rejeição de controles/substitutos isolados, tipos malformados e alt não vazio. O servidor é autoridade; nenhum endpoint Django foi implementado.
- Revisão técnica **pelo próprio implementador**, sem subagente independente disponível: leitura dos validadores e teste compartilhado. A equivalência é limitada ao corpus. Em particular, JSON com números integrais escritos como 2.0/2e0 pode ser aceito pelo JS e recusado pelo Python (type int); não é bypass do servidor, mas exige contrato de fronteira HTTP e regressão antes de integração. Tabelas com linhas de comprimentos distintos não são proibidas pelos guardas atuais; a política de tabelas e a renderização fiel devem ser testadas no spike JSON→PDF. O guard do cliente verifica unicidade/payload, não posição imutável; regenerar bloco de snapshot autorizado. Limites permanecem experimentais. Nenhum parecer independente ou WCAG certificado.

### Lock experimental versionado

- Fonte: [artefato 15196270278](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45995627126/artifacts/15196270278), baixado e inspecionado. ZIP contém somente package-lock.json, 13.025 bytes, lockfileVersion 3, SHA-256 `d2fbff6856b4c7a3894eded3493487df9fb206a13fbcf483db5276053e2fc788`, Git blob `53a292756c179c357344f552ed5d77136966800d`.
- 26 pacotes (10 Tiptap diretos e 16 transitivos), todos com versão, integridade SHA-512 e metadado de licença MIT no lock. O npm audit do CI de referência reportou 0 vulnerabilidades; isso não substitui revisão dos arquivos LICENSE, advisories futuros, SBOM e auditoria da cadeia de build.
- Ruling: versionar **exatamente** o lock já testado, sem atualizar pacote ou alterar dependência produtiva; retirar apenas a regeneração do lock no CI, preservar verificação SHA-256, npm ci e audit, e verificar que o lock não foi modificado. Custo residual: novo CI precisa validar checkout/instalação; esbuild 0.27.0 continua fixado no comando e fora do lock, portanto o build completo ainda não é reproduzível. Não implica aprovação definitiva do editor.

### PDF: medição atualizada, ainda sem JSON rico direto

Dados do mesmo CI, 100 ativos/10 signatários, cinco repetições por motor:

| Motor | Mediana wall (ms) | Mediana CPU (ms) | Pico RSS (KiB) | Páginas | Bytes |
|---|---:|---:|---:|---:|---:|
| ReportLab 5.1.2 | 47,899007 | 47,883607 | 80.532 | 5 | 7.780 |
| WeasyPrint 70.0 | 538,841959 | 539,079835 | 117.008 | 6 | 25.184 |

[Artefato de evidências 15196076638](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45995627126/artifacts/15196076638).
Os quatro PDFs simples e os dois ricos permanecem não conformes ao PDF/A-2b
no veraPDF; sucesso operacional do job não é aprovação arquivística.
Não usar a mediana isolada como SLA nem declarar fidelidade do editor:
o fixture atual não consome diretamente o schema Tiptap v2.

**Gate:** T01 permanece em avaliação; T02 bloqueada. Próximos incrementos
isolados: validar o novo CI com lock versionado, fechar o lock/auditoria
da ferramenta de build, prova direta JSON v2 validado → PDF com
variáveis/snapshot/recursos controlados e inspeção de todas as páginas,
limites e concorrência; homologação de storage privado real e execução
do worker dependem de ambiente/decisão autorizados; decisão final do ADR
e limites aprovados. Sem merge, deploy, provisionamento ou alteração
de dependências produtivas. O presente registro não declara T01 concluída.

## 9. Lock do editor GREEN e bootstrap do lock de build — 27/11/2026

[Núcleo Patrimonial #45996893701](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45996893701)
e [Segurança #45996893727](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45996893727)
no SHA `1f79229bea0d092d267d2ce2f0a6eb6c571730b0`: GREEN, hash do lock
OK, npm audit 0 vulnerabilidades reportadas, 33/33 Node Tiptap, 4/4 Node
inicial, 322 coletados, 320 Pytest aprovados, 2 smoke ClamAV ignorados,
1 aviso, cobertura 88,77% / 74,40%, Ruff, migrations, OpenAPI e Docker
aprovados. A instalação do lock Tiptap versionado está comprovada.

Ruling: manter esbuild 0.27.0 (versão já utilizada), em manifesto npm
separado `tiptap_poc/build_tools/package.json`, para não alterar as
26 dependências já validadas do editor. A rede local não resolve
registry.npmjs.org; RED local de npm ci sem lock = EUSAGE, exit 1.
Usar o runner de CI existente para gerar lock **temporário** uma vez,
instalar sem lifecycle scripts, auditar todos os pacotes do build,
publicar SHA-256/SBOM CycloneDX/audit e executar o bundle com o esbuild
local. Nenhum npm exec dinâmico durante o build. Custo residual: o
bootstrap ainda resolve o lock no runner; só concluir após recuperar,
versionar e verificar o lock em novo CI sem resolução dinâmica.
Não atualizar versões, não instalar no runtime produtivo, não contratar
serviços. Sem garantia de build bit a bit, pois Node/npm e runner
ainda podem variar. T01 em avaliação; T02 bloqueada.

## 10. Lock do build recuperado e versionado — 27/11/2026

O bootstrap de `9b28b3e` ficou GREEN em
[Núcleo Patrimonial #45998560696](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45998560696)
e [Segurança #45998560698](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45998560698).
320 Pytest aprovados, 2 ignorados, 33/33 Node Tiptap, 4/4 Node inicial;
Node 24.22.3 / npm 11.19.1, esbuild 0.27.0, bundle 792,4 KiB (valor
reportado pelo esbuild: 792.4kb), Chromium e build Docker aprovados.
O [artefato 15197072306](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45998560696/artifacts/15197072306)
foi baixado e inspecionado: lockfileVersion 3, 13.991 bytes, 27 pacotes
(1 esbuild e 26 binários opcionais de plataforma, todos MIT segundo
metadados do lock), integridades SHA-512, SBOM CycloneDX 1.5 com 27
componentes, npm audit 0 vulnerabilidades reportadas.
SHA-256 `15eb0b6d9f9203c0744f5038d03472320055d3166a1a070a7fdfece9fa04fed5`; Git blob `6f71b4ae6217f24e8d0b73e72294c54bbbd400b3`.
O blob enviado foi conferido contra o arquivo do artefato.

Ruling: versionar o lock e o arquivo SHA-256 exatos do CI GREEN, sem
alterar versões. Remover a geração dinâmica do lock; preservar npm ci
sem scripts, auditoria, SBOM, verificação do hash antes/depois,
git diff dos locks e teste da versão do binário. O novo CI deve
confirmar o consumo do lock versionado. O log registrou aviso DEP0169
de url.parse() em processos Node do runner, sem falha; não atribuir
a origem ao esbuild sem investigação. Node/npm e ubuntu-latest ainda
podem variar, portanto não afirmar reprodutibilidade bit a bit.
Metadados de licença e auditoria pontual não substituem revisão
de licenças, SBOM do editor completo e monitoramento de advisories.
Não há alteração de dependências produtivas ou liberação de T02.

**Próximo gate:** após GREEN do lock de build versionado, iniciar prova JSON rico Tiptap v2 → PDF diretamente do contrato Python, com resolução de variáveis, snapshot e recursos autorizados; sem adoção definitiva de motor ou alteração produtiva.

## 11. Spike JSON v2 para PDF — 27/11/2026

CI de dfc7fe0 GREEN: 320 Pytest, 2 ignorados, 33 Node Tiptap, locks íntegros e auditoria npm sem vulnerabilidades reportadas. Novo spike isolado consome o validador Python existente, snapshot sintético e imagens aprovadas. RED local: 26 falhas por capacidade ausente; GREEN 26/26. Revisão visual identificou divisão de signatários: 3/4 testes adicionais falharam; correção e GREEN local 30/30. Python 3.13.5, ReportLab 4.4.9, WeasyPrint 68.0, pypdf 5.9.0, Pillow 12.3.0; versões diferentes do CI. Ruff indisponível localmente. CI integral pendente.

Ruling: usar fontes Vera já distribuídas pelo ReportLab, rejeitar glifos não suportados em vez de perda silenciosa, tabelas não retangulares e cabeçalhos mistos, PNG de até 1 MiB e 512 px por dimensão, até 8 recursos no catálogo. Limites exclusivamente experimentais; podem restringir conteúdo válido no editor, exigindo revisão antes de integração. Snapshot reduzido de laboratório, não contrato definitivo de domínio. Nenhuma dependência produtiva alterada. Teste de socket não equivale a isolamento de rede por processo. PDF comum, não PDF/A. Pendentes: inspeção final em CI, fontes/licenças, limites de páginas/tempo, concorrência, paridade de schema, segurança de recursos reais e homologação dos motores. T02 bloqueada.

## 12. Benchmark direto JSON v2 — 27/11/2026

GREEN confirmado em 5c1556b: [Núcleo Patrimonial](https://github.com/Miranda-txt/G.A.T.I/actions/runs/46007623418) e [Segurança](https://github.com/Miranda-txt/G.A.T.I/actions/runs/46007623382). 350 Pytest aprovados, 2 ignorados, 1 aviso, 30/30 conversor, 33/33 Tiptap, 195 arquivos formatados, cobertura 88,77%/74,40%.

Coletor isolado por cenário: RED 7 falhas pela ausência do coletor; GREEN local 37/37 incluindo 30 regressões do conversor. Matriz 16 cenários (2 motores, 2 orientações, 1/100 ativos, 1/10 signatários), 5 amostras medidas e uma inicial por cenário. Cada PDF inspecionado, SHA-256, dimensões, conteúdo, imagem e ausência de mutação do input. Todos os hashes repetidos coincidiram localmente, sem garantia entre ambientes. Python 3.13.5, ReportLab 4.4.9, WeasyPrint 68.0; adaptação local da sintaxe PEP 758, sem Ruff disponível. CI usa versões distintas.

| Máximo | ReportLab mediana ms | WeasyPrint mediana ms | Páginas RL/WP |
|---|---:|---:|---:|
| Retrato | 34,96 | 331,57 | 4/5 |
| Paisagem | 32,12 | 327,09 | 7/7 |

RSS retrato 139,15/178,23 MiB do processo completo (ambos motores importados, inspeção incluída); bytes 70.280/21.048. Medições sequenciais, sem SLO, sem p95/p99 confiáveis. Ruling: manter cinco repetições por cenário no CI para limitar custo, preservar amostras brutas e validar PDF/A-2b nos quatro casos máximos com veraPDF existente. Não adotar motor definitivo, não alterar dependências produtivas. CI deste incremento pendente. Concorrência, limites adversariais, fidelidade visual e armazenamento/worker ainda pendentes. T02 bloqueada.

## 13. Capacidade concorrente experimental — 27/11/2026

GREEN confirmado em 152e609: [Núcleo Patrimonial](https://github.com/Miranda-txt/G.A.T.I/actions/runs/46010947982) e [Segurança](https://github.com/Miranda-txt/G.A.T.I/actions/runs/46010947789). 357 aprovados, 2 ignorados, 1 aviso, 197 arquivos formatados, cobertura 88,77%/74,40%. Os quatro PDFs JSON máximos foram classificados como não conformes PDF/A-2b.

| Motor | Retrato mediana ms | Paisagem mediana ms | RSS retrato KiB |
|---|---:|---:|---:|
| ReportLab 5.1.2 | 27,690357 | 29,817211 | 84220 |
| WeasyPrint 70.0 | 152,984797 | 160,564632 | 104020 |

ReportLab manteve hashes nas repetições máximas; WeasyPrint não. Não exigir regeneração idêntica: preservar bytes emitidos e hash. PDF comum é fallback previsto, sem aprovação definitiva.

Ruling: envelope experimental Linux por processo de 512 MiB de espaço virtual (não RSS), 10 s CPU, 30 s wall, 5 MiB por arquivo, 50 páginas verificadas após geração, dois processos simultâneos. Oito jobs em quatro pares, cada um com duas medições e uma inicial. Limites não são SLO nem capacidade comprovada do Render. RED local 11 falhas por ausência do coletor; GREEN 11/11; teste adicional de registro de falhas RED 1 falha/1 aprovado; GREEN final 13/13, compileall aprovado. Matriz local usa benchmark sintético substituto, não motores reais; CI executará benchmark real. Sem checkout integral local por DNS indisponível, sem Ruff/Python 3.14/Django local; baseline remota GREEN. Revisão própria, sem subagente. Limites por processo não equivalem a cgroups, isolamento de rede ou sandbox de filesystem; saída de diagnóstico descartada, código de retorno registrado. Limite de páginas posterior à geração; não protege sozinho contra consumo durante renderização. Pendentes: carga adversarial documental, isolamento real, fidelidade visual, armazenamento e worker. T01 aberta, T02 bloqueada.

## 14. Correção do teste de RLIMIT_FSIZE — 27/11/2026

[Núcleo Patrimonial #46016650040](https://github.com/Miranda-txt/G.A.T.I/actions/runs/46016650040) RED em d709cae: 369 aprovados, 1 falha, 2 ignorados, 1 aviso. [Segurança #46016650262](https://github.com/Miranda-txt/G.A.T.I/actions/runs/46016650262) GREEN. Ruff aprovado. A matriz concorrente real ainda não executou.

Falha: uma única escrita buffered de 8192 bytes com RLIMIT_FSIZE=1024 retornou exit 0 no CI Python 3.14.10. O log não informa quantos bytes foram efetivamente gravados porque a assertion de status precedia a inspeção do arquivo. Investigação local Python 3.13.5: a expressão buffered original retorna EFBIG; a escrita bruta única de 8192 bytes retorna 1024 e exit 0, com arquivo de 1024 bytes; nova escrita retorna EFBIG e exit 1. Logo, exit 0 de uma escrita isolada não demonstra violação do limite. Não atribuir uma causa interna específica ao CPython sem evidência adicional.

Ruling: separar limite exato, escrita parcial e tentativa posterior acima do limite com I/O sem buffering; verificar o conteúdo completo do arquivo (1024 bytes) e código de saída. Adicionar rejeição de PDF truncado com metadados originais. Sem alterar o coletor, os limites, controles produtivos ou workflow. Mutação local em cópia isolada, removendo --fsize: 2 falhas esperadas, 1 aprovado; restauração do blob 1772f50829339e55003975c92cc5e385a1c29b76: 16/16 aprovados, compileall aprovado. Teste local não reproduz integralmente o CI Python 3.14; regressão completa e matriz real pendentes do novo CI. T01 aberta, T02 bloqueada.
