# Metodologias de Desenvolvimento — Projeto MultiTV

**Status:** Aprovado  
**Projeto:** MultiTV  
**Aplicação:** MVP e evolução subsequente  
**Nome oficial do processo:** MultiTV Engineering Workflow — Spec-Driven, Incremental, Verification-First Development

---

## 1. Objetivo

Este documento formaliza as metodologias e práticas de engenharia aprovadas para orientar o desenvolvimento do Projeto MultiTV.

O processo deverá ser utilizado como referência operacional para planejamento, implementação, revisão, testes, segurança, integração e rastreabilidade, inclusive durante o desenvolvimento assistido por ChatGPT.

O objetivo é manter o desenvolvimento incremental, verificável, rastreável e seguro, evitando grandes alterações sem validação intermediária e preservando alinhamento com a Arquitetura Conceitual, a Arquitetura Técnica e as especificações do projeto.

---

## 2. Metodologia principal — Spec Driven Development

O **Spec Driven Development (SDD)** será a metodologia principal e a autoridade do processo de desenvolvimento.

Fluxo oficial:

```text
Arquitetura
    ↓
SPEC
    ↓
Plano técnico
    ↓
Tasks
    ↓
Implementação
    ↓
Testes
    ↓
Verificação
    ↓
Rastreabilidade
```

Nenhuma funcionalidade relevante deverá ser implementada diretamente sem especificação suficiente para orientar sua execução.

Estrutura padrão das especificações:

```text
specs/
└── XXX-feature/
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    ├── test-plan.md
    └── traceability.md
```

---

## 3. Desenvolvimento incremental

O desenvolvimento será realizado por incrementos pequenos e verificáveis.

Cada incremento deverá possuir escopo reduzido, resultado observável e possibilidade de validação isolada antes do avanço para o próximo incremento.

A prioridade será concluir pequenas unidades de trabalho de ponta a ponta, evitando acumular grandes blocos parcialmente implementados.

---

## 4. Vertical Slice Development

Sempre que aplicável, as funcionalidades serão implementadas como **fatias verticais**, atravessando apenas as camadas necessárias para entregar uma capacidade funcional verificável.

Uma Vertical Slice pode abranger, conforme a necessidade:

```text
domínio
↓
persistência
↓
serviço
↓
API/contrato
↓
cliente
↓
observabilidade
↓
testes
```

A finalidade é evitar desenvolvimento prolongado por camada sem validação funcional ponta a ponta.

---

## 5. Walking Skeleton

O projeto deverá preservar continuamente um **Walking Skeleton**, isto é, uma versão mínima integrada e executável do sistema.

A evolução deverá ocorrer sobre um fluxo funcional já conectado, expandindo-o progressivamente em vez de criar grandes componentes isolados antes de validar a integração entre eles.

---

## 6. Development Units

A unidade operacional mínima de desenvolvimento será denominada **Development Unit (DU)**.

Hierarquia oficial:

```text
FASE
  ↓
SUBFASE
  ↓
DEVELOPMENT UNIT
```

Exemplo:

```text
F3.3 — Pareamento
└── DU-F3.3-01 — Solicitar pareamento
```

A identificação da posição atual do desenvolvimento deverá, sempre que possível, utilizar o formato:

```text
Fase/Subfase + Development Unit
```

Exemplo:

```text
F3.3 / DU-F3.3-04
```

---

## 7. Kanban

O controle operacional do desenvolvimento utilizará **Kanban**.

Fluxo padrão:

```text
BACKLOG
   ↓
SPEC
   ↓
READY
   ↓
IMPLEMENTING
   ↓
VERIFYING
   ↓
REVIEW
   ↓
DONE
```

Estado auxiliar:

```text
BLOCKED
```

O trabalho em progresso deverá permanecer reduzido, priorizando a conclusão de uma unidade antes da abertura de diversas atividades paralelas.

---

## 8. Test Driven Development orientado a risco

O **TDD** será aplicado principalmente em regras determinísticas, críticas ou com alto risco de regressão.

Exemplos:

- regras de rotação;
- pareamento;
- expiração;
- limitação de tentativas;
- backoff;
- autorização;
- validação;
- seleção de protocolo;
- máquinas de estado;
- regras de negócio.

Ciclo padrão:

```text
RED
↓
GREEN
↓
REFACTOR
↓
VERIFY
```

A aplicação de TDD não será dogmática. Integrações experimentais poderão utilizar spikes antes da estabilização dos testes automatizados.

---

## 9. Spikes técnicos

Áreas com incerteza técnica relevante poderão utilizar **spikes controlados** para reduzir risco antes da implementação definitiva.

