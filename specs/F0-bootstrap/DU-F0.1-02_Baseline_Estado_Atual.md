# DU-F0.1-02 — Baseline do Estado Atual

**Fase:** F0 — Bootstrap e Walking Skeleton  
**Subfase:** F0.1 — Inspeção / Baseline  
**Development Unit:** DU-F0.1-02  
**Status:** BASELINE REGISTRADA — REMEDIAÇÃO NECESSÁRIA ANTES DO WALKING SKELETON  
**Repositório consultado:** `Miranda-txt/G.A.T.I`  
**Branch observada:** `main`  
**Commit observado:** `d4e13500ce5fb36e4929849dfd98faea438424ad`

---

## 1. Objetivo

Registrar o estado real do repositório depois da DU-F0.1-01 e estabelecer quais correções de baseline devem ocorrer antes da DU-F0.2-01.

---

## 2. Fontes consultadas

- repositório real `Miranda-txt/G.A.T.I`;
- Documento Consolidado de Requisitos e Projeto do GATI;
- `GATI_Fases_Desenvolvimento.md`;
- `GATI_Arquitetura_Pastas_Arquivos.md`;
- `metologias de desenvolvimento.md`, apenas como referência metodológica compatível;
- `BoasPraticasDesenvolvimento.md`, apenas como referência de guardrails compatíveis.

Decisões técnicas específicas de outros projetos não são autoridade para o GATI.

---

## 3. Estado observado

### Repositório

```text
visibilidade: private
branch padrão: main
arquitetura: monorepo
```

### Árvore

Foram observados:

```text
629 entradas
143 diretórios
486 arquivos
```

A estrutura macro está alinhada ao desenho alvo:

```text
.github/
backend/
endpoint/
infra/
lab/
specs/
docs/
scripts/
```

### Implementação

A maior parte dos arquivos ainda é scaffold.

Indicadores observados:

```text
89 arquivos vazios
475 arquivos com até 150 bytes
343 arquivos .py, em sua maioria placeholders
```

Isso significa que presença física de arquivo não representa implementação funcional.

---

## 4. Baseline executável

No estado observado não existe aplicação Django funcional.

Arquivos como:

```text
backend/manage.py
backend/pyproject.toml
backend/config/settings/base.py
backend/gati/apps/usuarios/models.py
scripts/verify.py
```

são placeholders.

Portanto:

```text
comando oficial de verify: AUSENTE
testes funcionais: AUSENTES
build funcional: AUSENTE
migrations reais: AUSENTES
```

Essa ausência deve ser registrada, e não substituída por um comando inventado.

---

## 5. GitHub Actions

Foram encontrados cinco workflows-placeholder:

```text
.github/workflows/build-images.yml
.github/workflows/ci-backend.yml
.github/workflows/ci-endpoint.yml
.github/workflows/release.yml
.github/workflows/security.yml
```

Todos contêm apenas comentários de placeholder.

O GitHub registrou cinco execuções no último commit observado, todas com resultado:

```text
failure
```

Não houve job executável em `ci-backend.yml`.

### Causa raiz

Os arquivos foram criados antes da Development Unit responsável pela implementação real do CI.

A arquitetura define que a árvore completa representa estado-alvo, mas que componentes devem ser criados progressivamente.

### Correção

Remover temporariamente os cinco workflows-placeholder.

Eles devem ser recriados somente quando a DU correspondente estiver pronta:

```text
DU-F0.5-01 — GitHub Actions inicial
```

Workflows de Endpoint, security, build de imagens e release devem surgir somente quando houver conteúdo real e verificável para executar.

---

## 6. README

O README atual ainda afirma:

```text
Este ZIP representa a arquitetura...
```

Isso não representa mais o repositório real.

Deve ser atualizado para:

- identificar o projeto;
- indicar o estágio F0;
- apontar fontes oficiais;
- informar que ainda não existe aplicação executável;
- não inventar comandos ainda inexistentes.

---

## 7. Fonte normativa

`docs/requisitos/` ainda não contém o Documento Consolidado oficial.

Correção prevista neste incremento:

```text
docs/requisitos/GATI_Documento_Consolidado_Requisitos_Projeto_v1.0.0_GitHub.pdf
```

A inclusão não altera o conteúdo do documento.

---

## 8. Metodologia

Não foi encontrado no repositório um documento metodológico próprio do GATI.

A referência metodológica disponível na fonte possui identificação de outro projeto.

Antes de avançar, deve ser formalizado:

```text
docs/metodologia/GATI_Metodologia_Desenvolvimento.md
```

Somente práticas de processo compatíveis são adaptadas.

Nenhuma arquitetura específica de outro projeto deve ser importada.

---

## 9. Segurança

Na inspeção estrutural não foram identificados secrets óbvios nos arquivos examinados.

O `.gitignore` cobre categorias relevantes, incluindo:

```text
.env
secrets/
*.key
*.pem
*.pfx
backups/
*.dump
logs/
storage/
quarantine/
driver-packages/
```

`backend/.env.example` contém apenas variáveis sem valores reais.

Isso não substitui secret scanning formal, que será configurado em uma DU futura.

---

## 10. Classificação

| Componente | Estado |
|---|---|
| Repositório privado | IMPLEMENTADO |
| `main` | IMPLEMENTADO |
| Arquitetura macro | IMPLEMENTADO |
| `.gitignore` | IMPLEMENTADO |
| `.editorconfig` | IMPLEMENTADO |
| `.gitattributes` | IMPLEMENTADO |
| Documento de fases | IMPLEMENTADO |
| Documento de arquitetura | IMPLEMENTADO |
| Documento normativo no repositório | AUSENTE |
| Metodologia GATI | AUSENTE |
| README | PARCIAL |
| SPEC F0 | PARCIAL / placeholder |
| PLAN F0 | PARCIAL / placeholder |
| TASKS F0 | PARCIAL / placeholder |
| Test Plan F0 | PARCIAL / placeholder |
| Traceability F0 | PARCIAL / placeholder |
| Django funcional | AUSENTE |
| PostgreSQL | AUSENTE |
| migrations reais | AUSENTE |
| testes reais | AUSENTE |
| verify | AUSENTE |
| CI inicial | CONFLITANTE |
| Endpoint funcional | AUSENTE |
| Infra funcional | AUSENTE |

---

## 11. Remediações desta DU

Aplicar:

1. formalizar metodologia do GATI;
2. substituir documentação placeholder da F0 por conteúdo real;
3. atualizar README;
4. incluir documento normativo em `docs/requisitos/`;
5. remover workflows-placeholder;
6. não iniciar código funcional antes da revisão dessa baseline.

Não aplicar nesta DU:

- Django;
- PostgreSQL;
- UsuarioTI;
- migrations;
- dependências Python;
- CI real;
- Endpoint;
- infraestrutura de produção.

---

## 12. Critério de saída

A DU-F0.1-02 pode ser considerada concluída quando:

```text
[ ] metodologia GATI registrada
[ ] fonte normativa presente no repositório
[ ] README corrigido
[ ] F0 SPEC/PLAN/TASKS/TEST-PLAN/TRACEABILITY reais
[ ] workflows-placeholder removidos
[ ] nenhum secret adicionado
[ ] diff revisado
[ ] repositório relido após push manual
```

Após isso, o próximo passo é:

```text
DU-F0.2-01 — Walking Skeleton Django
```

A implementação dessa DU deve começar apenas após nova leitura do repositório.
