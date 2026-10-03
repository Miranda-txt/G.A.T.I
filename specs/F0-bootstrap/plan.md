# Plano Técnico — F0 Bootstrap e Walking Skeleton

**Status:** EM EXECUÇÃO

---

## Ordem

### 1. DU-F0.1-01 — Inspeção

Status:

```text
CONCLUÍDA
```

Resultado:

- repositório real lido;
- árvore identificada;
- placeholders identificados;
- GitHub Actions inspecionado;
- baseline estrutural conhecida.

### 2. DU-F0.1-02 — Baseline

Status:

```text
EM REMEDIAÇÃO
```

Ações:

1. formalizar metodologia GATI;
2. adicionar fonte normativa ao repositório;
3. atualizar README;
4. substituir documentos F0 placeholders;
5. remover workflows-placeholder;
6. reler o repositório após push manual.

### 3. DU-F0.2-01 — Walking Skeleton Django

Executar somente depois da DU-F0.1-02.

Resultado esperado:

- projeto Django real;
- inicialização local;
- estrutura modular mínima;
- nenhuma feature de negócio antecipada.

### 4. DU-F0.2-02 — PostgreSQL + UsuarioTI

Resultado esperado:

- PostgreSQL 18;
- conexão Django;
- `UsuarioTI` customizado desde a migration inicial;
- migration real e testável.

### 5. DU-F0.3-01 — Ambientes

Resultado esperado:

```text
base.py
development.py
test.py
staging.py
production.py
```

Com `GATI_ENV` fail-safe e configurações explícitas.

### 6. DU-F0.4-01 — Testes + Verify

Resultado esperado:

- pytest;
- pytest-django;
- coverage;
- testes mínimos;
- comando `verify`.

Ferramentas adicionais não devem ser inventadas antes da análise correspondente.

### 7. DU-F0.5-01 — CI inicial

Resultado esperado:

- workflow real;
- checks reproduzíveis;
- migrations check;
- testes;
- coverage;
- pipeline verde;
- proteção de `main` conforme capacidade/configuração do repositório.

---

## Dependências

```text
F0.1-02
  ↓
F0.2-01
  ↓
F0.2-02
  ↓
F0.3-01
  ↓
F0.4-01
  ↓
F0.5-01
```

---

## Regra

Uma DU não deve antecipar implementação de DUs posteriores sem necessidade técnica demonstrada.
