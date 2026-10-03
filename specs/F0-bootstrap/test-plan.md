# Plano de Testes — F0 Bootstrap e Walking Skeleton

## DU-F0.1-02 — Validação documental/estrutural

Não há aplicação funcional para testes automatizados nesta DU.

Validar:

```text
[x] Documento de metodologia existe
[x] Documento normativo oficial existe em docs/requisitos
[x] README não se refere ao repositório como ZIP
[x] SPEC F0 não é placeholder
[x] PLAN F0 não é placeholder
[x] TASKS F0 não é placeholder
[x] TEST-PLAN F0 não é placeholder
[x] TRACEABILITY F0 não é placeholder
[x] Cinco workflows-placeholder foram removidos
[x] Nenhum arquivo .env real foi adicionado
[x] Nenhuma chave/token/credencial foi adicionada
[x] Estrutura macro do monorepo permanece íntegra
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
