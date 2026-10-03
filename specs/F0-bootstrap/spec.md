# SPEC — F0 Bootstrap e Walking Skeleton

**Fase:** F0  
**Status:** EM EXECUÇÃO  
**Objetivo:** estabelecer uma aplicação mínima integrada, executável, testável e versionada antes das funcionalidades da F1.

---

## 1. Fontes

Esta SPEC deve ser interpretada em conjunto com:

- Documento Consolidado de Requisitos e Projeto do GATI;
- `GATI_Fases_Desenvolvimento.md`;
- `GATI_Arquitetura_Pastas_Arquivos.md`;
- `docs/metodologia/GATI_Metodologia_Desenvolvimento.md`;
- ADRs aplicáveis, quando existirem.

---

## 2. Escopo F0

A F0 contém:

```text
DU-F0.1-01 — Inspeção completa do repositório
DU-F0.1-02 — Baseline do estado atual
DU-F0.2-01 — Walking Skeleton Django
DU-F0.2-02 — PostgreSQL + migration inicial + UsuarioTI
DU-F0.3-01 — Estrutura de ambientes
DU-F0.4-01 — Testes + verify
DU-F0.5-01 — GitHub Actions inicial
```

---

## 3. Estado atual

```text
DU-F0.1-01: CONCLUÍDA
DU-F0.1-02: REMEDIAÇÕES CONCLUÍDAS NA BRANCH — aguardando revisão final e integração na main
DU-F0.2-01: BLOQUEADA até integração da baseline na main e releitura do repositório
DU-F0.2-02: NÃO INICIADA
DU-F0.3-01: NÃO INICIADA
DU-F0.4-01: NÃO INICIADA
DU-F0.5-01: NÃO INICIADA
```

---

## 4. Requisitos arquiteturais da F0

O Walking Skeleton deve respeitar:

- Django monolítico modular;
- Python 3.14.x;
- Django 5.2.x LTS;
- PostgreSQL 18.x;
- Django Templates no frontend;
- separação progressiva entre domínio, serviços, Views/DRF e templates;
- Django ORM e migrations como autoridade de schema;
- ausência de microsserviços;
- ausência de Celery/Redis/broker geral;
- configuração segura por ambiente;
- nenhuma credencial versionada.

---

## 5. Fora de escopo da F0

A F0 não implementa funcionalidades completas de:

- inventário;
- movimentações;
- Termos;
- importações;
- uploads;
- Endpoint;
- scraping;
- drivers;
- produção.

Esses itens entram nas fases previstas no plano.

---

## 6. Critérios de aceite da F0

A F0 somente termina quando:

```text
[ ] Django inicia corretamente
[ ] PostgreSQL 18 conecta
[ ] migrations aplicam
[ ] UsuarioTI customizado existe desde a migration inicial
[ ] estrutura de ambientes existe
[ ] testes mínimos executam
[ ] health checks mínimos existem
[ ] verify existe e funciona
[ ] pipeline inicial está verde
[ ] documentação está sincronizada
[ ] nenhum secret foi versionado
```

---

## 7. Segurança

Desde a F0:

- secrets permanecem fora do Git;
- configurações falham de forma segura;
- produção não recebe `DEBUG=True`;
- hosts/origens são explícitos por ambiente;
- logs não devem conter secrets;
- dependências devem ser justificadas e verificadas;
- CI deve ganhar verificações de segurança de forma incremental.

---

## 8. Comentários de código

O código do GATI deve seguir a política definida em:

```text
docs/metodologia/GATI_Metodologia_Desenvolvimento.md
```

Comentários são em PT-BR e acompanham toda lógica adicionada/modificada, respeitando limitações sintáticas e evitando quebrar formatos/ferramentas.

---

## 9. Regra de avanço

Não iniciar a F1 enquanto a F0 não estiver saudável.
