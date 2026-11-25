# DU-UX-DASH-05 — Auditoria e homologação final da interface

**Estado:** iniciada; diagnóstico estático e baseline verificados. Não é laudo de conformidade WCAG nem aceite de homologação.
**Data:** 25/11/2026.
**Baseline:** `6cde964799120b6b0627cc5a19df4976cae43044`, PR #14, publicado no Render em 25/11/2026 (deploy `dep-dc3eg3s0916s738j9hdg`, live).
**Escopo:** consolidação do ciclo de modernização da Visão Geral e componentes compartilhados; verificação das telas administrativas e públicas. Não ampliar o domínio patrimonial.
**Fonte normativa:** [Paleta Enterprise Blue v1.0.0](GATI_Paleta_Cores_Enterprise_Blue_v1.0.0.md), RNF-010 conforme citado na especificação visual, [registro da implementação](IMPLEMENTACAO_ENTERPRISE_BLUE.md). As evidências históricas permanecem identificadas por data.

## 1. Baseline e evidências

- [CI pós-merge — qualidade](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45627071876): 178 coletados, 176 aprovados, 2 ignorados (ClamAV real opcional), zero falhas, 42,76 s. Cobertura de linhas 88,18% (mínimo 80%); ramificações 73,34% (mínimo 70%). Ruff, Django check, migrations em banco de CI, collectstatic, OpenAPI e Docker aprovados.
- [CI pós-merge — segurança](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45627071854): SAST, SCA e detecção de segredos aprovados.
- [Teste CDP](../../backend/tests/test_dashboard_browser.py): HTML renderizado pelo Django com dados sintéticos, viewport principal em 320, 375, 683, 768, 900, 901, 910, 1024, 1093, 1366 e 1920 px, escala de fonte em 200%, eventos de teclado sintéticos, menu e resize 768 → 910 → 768. Não equivale a zoom nativo, navegação real por leitor de tela ou testes de todos os fluxos.
- Homologação: versão live confirmada no Render; verificação anterior de prontidão e SELECT 1 direto no projeto Neon. Não foram coletadas respostas HTTP independentes dos endpoints nem capturas autenticadas desta versão.

## 2. Contrato visual

A camada de tema declara os 17 tokens oficiais, todos com valores iguais aos do catálogo. Ordem esperada: Bootstrap local → gati.css → gati-enterprise-blue.css → gati-shell-v2.css (somente área administrativa) → gati-dashboard-v2.css (somente Visão Geral). A área pública não deve carregar o shell administrativo. Não introduzir nova paleta, fonte remota ou biblioteca sem decisão registrada.

| Pares opacos conferidos | Contraste |
|---|---:|
| surface/accent | 6,70:1 |
| surface/accent-dark | 8,72:1 |
| surface/sidebar-active | 9,07:1 |
| sidebar-text/sidebar | 10,46:1 |
| ink/paper | 17,06:1 |
| muted/surface | 7,58:1 |
| environment-staging-text/environment-staging-bg | 8,24:1 |
| success/surface | 7,13:1 |
| warning/surface | 7,09:1 |
| danger/surface | 6,47:1 |
| line/surface (borda decorativa) | 1,23:1 |
| accent/sidebar (foco genérico potencial) | 2,32:1 |

Os dez pares textuais superam 4,5:1. Os dois últimos pares exigem análise contextual quando forem o único indicador de controle/estado, não constituem falha universal. O tema já usa muted nas bordas de campos e surface no foco de links da sidebar. Avaliar CSS computado, opacidade, hover, active, disabled, erro e foco; preservar indicadores não cromáticos.

## 3. Achados e prioridades

Prioridades: P1 = validar/corrigir antes do aceite do incremento; P2 = corrigir na consolidação ou justificar explicitamente. Nenhum achado é alegação de vulnerabilidade explorada. Verificações pendentes não são defeitos comprovados.