Fluxo:

```text
Spike
↓
prova experimental
↓
entendimento técnico
↓
contrato estabilizado
↓
testes automatizados
↓
implementação definitiva
```

Spikes não substituem especificações nem transformam automaticamente resultados experimentais em decisões arquiteturais aprovadas.

---

## 10. Contract-First Development

REST, WebSocket e demais integrações deverão seguir **Contract-First Development**.

Os contratos deverão ser definidos antes ou junto do início da implementação dos consumidores e provedores.

Os contratos compartilhados deverão centralizar, conforme aplicável:

- requests;
- responses;
- eventos;
- códigos de erro;
- schemas;
- tipos compartilhados.

O objetivo é reduzir divergência entre Core, Admin Web, Receiver Web, Chrome Extension e demais componentes.

---

## 11. Contract Testing

Quando houver múltiplos consumidores de um contrato, deverão ser introduzidos testes de contrato proporcionais ao risco.

Esses testes deverão detectar alterações incompatíveis antes que mudanças no provedor quebrem consumidores existentes.

---

## 12. Regression-First para bugs

Bugs relevantes deverão, sempre que tecnicamente possível, seguir o processo:

```text
Bug identificado
↓
reprodução
↓
teste que demonstra a falha
↓
correção
↓
teste aprovado
↓
regressão
```

A correção deverá buscar eliminar a causa da falha e não apenas seu sintoma imediato.

---

## 13. Trunk-Based Development

O modelo de versionamento será **Trunk-Based Development**.

A branch principal será `main`.

Branches auxiliares deverão ser pequenas, curtas e focadas, por exemplo:

```text
feat/...
fix/...
spike/...
```

A integração deverá ocorrer com frequência, evitando branches de longa duração.

O uso de GitFlow não será o padrão do projeto.

---

## 14. Conventional Commits

Os commits deverão seguir uma convenção consistente, preferencialmente **Conventional Commits**.

Tipos previstos:

```text
feat:
fix:
test:
refactor:
docs:
build:
ci:
chore:
perf:
security:
```

Exemplos:

```text
feat(pairing): add pairing expiration
fix(rotation): skip unavailable source
test(auth): cover revoked tv credential
security(api): enforce resource authorization
```

---

## 15. Continuous Integration

Cada incremento integrado deverá passar por verificações automatizadas proporcionais ao risco.

Pipeline conceitual:

```text
install
↓
format check
↓
lint
↓
typecheck
↓
unit tests
↓
contract tests
↓
integration tests
↓
security checks
↓
build
```

Validações mais custosas poderão ser executadas em fluxos separados, incluindo:

- E2E;
- performance;
- compatibilidade;
- testes prolongados de estabilidade.

---

## 16. DevSecOps e Shift-Left Security

Segurança será tratada durante a implementação e não apenas como uma validação final.

Cada incremento deverá avaliar, conforme aplicável:

- validação de entrada;
- autenticação;
- autorização;
- menor privilégio;
- gerenciamento de secrets;
- tratamento seguro de erros;
- exposição de dados;
- logs;
- dependências;
- abuso de recursos;
- superfícies de ataque introduzidas pela mudança.

A validação final de segurança não substitui os controles aplicados durante cada Development Unit.

---

## 17. Risk-Based Testing

A profundidade dos testes será orientada pelo risco da funcionalidade.

Funcionalidades críticas, como autenticação, autorização, credenciais, pareamento, migrations, backup/restore, rotação e reconexão, deverão receber validação mais extensa do que mudanças de baixo impacto.

A estratégia de teste deverá priorizar impacto, probabilidade de falha e possibilidade de regressão.

---

## 18. Architecture Decision Records

Decisões arquiteturais relevantes deverão ser registradas em `docs/adr/`.

Um ADR deverá ser considerado quando houver:

- alteração de arquitetura;
- escolha de dependência estrutural relevante;
- mudança de contrato importante;
- alteração de decisão arquitetural existente;
- trade-off técnico significativo;
- decisão com impacto duradouro no projeto.

---

## 19. Definition of Ready

Uma unidade de trabalho somente deverá entrar em implementação quando estiver suficientemente preparada.

Checklist base:

```text
[ ] SPEC compreendida
[ ] requisitos identificados
[ ] dependências conhecidas
[ ] contratos conhecidos ou planejados
[ ] critérios de aceite definidos
[ ] riscos identificados
[ ] estratégia de testes definida
```

Itens poderão ser adicionados conforme o risco da funcionalidade.

---

## 20. Definition of Done

Uma unidade não será considerada concluída apenas porque o código foi escrito.

Checklist base:

