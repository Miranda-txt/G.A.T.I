# ADR — Capacidades técnicas de Termos e Empréstimos V2

- Data: 25/11/2026
- Estado: **EM AVALIAÇÃO — não aprovado**
- SPEC: GATI-SPEC-TERM-002 v0.1.0
- Tarefa: T01 — baseline, spikes e contratos de dependência
- Branch: `feature/termos-emprestimos-v2`
- Base: `30536d343c456e791c230ab3f01b2f43b0d0cb8c`

## Contexto e evidências

A evolução mantém o monólito modular Django, PostgreSQL, templates, HTMX e Bootstrap, preservando os controles existentes de integridade patrimonial e o Enterprise Blue. O PR #15 foi integrado à main; sua consolidação visual integra a baseline.

CI da base exata, consultado no GitHub:
- [Núcleo patrimonial](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45699966244): sucesso; 185 testes aprovados, 2 smoke tests opcionais de ClamAV ignorados, nenhuma falha; cobertura de linhas 88,77%, ramificações 74,40%.
- [Segurança](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45699966260): sucesso.

A baseline é evidência remota histórica no SHA indicado, não execução local. Python 3.14 e PostgreSQL 18 são requisitos de validação. O manifesto e o lock existentes permanecem intactos.

## Decisão operacional

O responsável autorizou alterações e commits diretamente no GitHub. Usar a branch de desenvolvimento como isolamento remoto e o GitHub Actions para verificar os commits RED, GREEN e correções. O ambiente desta sessão não possui checkout executável com a stack completa; não há worktree local nem subagentes independentes. Adotar execução sequencial (Executing Plans) com registro de evidências por tarefa. Não declarar testes aprovados antes de conferir a execução no SHA correspondente. Falhas inesperadas exigem diagnóstico, correção mínima e nova verificação; não desativar controles de segurança.

A autorização não inclui merge na main, deploy, contratação ou uso de credenciais e dados reais. O repositório é público: não publicar dados pessoais, secrets ou documentação institucional sensível. Nenhuma alteração na visibilidade ou configuração do repositório.

## Matriz preliminar de candidatos

| Capacidade | Candidatos a investigar (não selecionados) | Evidência exigida |
|---|---|---|
| Editor visual | Tiptap OSS / ProseMirror | Schema restrito, roundtrip, limites, acessibilidade por teclado, recursos obrigatórios, licenças e ausência de dependências comerciais necessárias |
| PDF | WeasyPrint / ReportLab | Renderização pt-BR, paginação, fontes, texto extraído, bloqueio de URLs externas, CPU/RSS e tempo; PDF/A somente se validado independentemente |
| Storage privado | SDK S3 compatível com R2 | Escrita sem sobrescrever, leitura verificada SHA-256, acesso público negado, idempotência, falhas e recuperação |
| Worker | Management command Django com outbox PostgreSQL | Claim/lease, recuperação, concorrência e execução contínua em ambiente autorizado |

Nenhuma dependência nova foi escolhida, instalada ou incorporada ao lock. Antes de aprovar o ADR: verificar versões, licenças, manutenção, advisories, compatibilidade e resultados de spikes descartáveis com dados sintéticos. O transporte SMTP permanece vigente; mudança para HTTPS exige ADR conforme plano.

## Restrições e riscos

- Render Free não garante execução contínua de worker. O ambiente de homologação documentado possui restrições de SMTP, armazenamento efêmero e backend de e-mail fail-closed. Não inferir operação real a partir do CI.
- Preservar triggers, RBAC, transações, ordem dos locks e compatibilidade dos termos legados.
- Renderização offline, schema permitido, sem HTML/CSS livre, URLs remotas ou acesso irrestrito a arquivos; storage privado e verificação por SHA-256 dos bytes.
- Limites iniciais do plano: 100 ativos, 10 signatários, uploads permitidos até 25 MiB. Limites adicionais de páginas, imagens, memória e tempo ainda exigem medição e aprovação.
- Não substituir o Design System vigente. Reutilizar componentes e testes CDP; WCAG 2.2 AA permanece alvo, não certificação já demonstrada.

## Ledger de execução

| Etapa | Estado |
|---|---|
| Reconferir HEAD e CI da main | Evidência remota coletada |
| Criar branch isolada no GitHub | Criada a partir do SHA acima |
| Leitura integral e conferência cruzada dos documentos | Pendente de ateste completo |
| Fixtures sintéticas pt-BR: 1/100 ativos, 1/10 signatários | Pendente |
| Testes de capacidade (renderer, editor, storage, worker) | Pendente |
| Spikes, medições e decisão tecnológica | Pendente |
| ADR aprovado e lock atualizado quando aplicável | Pendente |
| T01 concluída / T02 liberada | Não |