| ID | Prioridade | Evidência | Impacto e ação / aceite |
|---|---|---|---|
| DASH05-01 | P1 | components/form.html renderiza help_text e field.errors sem IDs explícitos; common/forms.py estiliza widgets | Auditar associação acessível de ajuda e erros (aria-describedby/aria-invalid, labels e fieldsets conforme widget). Reproduzir com HTML Django, formular teste RED, preservar escape, CSRF, required e validação do servidor. Não presumir XSS pela presença de safe: rastrear a proveniência dos textos. |
| DASH05-02 | P1 | users/list.html contém table sem wrapper table-responsive; records/list.html e terms/list.html têm wrapper | Risco de overflow do documento para nomes/usuários longos e fonte ampliada. Medir viewport real com CDP, aplicar wrapper quando necessário e garantir acesso por teclado à rolagem sem criar armadilha de foco. |
| DASH05-03 | P2 | components/records.html: colspan="8"; common/registry.py: ativos 5 colunas de dados + ações; pessoas 4 + ações; demais variam | Inconsistência estrutural comprovada na linha vazia. Derivar colspan das colunas efetivas + ação, com testes de recursos distintos, sem alterar filtro, paginação ou autorização. |
| DASH05-04 | P2 | processes/wizard.html usa classes current/done sem aria-current="step"; texto ETAPA N DE 7 separado | Expor etapa atual semanticamente e garantir indicação textual, mantendo as sete etapas e os contratos existentes. Testar etapa inicial/intermediária/final. |
| DASH05-05 | P1 | gati.css e gati-enterprise-blue.css mantêm font-size em px fora das regras específicas dashboard/shell | Cobertura de escala tipográfica do DASH-04 não abrange todas as telas. Verificar formulários, listagens e área pública com fonte padrão ampliada; corrigir seletivamente, não converter tudo às cegas. |
| DASH05-06 | P1 | test_dashboard_browser.py testa exclusivamente /; test_web_api.py cobre renderização e fluxos, não reflow/estados visuais de cada página | Expandir teste CDP para amostras representativas autenticadas e públicas, sem dados reais, sem tempo virtual, sem desabilitar sandbox, sem portas de depuração ou dependências desnecessárias. |
| DASH05-07 | P2 | README, VALIDACAO.md e IMPLEMENTACAO_ENTERPRISE_BLUE.md têm registros históricos de preparação/testes iniciais | Acrescentar baseline atual e links rastreáveis sem sobrescrever evidência histórica nem afirmar que todos os serviços externos/fluxos estão homologados. Atualizar README neste incremento. |
| DASH05-08 | P1 | Catálogo exige contraste não textual, estados interativos, foco e identificação textual; testes de paleta avaliam tokens, não todos os componentes computados | Medir componentes reais e revisar alertas, foco, seleção, formulários, links, tabelas e estados de erro/disabled. Não marcar contraste estrutural decorativo como falha automática. |

## 4. Matriz de homologação

| Fluxo | Evidência atual | Validação a executar |
|---|---|---|
| Visão Geral / shell | CDP aprovado em 11 larguras; testes de semântica e navegação | Capturas atuais, dados vazios/preenchidos, zoom nativo, leitor de tela, revisão de contraste computado e movimento reduzido |
| Inventário, Pessoas, Manutenções, catálogos | Templates/registro e testes funcionais revisados | Listas vazias/populadas, paginação, filtros HTMX, colunas, textos longos, reflow |
| Formulários, detalhes e anexos | Componentes revisados estaticamente | Labels/erros/ajuda, foco, envio inválido, tabela e anexos sintéticos; sem enviar arquivos ao ambiente real |
| Entregas/devoluções | Wizard e testes funcionais existentes | Etapa atual, retorno, mensagens, confirmação, reflow de revisão; dados sintéticos |
| Termos e assinatura | Templates de lista e assinatura pública revisados | Termo longo, hash, confirmação de identidade, aceite, impressão; preservar avisos e segurança |
| Administração e auditoria | Lista de usuários e contrato de RBAC do shell | Listagem de usuários, trilhas, nomes longos, perfis administrativo/operador, rolagem |
| Autenticação e recuperação | Templates públicos e testes funcionais existentes | Login, erro/bloqueio, recuperação sem disparar e-mail real; leitura de mensagens e escala |
| Importação | Template upload revisado | Prévia, erros, estados vazios, instruções e foco; não importar dados reais |

