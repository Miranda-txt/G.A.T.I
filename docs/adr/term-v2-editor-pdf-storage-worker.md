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
