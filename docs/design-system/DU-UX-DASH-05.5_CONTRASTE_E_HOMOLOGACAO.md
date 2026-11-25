# DU-UX-DASH-05.5 — Contraste e homologação visual

Data: 25/11/2026. Estado: GREEN confirmado em duas rodadas; aprovado no escopo automatizado. Homologação manual pendente.

## Escopo e método

Baseline: `d7d8347` (DU05.4). Referência normativa: [WCAG 2.2](https://www.w3.org/TR/WCAG22/), critérios 1.4.1 (A), 1.4.3, 1.4.11, 2.4.7 e 2.4.11 (AA). A aparência do foco (2.4.13) é AAA. O gate local exige indicador explícito de foco e bordas de controles selecionados com contraste >= 3:1 como requisito conservador do design system; bordas decorativas e componentes inativos não constituem falha automática.

O teste `backend/tests/test_ui_contrast_browser.py` usa HTML renderizado pelo Django, dados sintéticos, Chromium/CDP por pipes, sem rede para serviços reais e com sandbox. Oito cenários: login, login inválido, erro de assinatura, dashboard, inventário, assistente, formulário de usuário e formulário de ativo inválido. Dois viewports: 320 e 1366 CSS px. Mede cores computadas, composição RGBA em superfícies sólidas, texto, placeholder, bordas e foco; hover/active via pseudoestados CSS, sem submissão real. Tab via CDP inicia modalidade teclado, seguido de foco programático na amostra. A posição central do componente focado é um gate geométrico conservador, não uma auditoria integral do 2.4.11.

## Evidências RED

- `f125927`: [CI inicial](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45666784202) — erro de instrumentação ao encontrar SVG de SELECT; não é RED funcional.
- `7f724f1`: [CI funcional](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45666920623) — 183 aprovados, 2 falhas, 2 ignorados. 28 amostras reprovadas; foco público 1,05:1; bordas 1,18–1,23:1; outline anulado pelo Bootstrap; checkbox também com diagnóstico de visibilidade reprovado. Teste anterior do dashboard apresentou timeout Browser.getVersion. [Segurança](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45666920508) aprovada.
- Correção candidata: especificidade explícita de foco para controles Bootstrap, foco azul na área pública, bordas de controles secundários e checkbox com tokens oficiais, estado marcado com accent. Diagnóstico de geometria de foco ampliado, asserções preservadas. Nenhum novo token, dependência, workflow ou regra de negócio. Resultado depende do CI.

## Limitações e roteiro manual pendente

Não houve acesso visual autenticado à homologação nem inspeção humana de screenshots neste incremento. Medição de CSS não substitui avaliação visual. Não declarar conformidade WCAG integral. Revisar presencialmente em ambiente autorizado com dados sintéticos:

- Login e recuperação (inclusive link válido/inválido), dashboard, inventário, pessoas, manutenção, catálogos, assistente completo, termos/assinatura, auditoria, importação/anexos e erros. Registrar navegador/versão, viewport, estado, resultado e evidência desidentificada.
- Teclado real: sequência Tab/Shift+Tab, acionamento Enter/Espaço, foco visível, elementos parcialmente/totalmente obscurecidos, menu mobile, rolagem de tabelas, retorno do foco e formulários inválidos. Verificar foco sem depender de cor e seleção com indicação não cromática.
- Zoom nativo 200% e reflow a 320 CSS px; leitores de tela (por exemplo NVDA/Firefox e VoiceOver/Safari), outros navegadores e preferências de alto contraste. Validar mensagens de sucesso, erro, atenção, controles desabilitados, estados checked/unchecked, gráficos, estados hover/focus/active, banners de ambiente e links. Componentes inativos têm exceções de contraste; avaliar clareza e semântica, não impor AA indevidamente.
- Revisar impressões dos termos, imagens/gradientes, ícones significativos e contraste de todos os estados não representados nos testes. Não usar dados reais, documentos, hashes de produção ou credenciais nas evidências.

Encerramento de DASH05-08 exige CI GREEN, registro dos limites e decisão de homologação manual. A publicação e merge em main permanecem sujeitos a autorização separada.

## Revalidação de f74a039 e sincronização do CDP

[CI de qualidade](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45667477387): 184 aprovados, 1 falha, 2 ignorados; 26 das 28 violações originais não reapareceram. Os dois resíduos correspondem ao checkbox focado fora do viewport (top 902,61/844,61 px; scrollY 0; altura 768 px). Outline sólido 3 px, contraste 6,70:1 e focus-visible verdadeiro em ambos. O teste anterior da Visão Geral passou; não houve timeout CDP nessa rodada. [Segurança](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45667477390) aprovada.

Investigação: o Bootstrap define scroll-behavior: smooth na raiz quando não há preferência por movimento reduzido. Fixture local reduzida, Chrome 144.0.7559.96, pipes e sandbox ativo, reproduziu a corrida nas duas larguras: foco verdadeiro/top 929/scrollY 0 antes da animação e foco verdadeiro/top 444/scrollY 485 após scrollend. Não é evidência de homologação da página real. Ajuste exclusivamente no teste: registrar scrollend antes de focus(), aguardar evento ou limite de 1500 ms para amostra inicialmente fora do viewport e dois frames de pintura; nenhuma rolagem é forçada. Mantidas todas as asserções de contraste, outline, foco e hit-test. Se o controle continuar oculto após a espera, permanece RED. Novo CI necessário. Timeout de inicialização CDP anterior é intermitente e não teve causa raiz demonstrada; não ampliar prazo, ignorar falhas nem desativar sandbox por hipótese.

## Parecer definitivo no escopo automatizado — 25/11/2026

Commit de código aprovado: `5be66ddc483fb0a656eca470b5eb3b878a2e0425`. As duas rodadas completas de CI passaram: 185 aprovados, 0 falhas, 2 ignorados (ClamAV real opcional); duração 73,12 s e 57,77 s; cobertura de linhas 88,77% e de ramificações 74,40%. Ruff (169 arquivos), Django, migrations, collectstatic, OpenAPI, Pytest/CDP, cobertura, Docker e segurança aprovados. Cinco testes CDP passaram em ambas as rodadas. As 28 violações originais não reapareceram, inclusive foco/visibilidade do checkbox em 320 e 1366 px após rolagem nativa. Resultado agregado do teste, não log por amostra. As asserções e os 17 tokens oficiais foram preservados.

- Qualidade: [rodada 1](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45669016137/attempts/1), [rodada 2](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45669016137/attempts/2).
- Segurança: [rodada 1](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45669016144/attempts/1), [reexecuções individuais](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45669016144/attempts/3). Auditoria [job 139426569328](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45669016144/job/139426569328), segredos [job 139426951994](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45669016144/job/139426951994).

DASH05-08 encerrado no escopo das amostras automatizadas; aceite visual manual permanece pendente, conforme roteiro acima. A causa do timeout intermitente de inicialização CDP não foi determinada; ele não ocorreu nas duas rodadas GREEN. Não houve avaliação humana de capturas autenticadas, leitores de tela, zoom nativo, outros navegadores ou revisão independente. Critérios e estados não testados não são declarados conformes. A revisão documental DU05.6 pode prosseguir; publicação/merge dependem de decisão explícita sobre a homologação manual, revisão e autorização separada. Esta atualização registra as evidências da baseline de código, sem alegar que seu próprio commit documental já foi validado.