```text
[ ] código implementado
[ ] compilação/typecheck aprovado
[ ] lint aprovado
[ ] testes relevantes aprovados
[ ] tratamento de erros revisado
[ ] validação de entrada revisada
[ ] autorização revisada quando aplicável
[ ] logs adequados
[ ] nenhum secret exposto
[ ] regressões avaliadas
[ ] documentação atualizada quando necessário
[ ] rastreabilidade atualizada
[ ] revisão concluída
```

Conforme a funcionalidade, também poderão ser obrigatórios:

```text
[ ] integration test
[ ] contract test
[ ] E2E
[ ] security test
[ ] migration test
[ ] backup/restore test
```

---

## 21. Protocolo de desenvolvimento assistido por ChatGPT

Durante implementação ou alteração de código, o ChatGPT deverá seguir o fluxo:

```text
1. Identificar Fase/Subfase/DU
        ↓
2. Consultar arquitetura relacionada
        ↓
3. Consultar SPEC relacionada
        ↓
4. Avaliar o código existente
        ↓
5. Identificar impacto e dependências
        ↓
6. Selecionar o menor incremento seguro
        ↓
7. Criar ou ajustar testes quando aplicável
        ↓
8. Implementar
        ↓
9. Executar validações
        ↓
10. Revisar segurança
        ↓
11. Revisar regressões
        ↓
12. Atualizar rastreabilidade/documentação
        ↓
13. Encerrar a Development Unit
```

O desenvolvimento assistido não deverá pular diretamente da solicitação para alterações extensas no código sem avaliação prévia do impacto.

---

## 22. Fluxo consolidado

```text
ARQUITETURA
     │
     ▼
    SPEC
     │
     ▼
    PLAN
     │
     ▼
   TASKS
     │
     ▼
DEVELOPMENT UNIT
     │
 ┌───┴────┐
 ▼        ▼
TEST     CODE
 │        │
 └───┬────┘
     ▼
   VERIFY
     │
     ▼
SECURITY REVIEW
     │
     ▼
REGRESSION CHECK
     │
     ▼
  REFACTOR
     │
     ▼
TRACEABILITY
     │
     ▼
     CI
     │
     ▼
    DONE
```

---

## 23. Composição oficial do MultiTV Engineering Workflow

| Disciplina | Abordagem adotada |
|---|---|
| Governança | Spec Driven Development |
| Planejamento | Kanban |
| Construção | Desenvolvimento incremental |
| Arquitetura funcional | Vertical Slices + Walking Skeleton |
| Unidade operacional | Development Units |
| Práticas de código | XP seletivo |
| Lógica crítica | TDD orientado a risco |
| Integrações experimentais | Spikes |
| APIs e eventos | Contract-First Development |
| Integrações | Contract Testing |
| Bugs | Regression-First |
| Git | Trunk-Based Development |
| Commits | Conventional Commits |
| Segurança | Shift-Left DevSecOps |
| Testes | Risk-Based Testing |
| Integração | Continuous Integration |
| Arquitetura | ADRs |
| Entrada de trabalho | Definition of Ready |
| Encerramento de trabalho | Definition of Done |

---

## 24. Metodologias não adotadas como padrão

### Scrum puro

Não será utilizado como metodologia principal. Elementos de Scrum poderão ser usados pontualmente se agregarem valor, mas o fluxo operacional oficial será Kanban.

### Waterfall

Não será adotado, pois o projeto possui riscos técnicos, benchmarks e compatibilidade que exigem ciclos curtos de feedback e validação.

### GitFlow

Não será o padrão. O projeto utilizará Trunk-Based Development com integração frequente.

---

## 25. Regra de governança

Este documento representa o processo de desenvolvimento aprovado para o Projeto MultiTV.

Mudanças substanciais no workflow deverão ser explicitamente discutidas e registradas antes de serem tratadas como novo padrão do projeto.

A metodologia deverá permanecer subordinada às decisões arquiteturais, requisitos, especificações e evidências obtidas durante testes e benchmarks.

---

## 26. Aprovação

Foi aprovado o **MultiTV Engineering Workflow**, incluindo:

1. Spec Driven Development;
2. desenvolvimento incremental por Vertical Slices;
3. Walking Skeleton;
4. Development Units;
5. Kanban com WIP reduzido;
6. TDD orientado a risco;
7. Contract-First e Contract Testing;
8. Regression-First para bugs;
9. Trunk-Based Development;
10. DevSecOps e Continuous Verification;
11. ADRs;
12. Definition of Ready e Definition of Done;
13. protocolo de desenvolvimento assistido por ChatGPT.

**Status final:** APROVADO.
