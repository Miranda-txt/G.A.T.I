# Handoff — fundação T02

## Retomada

- Branch autorizada: `feature/termos-emprestimos-v2` em `Miranda-txt/G.A.T.I`.
- Base anterior ao incremento: `604c3e019db2e2f4ea834f41f88bde30dfe3c6ca`. O HEAD deve ser revalidado antes de novas alterações.
- O responsável solicitou publicar o checkpoint parcial da T02 em vez de aguardar o commit integral T01–T14. Este documento acompanha o commit da fundação; o SHA do próprio commit deve ser obtido pelo histórico.
- Plano e SPEC originais no ZIP `GATI_Termos_Emprestimos_Documentacao_e_Plano (2)(3).zip`; consultar integralmente antes de implementar T03–T14.
- Relatório incremental: `docs/implementacao/GATI_TERMOS_EMPRESTIMOS_V2_RELATORIO_IMPLEMENTACAO.md`.

## Próxima ação técnica

1. Confirmar CI deste commit, incluindo Ruff, migrations e PostgreSQL. Restaurar checkout completo em Python 3.14/PostgreSQL 18 e dependências do lock quando possível.
2. Manter feature flag desabilitada no ambiente padrão. Confirmar `makemigrations --check --dry-run` e migration 0005 em banco descartável. Validar constraints, concorrência e rollback com `python -m pytest tests/test_term_v2_outbox*.py -v` a partir de backend; corrigir T02 e executar regressões.
3. Fechar ensaios possíveis de T01, sobretudo linhas altas/paginação, fidelidade visual, sandbox e licenças. Pendências de R2 real, runtime contínuo e aceite institucional continuam gates de liberação; não presumir aprovação.
4. Prosseguir com tarefas T03–T14 conforme contratos aprovados; manter feature flag off e handlers não homologados isolados. Não modificar regras de negócio do legado para facilitar implementação.
5. Expandir o relatório para os 28 critérios de aceite, atualizar ADRs, README e documentação afetada, preparar Handoff e revisar diff integrado. Não realizar merge ou deploy sem autorização.

## Pontos críticos

- A T02 ainda não foi testada localmente em Django/PostgreSQL. Não declarar completa.
- Antes de ativar handlers, implementar verificação de estado/lease no domínio, reconciliação de resultados ambíguos, deduplicação de efeitos externos e monitoramento de idade da fila.
- Revisar os nomes dos tipos de tarefas e o contrato de chaves na integração com as tarefas consumidoras. Não persistir segredo em outbox.
- Nenhum worker real configurado, nenhuma alteração em produção. Repositório público: somente dados sintéticos.
- Preserve todos os commits anteriores e não faça force push.

## Checkpoint posterior — 28/11/2026

A base `346d2a1` passou nos dois CIs, com 421 testes aprovados, migration 0005 OK e sem drift. Incremento subsequente adiciona conferência do lease antes do despacho, quarentena de NOTIFICACAO com lease vencido e serviço administrativo `queue_snapshot`. Ver seção de reforço T02 no relatório. 33 testes de política aprovados localmente; os quatro novos testes PostgreSQL e o CI completo devem ser confirmados no HEAD antes de declarar a T02 concluída. Não iniciar consumidores reais fora das tarefas previstas; T05/T07/T10/T13 ainda devem prover idempotência de domínio, revalidação antes do efeito e reconciliação. UI de consulta administrativa prevista para T11. Flag off, sem deploy, merge ou runtime provisionado. O próximo passo é confirmar CI e resolver falhas, depois confrontar o gate T02 e prosseguir para T03 com os requisitos originais.
