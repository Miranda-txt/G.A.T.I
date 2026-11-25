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
