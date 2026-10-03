# GATI — Metodologia de Desenvolvimento

**Projeto:** Sistema de Gerenciamento de Ativos de TI — GATI  
**Documento:** Metodologia oficial de desenvolvimento do GATI  
**Status:** PROPOSTA PARA FORMALIZAÇÃO NO REPOSITÓRIO  
**Aplicação:** MVP e evoluções posteriores  
**Autoridade técnica:** subordinada aos requisitos e decisões arquiteturais oficiais do GATI.

---

## 1. Objetivo

Este documento formaliza o processo de desenvolvimento do GATI antes da continuidade da implementação.

A metodologia utiliza apenas práticas de processo compatíveis com as fontes do projeto e não importa arquitetura, stack, componentes, regras de negócio ou exemplos específicos de outros projetos.

A ordem de autoridade permanece:

1. Documento Consolidado de Requisitos e Projeto do GATI;
2. decisões arquiteturais aprovadas do GATI;
3. Plano de Fases de Desenvolvimento do GATI;
4. Arquitetura de Pastas e Arquivos do GATI;
5. este documento de metodologia;
6. SPEC, plan, tasks, test-plan e traceability da Development Unit;
7. ADRs aprovados;
8. código e testes existentes, desde que compatíveis com as decisões superiores.

---

## 2. Metodologia principal — Spec Driven Development

O **Spec Driven Development (SDD)** será a metodologia principal de governança da implementação.

Fluxo:

```text
Requisitos / Arquitetura
        ↓
SPEC
        ↓
Plano técnico
        ↓
Tasks
        ↓
Baseline
        ↓
Implementação
        ↓
Testes direcionados
        ↓
Verify
        ↓
Revisão de segurança
        ↓
Regressão
        ↓
Documentação
        ↓
Rastreabilidade
```

Nenhuma funcionalidade relevante deve ser implementada diretamente sem especificação suficiente.

Estrutura mínima por fase/feature:

```text
specs/
└── <fase-ou-feature>/
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    ├── test-plan.md
    └── traceability.md
```

---

## 3. Unidade operacional — Development Unit

A unidade mínima de trabalho é a **Development Unit (DU)**.

Hierarquia:

```text
FASE
  ↓
SUBFASE
  ↓
DEVELOPMENT UNIT
```

Toda solicitação de desenvolvimento deve começar informando:

```text
FASE:
SUBFASE:
DEVELOPMENT UNIT:
OBJETIVO:
REQUISITOS:
ARQUIVOS/COMPONENTES AFETADOS:
DEPENDÊNCIAS:
RISCOS:
BASELINE:
STATUS:
```

---

## 4. Desenvolvimento incremental

Cada incremento deve ser:

- pequeno;
- compreensível;
- testável;
- revisável;
- reversível;
- documentável;
- versionável de forma isolada.

Não misturar sem necessidade:

- nova feature;
- refatoração ampla;
- atualização de dependência;
- migration;
- alteração de contrato;
- correção de bug não relacionado.

---

## 5. Vertical Slices

Quando aplicável, capacidades funcionais serão entregues como fatias verticais pequenas.

Exemplo conceitual:

```text
regra de domínio
    ↓
persistência
    ↓
serviço
    ↓
API / View
    ↓
interface
    ↓
observabilidade
    ↓
testes
```

A fatia deve atravessar apenas as camadas necessárias para entregar comportamento verificável.

---

## 6. Walking Skeleton

O GATI deve manter continuamente uma versão mínima integrada, executável e verificável.

A F0 estabelece esse Walking Skeleton antes das funcionalidades de negócio da F1 em diante.

---

## 7. Planejamento — Kanban

O fluxo operacional será Kanban com WIP reduzido.

Estados recomendados:

```text
BACKLOG
READY
IN PROGRESS
VERIFY
REVIEW
DONE
BLOCKED
```

Somente uma quantidade pequena de DUs deve permanecer em andamento simultaneamente.

---

## 8. TDD orientado a risco

TDD não será aplicado mecanicamente a todo código.

É obrigatório priorizar teste antes ou junto da implementação em regras com maior risco, incluindo:

- autenticação;
- autorização;
- credenciais;
- tokens;
- migrations;
- constraints;
- imutabilidade;
- máquinas de estado;
- assinatura;
- uploads;
- Endpoint;
- instalação de drivers;
- backup/restore;
- regressões já conhecidas.

---

## 9. Regression-First

Todo bug reproduzível deve, sempre que tecnicamente viável:

1. possuir teste que demonstre a falha;
2. receber a correção;
3. manter o teste como proteção contra regressão.

---

## 10. Contract-First e Contract Testing

