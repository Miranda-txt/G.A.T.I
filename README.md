# GATI — Sistema de Gerenciamento de Ativos de TI

O GATI é o sistema central do projeto para gerenciamento do parque de ativos de TI.

## Estado atual

```text
FASE: F0 — Bootstrap e Walking Skeleton
SUBFASE: F0.1 — Inspeção / Baseline
DU ATUAL: DU-F0.1-02 — Baseline do estado atual
```

O repositório ainda **não contém uma aplicação funcional pronta para execução**.

A estrutura atual representa o monorepo e a arquitetura alvo que serão implementados progressivamente.

## Fontes do projeto

Consulte, nesta ordem:

1. `docs/requisitos/GATI_Documento_Consolidado_Requisitos_Projeto_v1.0.0_GitHub.pdf`;
2. `GATI_Fases_Desenvolvimento.md`;
3. `GATI_Arquitetura_Pastas_Arquivos.md`;
4. `docs/metodologia/GATI_Metodologia_Desenvolvimento.md`;
5. `specs/`;
6. `docs/adr/`, quando aplicável.

## Desenvolvimento

O projeto utiliza:

- Spec Driven Development;
- desenvolvimento incremental;
- Vertical Slices;
- Walking Skeleton;
- Development Units;
- Kanban;
- TDD orientado a risco;
- Regression-First;
- Contract-First/Contract Testing;
- Trunk-Based Development;
- Conventional Commits;
- Shift-Left DevSecOps;
- Risk-Based Testing;
- ADRs;
- Definition of Ready;
- Definition of Done.

## Git

A branch principal é:

```text
main
```

Commit e push são realizados manualmente pelo responsável usando GitHub Desktop.

## Execução local

Ainda não existe comando oficial de execução nesta etapa.

Ele será documentado somente quando o Walking Skeleton for realmente implementado.

## Testes

Ainda não existe suíte funcional nem comando `verify`.

A configuração de testes e verificação pertence às Development Units previstas na F0.

## Segurança

Nunca versionar:

- `.env` real;
- secrets;
- tokens;
- credenciais;
- chaves privadas;
- backups;
- dados reais de produção;
- uploads reais;
- pacotes privados de drivers.

## Próximo passo

Concluir:

```text
DU-F0.1-02 — Baseline do estado atual
```

Depois:

```text
DU-F0.2-01 — Walking Skeleton Django
```
