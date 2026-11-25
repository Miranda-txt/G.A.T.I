# DU-UX-DASH-05.5 — Contraste e homologação visual

Data: 25/11/2026. Estado: RED funcional confirmado; validação GREEN pendente.

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