APIs e integrações relevantes devem possuir contrato definido antes ou junto da implementação.

Para o GATI, isso inclui especialmente:

- API `/api/v1/`;
- RFC 9457;
- OpenAPI;
- protocolo Endpoint ↔ Servidor;
- comandos do Endpoint;
- download de pacotes de drivers;
- assinatura externa;
- integrações SMTP quando aplicável.

Contratos aprovados não devem ser alterados silenciosamente.

---

## 11. Spikes

Uma integração ou comportamento incerto pode utilizar **Spike** quando houver risco técnico relevante.

Um Spike:

- possui objetivo explícito;
- possui prazo/escopo limitado;
- gera evidência;
- não se torna código de produção automaticamente;
- registra conclusão e decisão.

---

## 12. Trunk-Based Development

A branch principal é:

```text
main
```

Branches auxiliares devem ser curtas e focadas, por exemplo:

```text
feat/...
fix/...
spike/...
chore/...
```

Evitar branches de longa duração.

---

## 13. Conventional Commits

Formato:

```text
<tipo>(<escopo>): <descrição objetiva>
```

Tipos:

```text
feat
fix
test
refactor
docs
build
ci
chore
perf
security
```

Commit e push são executados manualmente pelo responsável por meio do GitHub Desktop.

---

## 14. DevSecOps e Shift-Left Security

Toda DU deve avaliar, conforme aplicável:

- validação de entrada;
- autenticação;
- autorização;
- menor privilégio;
- gestão de secrets;
- tratamento seguro de erros;
- exposição de dados;
- logs;
- dependências;
- abuso de recursos;
- novas superfícies de ataque;
- SAST;
- SCA;
- secret scanning;
- segurança de IaC/container quando introduzidos.

Segurança não é deixada para uma fase final.

---

## 15. Risk-Based Testing

A profundidade do teste depende do risco.

Prioridade elevada para:

- autenticação;
- RBAC;
- tokens;
- credenciais;
- dados pessoais;
- migrations;
- constraints;
- concorrência;
- idempotência;
- arquivos;
- SSRF;
- Endpoint;
- drivers;
- backup/restore.

Cobertura percentual não substitui testes de comportamento.

---

## 16. Architecture Decision Records

Utilizar ADR em:

- mudança arquitetural;
- escolha estrutural relevante;
- nova dependência estrutural;
- mudança importante de contrato;
- trade-off duradouro;
- revisão de decisão aprovada.

ADRs permanecem em:

```text
docs/adr/
```

---

## 17. Definition of Ready

Uma DU somente entra em implementação quando:

```text
[ ] Fase/Subfase/DU identificada
[ ] objetivo conhecido
[ ] requisitos consultados
[ ] arquitetura consultada
[ ] SPEC compreendida
[ ] escopo delimitado
[ ] fora de escopo conhecido
[ ] dependências identificadas
[ ] contratos identificados
[ ] critérios de aceite definidos
[ ] riscos identificados
[ ] estratégia de teste definida
[ ] impacto de segurança avaliado
[ ] impacto em banco avaliado
[ ] impacto em API avaliado
[ ] impacto em README/documentação avaliado
[ ] baseline identificada
```

---

## 18. Definition of Done

Uma DU somente pode ser concluída quando os itens aplicáveis estiverem atendidos:

```text
[ ] código implementado
[ ] comentários exigidos em PT-BR
[ ] format check aprovado
[ ] lint aprovado
[ ] typecheck aprovado
[ ] testes direcionados aprovados
[ ] testes relevantes aprovados
[ ] build aprovado
[ ] tratamento de erros revisado
[ ] validação de entrada revisada
[ ] autenticação revisada
[ ] autorização revisada
[ ] secrets revisados
[ ] logs revisados
[ ] regressões avaliadas
[ ] SAST/SCA/secret scanning avaliados quando configurados
[ ] contratos atualizados quando necessário
[ ] migrations testadas quando necessário
[ ] documentação atualizada
[ ] rastreabilidade atualizada
[ ] README avaliado
[ ] commit sugerido
[ ] status de commit informado
```

---

## 19. Baseline obrigatória

Antes de modificar código:

```text
BASELINE
```

A baseline serve para provar o estado anterior à mudança.

Se a baseline relevante estiver falhando, a alteração funcional fica bloqueada, exceto quando a própria DU tiver como objetivo corrigir a baseline.

O projeto deve evoluir para possuir um comando agregador:

```text
verify
```

O conteúdo real de `verify` será definido na DU-F0.4-01 conforme as ferramentas efetivamente adotadas.

Não inventar ferramentas antes da decisão correspondente.

---

## 20. Política de comentários em código

Comentários de código devem ser escritos em **Português do Brasil**.