Comando de teste previsto, executado a partir de `backend/`: `python -m pytest tests/test_term_v2_capabilities.py -v`. A correção de caminho evita duplicar o prefixo backend; o arquivo de teste ainda não foi criado. Nenhuma conclusão RED/GREEN é alegada.

Ruling: isolamento por branch remota e verificação pelo CI, em vez de worktree local — autorizado pelo responsável nesta etapa e necessário diante das limitações do ambiente; custo residual: execução local e verificação independente não realizadas. Sem atalhos nos gates tecnológicos.

**README:** sem alteração necessária neste incremento documental; avaliar novamente quando houver novas dependências, setup ou comandos operacionais.

**Gate:** T01 em andamento. T02 permanece bloqueada até que as capacidades e o ADR sejam efetivamente validados.

## Execução experimental do renderer — T01 (25/11/2026)

- RED observado em [CI do commit bb91461](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45713873959/job/139554874717): 5 falhas por ausência de renderer_spike.py, 185 aprovados e 2 ignorados (192 coletados, 74,69 s). Ruff, Django check, migrations, OpenAPI e pipeline de segurança aprovados. Build e gate de cobertura não executados no RED.
- O primeiro RED (326941d) foi interrompido pelo Ruff, corrigido em bb91461, sem alteração de assertions.
- Candidato de laboratório: ReportLab 5.1.2 (BSD, Python >=3.10,<4, Pillow >=13.0.0 e charset-normalizer), conforme [metadados PyPI](https://pypi.org/pypi/reportlab/5.1.2/json). A versão está fixada apenas para o experimento; [notas de segurança 5.1](https://docs.reportlab.com/releases/notes/whats-new-51/) descrevem correções do avaliador de expressões. Evitar inteiramente a avaliação de código e markup. A ausência de advisories conhecidos não prova segurança.
- Ruling: acrescentar dependências fixadas em requirements-spike.txt, instaladas somente no runner de testes e auditadas no SCA/SAST; não modificar requirements.in, requirements.lock nem Dockerfile. Necessário para testar o candidato sem escolher dependência produtiva. Custo residual: manter instalação adicional enquanto o spike existir e verificar compatibilidade real no CI.
- Adapter experimental usa Canvas, texto literal, A4, quebra de linhas, paginação, bytes em memória, limite provisório de 20 páginas e 512 caracteres por campo; recusa qualquer recurso não vazio. Não aceita HTML/CSS, imagens, fonte fornecida por usuário ou caminho/URL de recurso. Helvetica WinAnsi permite testar pt-BR, mas não comprova fonte incorporada, PDF/A, acessibilidade, tabelas ricas nem isolamento completo de rede/arquivos. Limites são guardas do laboratório, não limites de produto aprovados.
- GREEN do renderer, auditoria do candidato, medições de CPU/RSS, inspeção visual, fontes redistribuíveis, PDF/A independente, editor, storage e worker permanecem pendentes. Nenhum requisito de produção ou deploy alterado.

## Validação avançada do renderer — 25/11/2026

- GREEN inicial: [52b9bfe, núcleo patrimonial](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45722771082), 190 aprovados, 2 ignorados, 56,31 s, cobertura 88,77% linhas/74,40% ramos, build Docker aprovado; [segurança](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45722771073) aprovada. O YAML experimental foi corrigido em 4b4da62; Ruff do spike em 52b9bfe.
- RED avançado: [bdf0d6b, job 139588411916](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45723801267/job/139588411916), 214 coletados, 207 aprovados, 5 falhas, 2 ignorados, 72,70 s. Falhas: fonte sem descritor; patch11 (campo desconhecido), patch12 (descricao ausente), patch13 (signatário com extra), documento sem resources. Os quatro testes SHA-256, paginação A4 e demais casos adversariais passaram. Ruff e [segurança](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45723801274) aprovados. Cobertura e build não executados nesse RED.
- Ruling: usar Vera.ttf fornecida pelo pacote ReportLab fixado, com fonte inicial TrueType explícita, sem caminhos/fontes fornecidos pelo usuário. Experimento local com ReportLab 4.4.9/pypdf 5.9.0 verificou extração pt-BR, FontFile2, ToUnicode e igualdade binária em duas gerações de um documento de duas páginas. Não substitui CI 5.1.2/6.21.4. A licença Bitstream Vera distribuída junto à fonte foi localizada no pacote local; confirmar distribuição e requisitos de licença no ambiente fixado antes de adoção. O conjunto de caracteres continua deliberadamente restrito ao laboratório. Custo residual: disponibilidade da fonte no pacote, subconjuntos, cobertura de glifos, compatibilidade e licença exigem confirmação. Nenhum arquivo de fonte adicional versionado.
- Correção do contrato de laboratório: validar conjunto exato de campos no documento e em cada ativo/signatário antes da renderização; campos desconhecidos ou ausentes geram ValueError. Não alterar assertions nem ampliar a API produtiva.
- GREEN das correções ainda pendente. O teste de fontes não comprova PDF/A. Benchmark, metadados, ICC e validação independente PDF/A permanecem pendentes.

## Benchmark e avaliação arquivística — T01

- GREEN avançado em [8ff9826](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45724279165): 212 aprovados, 2 ignorados, 62,47 s; cobertura 88,77%/74,40%; build Docker e [segurança](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45724279125) aprovados. Os 27 casos do renderer passaram com fonte incorporada e schema estrito.
- RED do benchmark em [b5c3799](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45725012842/job/139592527341): 218 coletados, 212 aprovados, 4 falhas esperadas (dois casos por componente ausente), 2 ignorados, 61,28 s; Ruff e [segurança](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45725012879) aprovados. Cobertura/build não executados por gate RED.
- Ruling: medir cada caso em processo Linux novo, uma geração de aquecimento e 10 repetições medidas; RSS máximo do processo inclui imports e aquecimento, não somente a função; latência e CPU não incluem parsing do PDF, inicialização ou I/O do relatório. Dados brutos JSON, SHA-256, tamanho, páginas e PDF sintético serão artefatos do CI. Não inferir SLA produtivo a partir de runner compartilhado.
- Ruling: tentar veraPDF CLI 1.30.4 (versão com correção de segurança de 09/11/2026, [release notes](https://github.com/veraPDF/veraPDF-library/releases/tag/v1.30.4)), em vez de 1.30.2. Disponibilidade do tag Docker ainda precisa ser confirmada no CI; registrar digest efetivamente obtido. Container sem rede, entrada sintética read-only, limites de recursos, sem XSLT/perfis customizados. Validar perfil PDF/A-2b explicitamente. XML analisado por defusedxml já presente no lock; códigos 0/1 precisam ser coerentes com relatório completo e resumo sem falhas operacionais. Não conformidade documentada não equivale a falha operacional: fallback PDF comum sem alegação PDF/A; decisão definitiva permanece pendente. Ausência de imagem ou falha operacional impede a avaliação; não omitir nem substituir a evidência.
- Resultados numéricos e relatórios reais ainda pendentes da execução do CI. ADR continua em avaliação.

## Evidências medidas — CI 45815496442 (26/11/2026)

**Escopo:** apenas o renderer experimental de texto literal, sem integração aos Termos V2 em produção. Python 3.14.10, ReportLab 5.1.2, pypdf 6.21.4; runner GitHub Actions Ubuntu/Linux x86-64 compartilhado.

- [Pipeline patrimonial, SHA a450661](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45815496442): **success**, 218 testes coletados, **216 aprovados e 2 ignorados** (65,83 s); Ruff lint/format, Django check, migrations, OpenAPI, coverage check e build Docker aprovados; linhas 88,77%, ramificações 74,40%.
- [Pipeline de segurança, mesmo SHA](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45815496504): **success**; pip-audit do lock e dependências experimentais sem vulnerabilidades conhecidas detectadas, Bandit e Gitleaks aprovados.
- [Artefato íntegro de medições, PDFs sintéticos e relatórios veraPDF](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45815496442/artifacts/15115656672): `gati-term-v2-renderer-evidence`, 18 arquivos ZIP (4 PDFs, 4 JSON, 4 XML, 4 stderr, status e digest da imagem). SHA-256 do ZIP informado pela ação: `8faf373013bb162afc5c0a8a9c5accaae7433fb12b0b5af71e715034fc7bed5b`. Os arquivos individuais e hashes completos estão no artefato.

### Desempenho real do experimento

Cada cenário foi executado em **processo Linux isolado**, com uma geração de aquecimento e **10 amostras cronometradas** (40 amostras no total). Mediana da latência de renderização e tempo de CPU em milissegundos; RSS é o pico do processo **inteiro** em KiB (inclui imports e aquecimento, não é apenas memória incremental da geração).

| Cenário | Ativos | Signatários | Páginas | PDF (bytes) | Latência mediana (ms) | CPU mediana (ms) | RSS pico (KiB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mínimo | 1 | 1 | 1 | 22.261 | 3,413 | 3,411 | 38.948 |
| Máximo de ativos | 100 | 1 | 3 | 24.104 | 11,721 | 11,718 | 39.008 |
| Máximo de signatários | 1 | 10 | 1 | 22.342 | 3,779 | 3,777 | 38.876 |
| Máximo combinado | 100 | 10 | 3 | 24.180 | 12,095 | 12,092 | 39.032 |

**Interpretação:** geração de PDF simples com boa capacidade experimental nos fixtures, sem SLA de produção inferível. A latência não inclui o startup do processo, parsing pypdf, gravação do relatório ou subprocesso do veraPDF. Ainda faltam cenários com templates ricos, anexos, imagens, múltiplas fontes, concorrência, limite de CPU/RSS sob carga e validação de experiência visual final. Os checks de SHA-256 foram aprovados. Uma inspeção visual pontual das páginas 1 e 3 do cenário máximo não identificou cortes evidentes, mas não é aprovação de layout final, acessibilidade ou PDF/A.

### Resultado independente do veraPDF

- Imagem efetivamente utilizada: `verapdf/cli:v1.30.4`, digest `sha256:c2ac9448973a56acd833c81441e38d2dca58ea26a2ce1621e9a32e85d3d2728f`.
- Quatro relatórios com `jobEndStatus=normal`, perfil `PDF/A-2b validation profile`, `isCompliant=false` e código de saída `1`; não conformidade **não** é falha operacional. Os stderr associados ficaram vazios.
- Os quatro cenários falharam nas mesmas três regras da ISO 19005-2:2011:

| Cláusula | Falha observada nos XMLs do veraPDF |
|---|---|
| 6.1.7.1 | Ausência ou posição inadequada de EOL em torno de palavras-chave `stream`/`endstream` |
| 6.2.4.3 | Uso de `DeviceGray` sem `OutputIntent`/perfil de cor apropriado |
| 6.6.2.1 | Ausência de metadados `/Metadata` XMP válidos no catálogo |

**Ruling:** manter explicitamente o renderer T01 como **PDF comum experimental**, jamais identificá-lo como PDF/A. A SPEC permite fallback quando PDF/A não está comprovado. Não contornar o veraPDF nem alterar suas regras de aprovação. Se a produção exigir PDF/A, investigar gerador compatível, metadados XMP, ICC/OutputIntent e delimitadores; gerar novo documento e obter `isCompliant=true` em perfil independente antes de alegar conformidade. Custo residual: indisponibilidade do recurso PDF/A até implementação e validação específica. A falha na cláusula 6.1.7.1 sugere ainda validar compatibilidade/formatação binária do gerador antes de qualquer alteração pós-processamento.

### Gate e pendências

- GREEN do benchmark e do parser: comprovado no SHA `a450661`.
- Coleta numérica e diagnóstico PDF/A: concluídos e vinculados acima.
- **T01 NÃO concluída:** continuam pendentes spikes e testes de editor visual, storage privado e worker/outbox; validação da licença e fontes, decisão tecnológica do ADR e aceite final.
- **T02 NÃO liberada.** Não houve aprovação de PDF/A nem alteração da configuração de produção, de dependências definitivas, merge ou deploy.

## Spike do editor visual — contrato inicial (26/11/2026)

- [RED remoto do editor, commit da5799b](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45819746738): 25 falhas esperadas por ausência de schema.py, 216 testes anteriores aprovados e 2 ignorados. Segurança aprovada. O commit RED original 8cbd6b exigiu correção de formatação em da5799b antes da confirmação funcional.
- Contrato experimental: JSON `schema_version=1`, classificação ENTREGA/DEVOLUCAO/EMPRESTIMO, layout A4, orientação portrait/landscape, margem 10–30 mm; texto/heading/listas, quatro marcas simples, variáveis do catálogo de classificação e um bloco patrimonial obrigatório não editável. Limites provisórios: 800 nós, profundidade 8, 65.536 bytes JSON, 4.096 caracteres por nó de texto. São guardas de experimento, **não** limites aprovados para produção.
- Fail closed: rejeitar atributos/nós não permitidos, imagens e referências de arquivo/URL (não há recursos aprovados neste laboratório), links, scripts, iframes, CSS livre, formatos desconhecidos ou remoção/duplicação do bloco patrimonial. O texto literal que contém `<script>` permanece texto JSON, nunca HTML executável.
- Ruling: validar primeiro o contrato em Python independente do Django e manter o editor como prova local sem rota, persistência, servidor de prévia, upload, autenticação nem integração com modelos do GATI. Isso reduz risco sobre o domínio legado. Custo residual: ergonomia, browser real, recursos ricos, compatibilidade e tecnologia definitiva ainda não validados. Tiptap/ProseMirror permanecem candidatos; não declarar escolha definitiva nem fidelidade Word com este spike.
- **Gate:** GREEN do schema Python e evidências de UI/teclado dependem de CI e ensaio; T01 e T02 permanecem em seus estados anteriores.

## UI experimental do editor — implementação T01 (26/11/2026)

- Contrato Python: [412063b](https://github.com/Miranda-txt/G.A.T.I/commit/412063bbfbf2b1ca88318cc6faf7882eea68e13c), 25 testes locais em Python 3.13.5 aprovados; confirmação remota no Python 3.14 é gate separado.
- Contrato JavaScript isolado e 4 testes Node: [255b796](https://github.com/Miranda-txt/G.A.T.I/commit/255b796e69e25e066d815497d4d69b704b2ccd14); execução local Node 22 com 4 testes aprovados, e CI remoto adicional para Node. Não instala novas bibliotecas nem altera lock.
- Interface demonstrativa: [e6aa310](https://github.com/Miranda-txt/G.A.T.I/commit/e6aa3109dd936adda3a6a0d4950e9146361a4c23), em `backend/tests/fixtures/term_v2/editor_spike/index.html`; parser JS de conteúdo literal, catálogo por classe, quatro marcas, listas, folha A4 **apenas ilustrativa**, bloco protegido fora da região editável, exportação local JSON. Sem requisições externas, upload, imagens ou persistência. Sintaxe de JS adicional coberta por [6494eef](https://github.com/Miranda-txt/G.A.T.I/commit/6494eef14a74364fbfb623b4e7f8debfb71701b7).
- **Ruling:** usar um protótipo de API nativa `contenteditable` sem dependências para isolar o contrato JSON e observar problemas de interação, e **não** assumir que isso substituirá ProseMirror/Tiptap na arquitetura final. Custo residual: seleções cruzando elementos são limitadas, entrada por teclado/colagem exigirá teste de navegador, recursos avançados (tabelas, cabeçalho/rodapé, imagens, undo/redo, paginação do servidor, estilos ricos) não são demonstrados. Em especial, não afirmar equivalência ao Word, acessibilidade WCAG AA certificada ou editor pronto para produção.
- UI/UX Pro Max: tokens oficiais Enterprise Blue reutilizados, foco visível, rótulos acessíveis e status via `aria-live`; responsividade declarada em CSS, mas revisão real em navegadores, com leitor de tela e 375px/zoom, permanece pendente.
- **Ruling:** nenhuma rota produtiva, template legado, modelo Django, migration ou feature flag foi alterada neste spike; não há formulário de gravação e nenhum dado real deve ser informado. Custo residual: integração end-to-end, RBAC, validação server-side ao persistir e prévia PDF ficam para etapas posteriores T03/T04, dependentes de aprovação tecnológica.
- Comparação de opções tecnológicas a concluir: (a) DOM nativo sem dependências, prova limitada; (b) ProseMirror/Tiptap OSS, candidato para esquema/extensões e acessibilidade, exigir spike de compatibilidade, license/SCA, tamanho, UX e teste de colagem. Não instalar pacotes do editor sem evidência e ADR aprovada.
- Gates pendentes de conclusão deste recorte: pipeline GREEN no SHA final, ensaio real de teclado/colagem/variáveis e roundtrip entre o cliente e o normalizador Django, comportamento em dispositivos móveis, testes de acessibilidade e decisão da tecnologia do editor. T01 continua aberta.

## Revisão de UX, acessibilidade e candidatos de editor — 26/11/2026

### Prova executada em Chromium/CDP

- [CI GREEN anterior, commit 22a8cdb](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45828609895): 246 aprovados, 2 testes opcionais de ClamAV ignorados, sem falhas. Reflow sem scroll horizontal em 320, 375, 768 e 1366 CSS px, incluindo alteração da fonte raiz para 200%; testes do contrato e roundtrip cliente→validador Python.
- [RED da extensão de UX, commit 6332666](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45829519751): 248 aprovados, 1 falha funcional esperada no título, 2 ignorados. Título não impedia colagem rica, quebra com Enter ou drop, e não normalizava linha ao colar. Os demais casos, incluindo parágrafo sem HTML executável e Tab/foco, passaram.
- [GREEN da correção, commit 23cd719](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45829912842): **251 testes coletados; 249 aprovados, 2 ignorados, zero falhas**; Ruff lint/format, Django checks/migrations, OpenAPI, cobertura (88,77% linhas e 74,40% ramificações), build Docker e veraPDF experimental executados com sucesso operacional. [Segurança no mesmo SHA](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45829912973): GREEN. Nenhum deploy ou merge.
- Três testes Chromium acrescentados: colagem de HTML no título como **texto literal em uma linha**, bloqueio de Enter e drop; colagem no parágrafo como texto literal sem executar HTML; Tab/Shift+Tab e indicador de foco na transição entre título, parágrafo e seletor de variáveis. A inserção do título não usa innerHTML. Não se afirma acessibilidade WCAG 2.2 AA certificada: não foram testados leitor de tela, IME, mobile touch real, browsers alternativos, contrastes automatizados nem casos complexos de seleção/undo/redo.

### Avaliação comparativa — decisão ainda não aprovada

| Alternativa | Evidência disponível | Trade-off e decisão provisória |
|---|---|---|
| `contenteditable` nativo atual | JSON restrito e tests Python+Node+Chromium passam em casos sintéticos; nenhuma dependência | Apropriado somente como **spike**: seleção entre nós, históricos de desfazer, transformações ricas, tabela, composição IME e sanitização cross-browser exigiriam manutenção extensa. **Não escolher para T04 definitivo com base neste recorte.** |
| Tiptap OSS (base ProseMirror) | A [documentação oficial](https://tiptap.dev/docs/editor/getting-started/overview) identifica núcleo MIT, compatibilidade com JS sem framework e extensões modulares; [catálogo oficial](https://tiptap.dev/open-source-to-platform) distingue OSS de recursos pagos | **Candidato prioritário para PoC comparativo** se a SPEC exigir autoria rica. Necessário validar as extensões exatas OSS, estrutura JSON ↔ schema Python, nó patrimonial protegido, colagem, acessibilidade, pacote/lock, licenças de dependências e SCA antes de escolher. Não contratar recursos Pro/Cloud nem incluir dependência definitiva. |
| ProseMirror diretamente | [Core e módulos MIT](https://github.com/ProseMirror/prosemirror-state/blob/master/LICENSE); projeto central mudou para [novo host de desenvolvimento](https://github.com/ProseMirror/prosemirror/blob/master/README.md) | Mais controle e menos abstração, mas maior custo de implementar toolbar, comandos, extensões e compatibilidade. **Candidato alternativo**, não aprovado. Confirmar versões, manutenção e advisories dos módulos efetivos. |

**Ruling:** manter apenas o schema JSON versionado e os testes como resultados comprovados da T01. Não declarar editor definitivo, equivalência ao Word ou aprovação do ADR. A PoC de integração Tiptap/ProseMirror é uma decisão técnica pendente sujeita a licença, segurança, compatibilidade, recursos da SPEC e aceitação; não usar plugins pagos para preencher lacunas. Os limites atuais de 800 nós/65.536 bytes e recursos proibidos são guardas experimentais, não especificação final.

**Pendências do gate T01:** editor rico (tabelas, imagens permitidas, cabeçalho/rodapé e preview do servidor), avaliação de acessibilidade com tecnologias assistivas e dispositivo real, decisão final do editor, storage privado e worker/outbox. PDF/A-2b permanece *noncompliant* no veraPDF; PDF simples não deve ser rotulado como arquivístico. T02 ainda não liberada.

## Spike de storage privado — contrato S3/R2 (26/11/2026)

### Referências de evidência

- [RED remoto, commit 5e4a48a](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45832527348): testes novos falharam exclusivamente por ausência de `storage_spike.py` (**26 falhas**), 249 testes anteriores passaram e dois testes opcionais foram ignorados; lint, formatação, Django checks e security green. A branch não inclui integração produtiva neste SHA.
- [Implementação experimental, 46f9e94](https://github.com/Miranda-txt/G.A.T.I/commit/46f9e949443cfcc80995d94539896a69e3548096), corrigida apenas quanto à formatação Ruff em [c5dcd58](https://github.com/Miranda-txt/G.A.T.I/commit/c5dcd584fa7246ffe5dc96cb7b3ac8e8a6d4e464).
- Execução local **não representativa do ambiente do CI**, Python 3.13.5 com pypdf instalado no ambiente isolado, 26/26 casos aprovados em 0,31 s após o ciclo RED local (26 falhas). Não é teste do Cloudflare R2 real. A verificação completa em Python 3.14/PG18 e o CI do commit corrigido devem ser consultados no GitHub, não presumidos como aprovados.
- Código e testes experimentais: `backend/tests/fixtures/term_v2/storage_spike.py`, `backend/tests/test_term_v2_storage_spike.py` e `backend/tests/fixtures/term_v2/storage.README.md`.

### Contrato avaliado e limites

O protótipo aceita um cliente com interface compatível com `put_object/head_object/get_object`. O cliente `FakeR2` executa em memória, sem rede, credenciais, bucket ou banco. Os cenários incluem 1:1 upload/download com SHA-256, chaves UUID, negação simulada de acesso anônimo, autorização por callback de laboratório, stream encerrado, não sobrescrita por intenção distinta, idempotência, concorrência com dois escritores, resposta perdida após PUT, falhas antes de PUT, objeto ausente, corrupção de bytes/metadata/MIME, arquivo inválido e limite temporário de tamanho. **Somente as condições simuladas foram verificadas**; o fake não demonstra a política de acesso de um bucket real.

- Ruling: usar `PutObject(IfNoneMatch="*")` para intenção de escrita única com chave opaca e identificador de operação; verificar `ContentLength`, `ContentType`, metadados da intenção, SHA-256 dos bytes retornados, sem tratar ETag como SHA-256. A [documentação oficial R2 de operações condicionais](https://developers.cloudflare.com/r2/api/s3/conditional-operations/) e do [modelo de consistência](https://developers.cloudflare.com/r2/reference/consistency/) descreve escrita condicional atômica e erro 412 quando já existe chave. **Custo residual**: o SDK Python exato, cenários 409/412, retires/timeout, multipart, quotas, consistência e comportamento real exigem PoC contra ambiente descartável **autorizado**, sem uso de serviços pagos por iniciativa própria.
- Ruling: **não alegar imutabilidade regulatória por Object Lock no R2**: a [matriz oficial de compatibilidade S3/R2](https://developers.cloudflare.com/r2/api/s3/api/) marca os campos S3 de Object Lock como não implementados. A aplicação pode garantir criação de objetos com nomes novos, mas exclusão/retention lock não fica garantida por isso. **Custo residual**: decisão específica sobre proteção contra exclusão, segregação de IAM, backup independente/restore e retenção jurídica antes da adoção.
- Ruling: upload de artefato gerado internamente fica separado de anexos de usuário. A integração com `arquivos` e a migração de anexos existentes não serão antecipadas; scanner/quarentena permanece fail-closed no fluxo de recursos enviados por usuários. **Custo residual**: teste real de scanner, tamanho/MIME de novos recursos e integração com storage ainda pendente.
- Ruling: o callback `permit` é só uma interface didática; **não é RBAC**, não deve ser recebido do usuário e não substitui autorização por recurso no servidor. Nenhuma URL pública ou pré-assinada é emitida no protótipo. **Custo residual**: testes de autorização real, configuração IAM e negação anônima de bucket, limites de download e no-store do endpoint HTTP permanecem obrigatórios.
- Ruling: PostgreSQL e objetos R2 não têm transação comum; T02/T05/T07/T13 deverão registrar intenção, confirmar objeto/hash antes de marcar DISPONIVEL, reconciliar objeto órfão/metadata sem objeto e testar replay/backups. O fake não exercita essas transações. **Custo residual**: consistência transacional e recuperação ainda pendentes.

Nenhuma dependência, configuração de nuvem, modelo de banco, rota, migração, arquivo produtivo ou lock foi alterado. O limite de 25 MiB e o schema `StoredArtifact` pertencem ao **laboratório**, não a uma política final de PDFs. O SDK S3/boto3 permanece **candidato não escolhido**; antes de fixar versão verificar licença, advisories, Python 3.14, suporte a cabeçalhos condicionais e auditoria SCA. T01 continua **EM AVALIAÇÃO**; T02 não liberada.

## Spike do worker/outbox PostgreSQL — T01 (26/11/2026)

**Escopo:** proof-of-capability em PostgreSQL 18 de teste, usando exclusivamente a tabela temporária de ensaio `gati_t01_worker_spike` criada e descartada pelo fixture (somente nome de banco `test_*`). O módulo é `backend/tests/fixtures/term_v2/worker_spike.py` e **não é** o worker produtivo T02, não cria migrations persistentes, não registra handlers reais, não opera rede/SMTP/PDF/R2 nem cria um processo contínuo ou scheduler.

### Evidências RED → GREEN

- [RED commit 8632032, Núcleo Patrimonial](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45834510453): **287 coletados**, **275 passaram, 10 falharam** por ausência de `worker_spike.py`, **2 ignorados**; Ruff e checks preliminares aprovados.
- [GREEN parcial commit 7409e7e](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45834942199): 284 passaram, 1 falhou, 2 ignorados; falha inicialmente atribuída à comparação UUID. [Commits 5161f49](https://github.com/Miranda-txt/G.A.T.I/commit/5161f4961de89d706c238d2a124fc869d77681c7) e [d1a9e82](https://github.com/Miranda-txt/G.A.T.I/commit/d1a9e823faa7be59a64d4537c6edb5dbef202b96) normalizaram a comparação e a moveram ao SQL, mas a falha permaneceu.
- **Causa real identificada no traceback**: o teste carregava `runpy.run_path()` em cada consulta de `_api()`; isso criava novas classes `WorkerConflict`, incompatíveis com a classe da exceção que o worker realmente lançava. Os testes de deduplicação de mesma intenção já passavam; o teste adversarial capturava a classe errada. [Fix de teste 0a69fe9](https://github.com/Miranda-txt/G.A.T.I/commit/0a69fe99ced50a86c9825dfb711b9b82cb7d56eb) adicionou cache de módulo sem enfraquecer as assertions.
- [CI GREEN do código final, commit 0a69fe9, execução #45836098825, tentativa 2](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45836098825): **287 coletados, 285 aprovados, 2 ignorados, 0 falhas**; Ruff lint/format, checks Django, migrations, OpenAPI, build Docker, cobertura de linhas 88,77% / ramos 74,40%, benchmark e veraPDF operacional aprovados. [Pipeline de segurança no mesmo SHA](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45836099229): consultar status específico ao auditar o gate.
- A primeira tentativa do último SHA registrou 284 aprovados e uma falha **preexistente e intermitente de infraestrutura Chromium/CDP**, `Browser.getVersion: timeout CDP`, em `tests/test_dashboard_browser.py`. A reexecução do job sem alteração de código passou. **Ruling:** classificar como flakiness a investigar, não desabilitar teste, não tratar retry isolado como prova de estabilidade absoluta do Chromium.

### Comportamentos demonstrados (PostgreSQL real, dados sintéticos)

1. Enqueue transacional com rollback integral e chave única de deduplicação; mesma intenção retorna mesmo ID, outra intenção conflita.
2. Claim concorrente com `SELECT ... FOR UPDATE SKIP LOCKED`; linha bloqueada é ignorada, três consumidores recebem três tarefas distintas.
3. Lease temporário com `lease_id` opaco; lease expirado pode ser recuperado por outro consumidor; confirmação de lease obsoleto recusada (fencing da finalização).
4. Tentativa máxima, backoff exponencial determinístico de laboratório (5 s, 10 s) e transição a `DEAD`; tarefa exaurida não é reexecutada.
5. Handler simulado fora do bloqueio de claim; erros convertidos em códigos sanitizados sem registrar texto de exceções potencialmente sensíveis; reexecução após DONE não reprocessa.
6. Rejeição de tipo e identificação não autorizados, chaves inválidas, datas ingênuas e parâmetros de lease inválidos.

### Limitações e decisões ainda pendentes

- **Não prometer exactly-once.** Um handler pode executar efeitos externos antes de perder lease ou após confirmação ambígua; fencing da conclusão do banco não impede efeitos duplicados por si. Handlers de produção precisam de idempotência ponta a ponta e verificação de estado/autorização imediatamente antes de efeitos.
- **Sem outbox definitiva.** A tabela de teste não representa o schema persistente T02, que exigirá migration expand, constraints/índices, transições, autenticação do runner, auditoria, políticas de retry/jitter e fila de falhas monitorada. Nenhuma API de enfileiramento é habilitada no GATI.
- **Sem garantia de worker contínuo no Render Free**. O spike apenas valida concorrência e transações PostgreSQL; a execução contínua, disponibilidade, watchdog, restart, credenciais de menor privilégio, deploy reversível e observabilidade exigem ambiente autorizado e decisão de operação.
- **Sem alteração produtiva**: nenhuma dependência/lock, serviço Django, rota, worker de deployment, migration, bucket, conta ou segredo real foi introduzido. Manter T01 em avaliação e T02 bloqueada até assinatura da decisão tecnológica e dos demais gates.

Ruling: o protótipo isolado em testes fornece evidência suficiente **somente** para a viabilidade do mecanismo PostgreSQL de claims/leases, não para aprovação de plataforma de execução nem da fila de produção. Custo residual: interrupções de serviço, duplicação de efeitos externos e retenção de tarefas ainda dependem de desenho e testes integrados.
