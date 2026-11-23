# GATI — Registro de implementação visual Enterprise Blue

**Data:** 23/11/2026
**Status:** implementação autorizada para commit na branch `main` em 23/11/2026; **homologação visual e verificação integral da nova versão pendentes**.
**Fonte de verdade da paleta:** `GATI_Paleta_Cores_Enterprise_Blue_v1.0.0.md`.
**Baseline consultada:** repositório `Miranda-txt/G.A.T.I`, branch `main`, commit `624f5f3431cd8da0f2e474313972f9890fb04e8f`.

## Decisão de baixo risco

Para preservar a folha CSS original e tornar o rollback simples, foi adotada uma **camada adicional de tema**, carregada **depois** do arquivo `gati.css` por ambos os templates globais, sem alteração de lógica Django, contratos, modelos, migrações ou endpoints. Os 17 códigos HEX são exatamente os da especificação aprovada. Não foram adicionadas bibliotecas, requisições externas nem fontes externas.

A camada corrige cores fixas herdadas das seguintes regiões: sidebar e estado ativo, marca e navegação, topbar, botões Bootstrap (inclusive hover), métricas, cards, painéis, tabelas, formulários, controles focados, estados vazios, termos, login, assinatura pública, alertas, rodapé e banners de desenvolvimento/homologação. Melhorou-se o tamanho de legendas de 9–11 px para **no mínimo 11–12 px nos seletores explicitamente revisados**, sem refatorar o layout.

O banner `AMBIENTE DE HOMOLOGAÇÃO` permanece em amarelo (`#FFF4CC`) com texto (`#78350F`). Verde (`#166534`), âmbar (`#92400E`) e vermelho (`#B91C1C`) são reservados para sucesso, atenção e erro. O estado de foco permanece visível e a seleção da sidebar conserva marcador lateral além da cor.

## Arquivos alterados/adicionados

| Caminho | Alteração |
|---|---|
| `backend/static/gati/css/gati-enterprise-blue.css` | Novo CSS de tema baseado nos 17 tokens aprovados |
| `backend/templates/base.html` | Importa o CSS de tema depois do CSS existente |
| `backend/templates/public.html` | Importa o mesmo tema na área pública de autenticação e assinatura |
| `backend/tests/test_ui_palette.py` | Cinco testes para tokens, links dos templates, contrastes, foco e banners |
| `docs/design-system/GATI_Paleta_Cores_Enterprise_Blue_v1.0.0.md` | Cópia íntegra do catálogo aprovado |
| `docs/design-system/IMPLEMENTACAO_ENTERPRISE_BLUE.md` | Este registro de decisão e testes |

## Validação nesta preparação

- Inspeção do repositório na branch `main`, incluindo templates, CSS, testes e workflow CI.
- Histórico do GitHub Actions consultado: execuções no commit-base `624f5f3` concluídas com sucesso. Não equivale à execução local do `verify` completo.
- Testes específicos: `5 passed, 21 subtests passed` com `pytest` sem banco de dados.
- Parser CSS `tinycss2`: 113 regras analisadas, **zero erros de sintaxe** (parser usado apenas para verificar o arquivo, não adicionado como dependência).
- Conferência de SHA de blob Git dos templates de origem com a versão consultada no GitHub.
- **Não executados nesta preparação:** suíte Django com PostgreSQL, CI do patch aplicado, testes E2E/Playwright e homologação visual real. A tentativa de abrir a prévia no Chromium do ambiente foi bloqueada (`net::ERR_BLOCKED_BY_ADMINISTRATOR`).

## Critérios de homologação pendentes

1. Conferir em *staging* o dashboard, Inventário, Pessoas, filtros e telas com formulários; verificar colunas e rolagem em resoluções desktop, notebook e tablet.
2. Conferir login, recuperação de senha e assinatura externa; garantir que o tema não oculte avisos de segurança nem controles de aceite.
3. Navegar com teclado; testar `Tab`, `Shift+Tab`, `Enter`, foco visível, estados de erro e cores com zoom de 200%.
4. Testar alertas de sucesso/atenção/erro em condições reais, contraste e componentes de formulário; verificar WCAG 2.2 AA aplicável.
5. Executar os testes completos do repositório com PostgreSQL/ClamAV nas condições de CI, `manage.py check`, `collectstatic` e validação de assets estáticos.
6. Acompanhar o GitHub Actions após o commit autorizado; realizar homologação visual e registrar eventuais correções em branches `fix/...`, com testes e revisão antes do merge.

## Segurança, rollback e README

A mudança não introduz API, execução de JavaScript, armazenamento, autenticação ou autorização novos. O script de aplicação (distribuído fora do repositório) verifica o conteúdo esperado dos templates e cria backup fora do repositório antes de copiar, sem realizar commit/push.

**Rollback:** restaurar os dois templates anteriores e remover o arquivo CSS adicional; os testes e a documentação novos podem ser retirados em alteração documental separada, quando necessário. O CSS original `gati.css` não foi modificado.

**README: SEM ALTERAÇÃO NECESSÁRIA.** Não há novas dependências, variáveis de ambiente, comandos de aplicação, rotas ou processo de instalação; a especificação e este registro ficam em `docs/design-system/`.

**Status do commit:** autorizado explicitamente pelo responsável em 23/11/2026, com a publicação no repositório separada da homologação e do deploy. Eventuais correções seguirão em branches `fix/...`.

**Mensagem do commit autorizado:** `style(ui): aplica paleta corporativa Enterprise Blue`.