A preferência geral de boas práticas é explicar intenção, regra, risco, segurança e comportamento não óbvio, em vez de apenas repetir a sintaxe.

### 20.1 Regra específica solicitada para o GATI

Por decisão explícita do responsável pelo projeto, o GATI adota uma exigência adicional:

> Toda linha de lógica adicionada ou modificada deve possuir contexto explicativo em comentário PT-BR.

Para preservar arquivos válidos e evitar comentários que prejudiquem ferramentas, ficam excetuadas apenas:

- linhas em formatos que não suportam comentários;
- linhas vazias;
- delimitadores puramente estruturais;
- conteúdo gerado automaticamente;
- arquivos cuja ferramenta proíba comentários naquele ponto.

Mesmo nessas exceções, o bloco ou unidade lógica correspondente deve possuir comentário explicativo próximo.

Comentários devem permanecer sincronizados com o código e não devem esconder comportamento incorreto.

Esta regra é registrada como convenção específica do GATI e poderá ser revista formalmente se demonstrar prejuízo mensurável de legibilidade ou manutenção.

---

## 21. Dependências

Nenhuma dependência deve ser adicionada apenas por conveniência.

Antes de adicionar:

1. justificar necessidade;
2. verificar alternativa nativa;
3. avaliar manutenção;
4. avaliar maturidade;
5. avaliar compatibilidade;
6. avaliar licença quando relevante;
7. consultar vulnerabilidades atuais;
8. avaliar dependências transitivas;
9. definir versão conforme baseline;
10. atualizar lockfile quando existir;
11. atualizar documentação de setup.

Dependência estrutural pode exigir ADR.

---

## 22. GitHub Desktop e responsabilidade humana

O fluxo é:

```text
alteração preparada
      ↓
testes / verify
      ↓
revisão de segurança
      ↓
documentação
      ↓
commit recomendado
      ↓
responsável revisa no GitHub Desktop
      ↓
responsável realiza commit
      ↓
responsável realiza push
```

O assistente não deve presumir que commit ou push ocorreu.

---

## 23. Registro obrigatório por fase, subfase e DU

Toda mudança de fase, subfase ou Development Unit deve deixar registro Markdown no repositório.

O registro deve conter:

- identificação;
- objetivo;
- fonte consultada;
- estado anterior;
- alterações;
- arquivos afetados;
- riscos;
- segurança;
- testes;
- resultado;
- pendências;
- README;
- ADR;
- rastreabilidade;
- commit recomendado.

Local preferencial:

```text
specs/<fase>/
```

Quando a fase possuir subdivisões, o registro pode permanecer na pasta específica da subfase/DU.

---

## 24. Fontes obrigatórias antes de desenvolver

Antes de cada DU:

1. consultar o repositório real `Miranda-txt/G.A.T.I`;
2. consultar a documentação oficial do GATI;
3. consultar SPEC/plan/tasks atuais;
4. consultar ADRs relacionados;
5. verificar código e testes existentes;
6. verificar estado de CI quando aplicável;
7. somente então implementar.

Não tratar documentação de outro projeto como autoridade arquitetural do GATI.

---

## 25. Composição oficial do GATI Engineering Workflow

| Disciplina | Abordagem |
|---|---|
| Governança | Spec Driven Development |
| Planejamento | Kanban |
| Construção | Desenvolvimento incremental |
| Arquitetura funcional | Vertical Slices + Walking Skeleton |
| Unidade operacional | Development Units |
| Práticas de código | XP seletivo |
| Lógica crítica | TDD orientado a risco |
| Integrações experimentais | Spikes |
| APIs/integrações | Contract-First |
| Validação de integrações | Contract Testing |
| Bugs | Regression-First |
| Git | Trunk-Based Development |
| Commits | Conventional Commits |
| Segurança | Shift-Left DevSecOps |
| Testes | Risk-Based Testing |
| Integração | Continuous Integration |
| Arquitetura | ADRs |
| Entrada de trabalho | Definition of Ready |
| Encerramento | Definition of Done |

---

## 26. Metodologias não adotadas como padrão

Não serão utilizadas como processo principal:

- Scrum puro;
- Waterfall;
- GitFlow.

Elementos pontuais podem ser utilizados se tiverem finalidade concreta e não contradisserem o processo vigente.

---

## 27. Governança

Mudanças substanciais nesta metodologia devem:

1. ser propostas explicitamente;
2. possuir justificativa;
3. avaliar impacto;
4. ser registradas em Markdown;
5. ser revisadas quanto a segurança e regressão;
6. ser incorporadas ao documento quando aprovadas.

A metodologia é subordinada aos requisitos e decisões arquiteturais do GATI.
