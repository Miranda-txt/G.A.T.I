# Plano de Testes — F0 Bootstrap e Walking Skeleton

## DU-F0.1-02 — Validação documental/estrutural

Não há aplicação funcional para testes automatizados nesta DU.

Validar:

```text
[ ] Documento de metodologia existe
[ ] Documento normativo oficial existe em docs/requisitos
[ ] README não se refere ao repositório como ZIP
[ ] SPEC F0 não é placeholder
[ ] PLAN F0 não é placeholder
[ ] TASKS F0 não é placeholder
[ ] TEST-PLAN F0 não é placeholder
[ ] TRACEABILITY F0 não é placeholder
[ ] Cinco workflows-placeholder foram removidos
[ ] Nenhum arquivo .env real foi adicionado
[ ] Nenhuma chave/token/credencial foi adicionada
[ ] Estrutura macro do monorepo permanece íntegra
```

### CI

Após remover os workflows-placeholder:

- não criar workflow falso apenas para produzir status verde;
- histórico de falhas antigas permanece como evidência histórica;
- CI real será criado na DU-F0.5-01.

### Baseline executável

Nesta DU:

```text
verify: NÃO DISPONÍVEL
pytest: NÃO CONFIGURADO
Django check: NÃO DISPONÍVEL
build: NÃO DISPONÍVEL
```

Isso é esperado até as DUs correspondentes.

---

## DU-F0.2-01 e posteriores

Cada DU deve adicionar seu plano de teste antes da implementação.

A DU-F0.4-01 formalizará o `verify`.
