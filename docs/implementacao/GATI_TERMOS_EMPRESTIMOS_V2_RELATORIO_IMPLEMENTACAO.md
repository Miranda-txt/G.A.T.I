# GATI — Registro incremental de implementação de Termos e Empréstimos V2

**Estado:** checkpoint parcial para publicação na branch de desenvolvimento; T01 aberta; T02 em implementação isolada; nenhuma liberação operacional.

**Base:** `Miranda-txt/G.A.T.I`, `feature/termos-emprestimos-v2`, `604c3e019db2e2f4ea834f41f88bde30dfe3c6ca`.

**Autoridade:** GATI-SPEC-TERM-002 v0.1.0 e plano de 25/11/2026 (T01–T14). O plano e a SPEC originais foram recuperados do ZIP aprovado. Este registro complementa o parecer `docs/adr/term-v2-t01-gate-review.md`, não o substitui.

## Evidências oficiais T01

- [Núcleo patrimonial #46052005006](https://github.com/Miranda-txt/G.A.T.I/actions/runs/46052005006): GREEN; 385 testes aprovados, 2 ignorados, 1 aviso; 201 arquivos já formatados. Steps de capacidade concorrente e corpus adversarial GREEN.
- [Segurança #46052005013](https://github.com/Miranda-txt/G.A.T.I/actions/runs/46052005013): GREEN.
- Corpus adversarial oficial: 64 jobs, 28 aceitos, 36 rejeitados; contagem extraída da saída JSON do workflow. Isso não comprova homologação visual, sandbox integral, R2 real ou execução contínua.

## Implementação T02 em área isolada

| Componente | Estado |
|---|---|
| `OutboxTask` e migration `0005_outbox_task.py` | Código escrito, sintaxe validada, validação Django/PostgreSQL pendente |
| `services/outbox_policy.py` | RED 27 falhas pela ausência da implementação; GREEN 27/27 em Python 3.13.5 |
| `services/outbox.py` | Código candidato com deduplicação, claims `SKIP LOCKED`, leases, fencing, backoff e tratamento sanitizado; integração pendente |
| `management/commands/processar_tarefas_termos.py` | Comando candidato com desligamento gracioso; sem handlers registrados; execução desabilitada |
| `test_term_v2_outbox.py` | Nove testes de integração escritos; coleta bloqueada por ausência do Django local |
| `settings/base.py` | Feature flag default off e parâmetros de worker |

### Rulings (provisórios até revisão integrada)

- O responsável autorizou a publicação do checkpoint parcial em um commit, alterando a estratégia anterior de esperar T01–T14. Nenhum merge ou deploy autorizado.
- Preparar T02 sem aprovação operacional da T01: nenhuma rota ou handler habilitado, nenhuma nova dependência. Não equivale ao encerramento de gate.
- IDs de recursos canônicos (PK positivo ou UUID), chave `tipo:recurso:UUID-do-evento`. UUID de evento deve ser gerado/persistido pelo serviço consumidor e reaproveitado na repetição; não aceitar segredo ou texto livre na chave. O conjunto fechado de tipos é candidato, a reconciliar com os contratos T05/T07/T10/T13.
- `scheduled_at` conserva a intenção original para deduplicação depois de alterar `run_after`. Reutilizar chave para horário de intenção diferente causa conflito.
- Retentar somente resultado `RETRY` explicitamente seguro; exceções não classificadas e resultados ambíguos são quarentenados como `OUTCOME_UNCERTAIN` sem log do texto da exceção. Exige estratégia de reconciliação e handlers idempotentes nas tarefas consumidoras; não garante exactly-once.
- Leases vencidos recuperáveis e fencing da finalização em transação. O handler roda fora de transação externa; deve verificar domínio e lease imediatamente antes do efeito externo. O limite de lease não interrompe um efeito em voo.
- A migration é exclusivamente aditiva. Não alterar triggers 0002/0004. Antes de rollback de schema, preservar fila; remover a tabela com registros pode perder tarefas pendentes. Preferir desabilitar o recurso e reverter código com schema expandido.

### Testes e limitações

- `python -m pytest -q -c /dev/null backend/tests/test_term_v2_outbox_policy.py`: 27 passed, reconfirmado antes da publicação (ambiente parcial, sem Django).
- `python -m compileall -q backend`: exit 0, apenas nos arquivos copiados/modificados do patch.
- `python -m pytest -q backend/tests/test_term_v2_outbox.py`: coleta interrompida com `ModuleNotFoundError: No module named 'django'` no ensaio anterior; não é RED funcional nem aprovação.
- Clone Git bloqueado por DNS; dois arquivos existentes foram reconstruídos dos blobs do GitHub e verificados por SHA Git antes das alterações. Não há checkout completo. O ambiente local usa Python 3.13.5, sem Django, PostgreSQL e Ruff exigidos no CI. Ainda não há evidência de migrations check, SQL real, regressões do aplicativo, build, segurança ou revisão independente deste patch.
- Revisão do diff antes da publicação: 12 arquivos previstos, sem alterações em workflows, dependências ou infraestrutura; finais de linha CRLF do modelo preservados. A verificação de whitespace considerou CRLF. CI do novo commit pendente.

## Status do plano

| Tarefa | Estado |
|---|---|
| T01 — Baseline, spikes e contratos | Parcial, baseline GREEN; gates tecnológicos/operacionais restantes abertos |
| T02 — Outbox persistente e interfaces | Fundação candidata escrita; 27 testes de política GREEN local; testes PostgreSQL pendentes |
| T03 — Modelos versionados | Pendente |
| T04 — Editor visual | Pendente (spikes anteriores não são integração) |
| T05 — Emissão e PDF original | Pendente |
| T06 — Assinaturas | Pendente |
| T07 — PDF final e artefatos | Pendente |
| T08 — Recusa, cancelamento e substituição | Pendente |
| T09 — Empréstimos | Pendente |
| T10 — Convites e lembretes | Pendente |
| T11 — Consulta e recuperação | Pendente |
| T12 — Migração legado | Pendente |
| T13 — Segurança/backup/operação | Pendente |
| T14 — Homologação integrada | Pendente |

Nenhum critério CA-TERM-01–28 é declarado concluído por este incremento isolado. T02 contribui para CA-TERM-08/12/13/14/25, mas faltam os fluxos consumidores e testes integrados. Nenhum dado real, credencial, serviço externo, deploy ou merge foi utilizado.