Matriz mínima proposta: 320, 768, 900/901, 1366 e 1920 px para telas representativas; fonte padrão 100% e 200%; zoom nativo 100%, 125%, 150%, 200% em navegador real; teclado, contraste e leitor de tela quando disponível. Manter as onze larguras existentes no dashboard. O navegador do CI é evidência automatizada, não substituto da homologação humana.

## 5. Sequência de execução e Definition of Done

1. Diagnóstico e registro versionado — concluído para o conjunto inspecionado.
2. Criar regressões direcionadas para os achados P1/P2 reproduzíveis; executar RED antes de alterar código.
3. Corrigir componentes incrementalmente; revisão de impacto em CSS, templates, HTMX, CSRF, RBAC, mensagens e impressão.
4. Executar regressões CDP e suíte completa; cobertura mínima, Docker, SAST/SCA/segredos. Registrar SHA e links. Não reduzir gates, ignorar browser obrigatório no CI ou desativar sandbox.
5. Homologação visual em navegador real com dados autorizados/sintéticos, registrar evidências desidentificadas, divergências de zoom e leitor de tela. Caso acesso indisponível, registrar pendência explícita; não declarar WCAG integral.
6. Atualizar registro de implementação e README com escopo real e riscos; preservar catálogo original. Revisar e obter autorização separada para merge/deploy, CI pós-merge e health checks.

**Limites e decisão:** o plano detalhado original DU-UX-DASH-05 não foi localizado na árvore do repositório consultada; esta matriz é uma proposta operacional para a solicitação atual, não reprodução literal daquele plano. O levantamento estático não cobre toda a cascata CSS computada nem todos os templates. Não houve revisão independente nem acesso visual autenticado a staging nesta revisão. Não foram alterados CSS, HTML, dependências, dados, configurações ou workflows. O relatório não fecha o incremento.

## 6. Atualização de situação — 25/11/2026

Baseline de código validada: `5be66ddc483fb0a656eca470b5eb3b878a2e0425` na branch de consolidação. As evidências iniciais acima são históricas. DU-UX-DASH-05.5 aprovado no escopo automatizado em duas rodadas: 187 coletados, 185 aprovados, 2 ignorados (ClamAV real opcional), zero falhas; cobertura 88,77% de linhas e 74,40% de ramificações. Docker, SAST, SCA e segredos aprovados. Consultar [parecer e ressalvas do DU05.5](DU-UX-DASH-05.5_CONTRASTE_E_HOMOLOGACAO.md).

DASH05-08 (P1): encerrado quanto às 28 violações reproduzidas e às amostras automatizadas; a homologação manual e os estados não cobertos permanecem pendentes. Não equivale a conformidade integral WCAG 2.2 AA. Não houve dispensa do aceite manual nem autorização de merge/deploy.

| Subetapa | Situação |
|---|---|
| DU-UX-DASH-05.1 — Auditoria e baseline | Concluída |
| DU-UX-DASH-05.2 — Componentes compartilhados | Concluída |
| DU-UX-DASH-05.3 — Tipografia e responsividade | Concluída no escopo automatizado |
| DU-UX-DASH-05.4 — Expansão CDP | Concluída no escopo automatizado; DASH05-06 encerrado nesse escopo |
| DU-UX-DASH-05.5 — Homologação visual e contraste | Automação aprovada; homologação manual pendente |
| DU-UX-DASH-05.6 — Documentação final e revisão técnica | Próxima etapa; consolidar evidências, DASH05-07 e riscos residuais |
| DU-UX-DASH-05.7 — Merge, CI e publicação | Pendente de revisão, decisão sobre homologação manual e autorização separada |

Progresso de execução técnica: 5/7 (71,4%), contando DU05.5 apenas no escopo automatizado, sem ponderação por esforço. Homologação completa de DU05.5 ainda não concluída. A atualização documental não modifica o código validado e não substitui o CI do novo commit de documentação.
