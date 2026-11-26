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
