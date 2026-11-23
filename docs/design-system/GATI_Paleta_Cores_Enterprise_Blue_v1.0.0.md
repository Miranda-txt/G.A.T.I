# GATI — Paleta de Cores Corporativa Enterprise Blue

> **Documento de referência visual do projeto GATI.** Define as cores selecionadas, suas responsabilidades e orientações para uso consistente na interface. Não constitui uma implementação de CSS, modificação de código ou homologação de acessibilidade.

## Controle documental

| Campo | Informação |
|---|---|
| Projeto | GATI — Sistema de Gerenciamento de Ativos de TI |
| Identidade visual | **GATI Enterprise Blue** |
| Versão deste documento | **1.0.0** |
| Data | **23/11/2026** |
| Estado da decisão | **Paleta escolhida como diretriz visual; implementação não iniciada** |
| Abrangência | Dashboard, navegação, formulários, listagens, detalhes, fluxos operacionais e telas públicas, quando aplicável |
| Base de análise | Print da tela “Visão geral”; CSS e templates atuais do repositório `Miranda-txt/G.A.T.I`; documentos de requisitos e arquitetura do GATI; recomendações da skill UI/UX Pro Max |
| Compatibilidade arquitetural | Django Templates + HTMX + Bootstrap 5.3 e CSS da aplicação; nenhuma nova biblioteca necessária |

## 1. Objetivo e posicionamento

O objetivo é conferir ao GATI uma aparência **corporativa, sóbria, confiável, moderna e tecnológica**, preservando sua estrutura funcional. A linguagem visual combina **azul-marinho e azul corporativo** com **superfícies brancas e cinzas neutros**.

A proposta privilegia informação operacional, consistência e legibilidade. O azul identifica a aplicação e a interação principal; verde, âmbar e vermelho permanecem reservados aos estados semânticos de sucesso, atenção e erro. O amarelo suave diferencia **homologação** da produção.

**Limite:** este documento define intenção e especificação visual. Não autoriza alteração em regras de negócio, permissões, endpoints, banco de dados ou comportamento dos fluxos existentes.

## 2. Catálogo oficial da paleta

### 2.1 Identidade, navegação e interação

| Nome | HEX | Token CSS de referência | Função na aplicação | Regras de uso |
|---|---|---|---|---|
| **Azul-marinho** | `#0F253D` | `--sidebar` | Fundo principal da **sidebar** e superfícies institucionais escuras | Aplicar na navegação persistente; usar texto branco ou cinza-azulado claro. Evitar como fundo de todos os cards. |
| **Azul corporativo** | `#1D4ED8` | `--accent` | Cor primária: botão **Cadastrar ativo**, links, controles ativos, ícones de destaque, barras padrão e indicadores de interação | Reservar para ações principais e realces; texto branco quando o azul for usado como preenchimento de botão. |
| **Azul escuro de hover** | `#1E40AF` | `--accent-dark` | Hover/active de botões primários, links e controles azuis | Não confundir com cor semântica de erro; manter estados de foco visíveis. |
| **Azul ardósia** | `#244B70` | `--sidebar-active` | Fundo do item **selecionado** na sidebar e do agrupamento de navegação em destaque | Combinar com texto branco e marcador ativo discernível; seleção não deve depender apenas da cor. |
| **Azul noturno de hover** | `#183A59` | `--sidebar-hover` | Fundo do hover e feedback dos links na sidebar | Distinguir do estado selecionado. Não substituir o estado de foco por hover. |

### 2.2 Neutros, conteúdo e superfícies

| Nome | HEX | Token CSS de referência | Função na aplicação | Regras de uso |
|---|---|---|---|---|
| **Branco** | `#FFFFFF` | `--surface` | Fundo de **cards, painéis, tabelas, topbar, formulários e modais**; texto sobre botão azul e navegação selecionada | Garantir separação do fundo da página por borda/espaçamento. |
| **Cinza gelo** | `#F8FAFC` | `--paper` | Fundo da área de trabalho, espaço entre cards e linhas alternadas discretas de tabela | Superfície neutra predominante; não usar para textos. |
| **Cinza suave** | `#E2E8F0` | `--line` | Bordas de cards, divisórias, tabelas, campos de formulário e separadores | Cor estrutural; para limites de controles essenciais, verificar contraste de 3:1 no componente renderizado. |
| **Grafite** | `#0F172A` | `--ink` | Títulos, números de métricas, dados patrimoniais, cabeçalhos e texto principal | Prioridade para textos densos, identificação de ativos e valores. |
| **Cinza ardósia** | `#475569` | `--muted` | Textos secundários, descrições, metadados, legendas, subtítulos e informações auxiliares | Não clarear indiscriminadamente; manter contraste legível sobre branco e cinza gelo. |
| **Cinza-azulado claro** | `#CBD5E1` | `--sidebar-text` | Texto e ícones secundários da **sidebar escura** | Usar sobre azul-marinho; não usar como texto pequeno sobre superfície branca. |
| **Azul muito claro** | `#EFF6FF` | `--primary-soft` | Fundo de ícones neutros/azuis, chips informativos, destaques secundários, banner de desenvolvimento local quando apropriado | Texto ou ícone em azul escuro; não marcar erro/sucesso apenas com este fundo. |

### 2.3 Cores semânticas e ambientes

| Nome | HEX | Token CSS de referência | Função na aplicação | Regras de uso |
|---|---|---|---|---|
| **Verde de sucesso** | `#166534` | `--success` | Sucesso de operação, status regular e confirmação concluída | Acompanhar com rótulo/ícone; não retornar ao verde como cor primária da marca. |
| **Âmbar de atenção** | `#92400E` | `--warning` | Pendências, garantias a vencer, ações que precisam de atenção | Reservar para significado operacional; incluir texto/ícone, prazo e contexto quando houver. |
| **Vermelho de erro** | `#B91C1C` | `--danger` | Falhas, validação negativa, bloqueios e ações destrutivas | Não utilizar como cor decorativa; associar mensagem objetiva e recuperação. |
| **Amarelo claro de homologação** | `#FFF4CC` | `--environment-staging-bg` | Fundo do banner persistente **AMBIENTE DE HOMOLOGAÇÃO** | Exibir exclusivamente quando o ambiente for staging/homologação; preservar identificação textual. |
| **Marrom-âmbar escuro** | `#78350F` | `--environment-staging-text` | Texto do banner de homologação | Usar sobre `#FFF4CC`, com alto contraste. |

**Total: 17 cores explicitamente especificadas.** Cores adicionais, incluindo fundos claros de sucesso/erro, não estão automaticamente aprovadas por este catálogo e deverão ser propostas e validadas antes do uso.

## 3. Mapeamento por região e componente

| Região / componente | Fundo principal | Texto / conteúdo | Destaques e estados |
|---|---|---|---|
| **Sidebar** | `#0F253D` | `#FFFFFF` para elementos principais; `#CBD5E1` para itens e rótulos secundários | Hover `#183A59`; item ativo `#244B70`; indicador visível de seleção |
| **Logo GATI** | Integrado à sidebar | `#FFFFFF` | Manter legibilidade e proporções da marca; não redesenhar a logomarca neste incremento |
| **Topbar / cabeçalho** | `#FFFFFF` | `#0F172A`; metadados `#475569` | Bordas `#E2E8F0`; links `#1D4ED8` |
| **Plano de fundo da aplicação** | `#F8FAFC` | `#0F172A` / `#475569` | Espaçamento e bordas definem hierarquia |
| **Cards de indicadores** | `#FFFFFF` | Números `#0F172A`; legendas `#475569` | Ícones azuis sobre `#EFF6FF`; ícones âmbar quando houver pendência |
| **Painéis do dashboard** | `#FFFFFF` | Títulos `#0F172A`; resumos `#475569` | Borda `#E2E8F0`; links operacionais `#1D4ED8` |
| **Botão primário** | `#1D4ED8` | `#FFFFFF` | Hover/active `#1E40AF`; foco visível e acionável por teclado |
| **Botões secundários** | `#FFFFFF` ou `#EFF6FF` | `#1E40AF` / `#0F172A` | Borda `#E2E8F0`, conforme estado/contraste; não competir com CTA principal |
| **Links** | Superfície do componente | `#1D4ED8` | Hover `#1E40AF`; indicar interação também por contexto, foco ou sublinhado quando necessário |
| **Tabelas / listagens** | `#FFFFFF` | `#0F172A`; metadados `#475569` | Cabeçalho/linhas suaves `#F8FAFC`; divisórias `#E2E8F0` |
| **Campos de formulário** | `#FFFFFF` | `#0F172A`; ajuda `#475569` | Borda `#E2E8F0`; foco de alta visibilidade com azul corporativo |
| **Estados vazios** | `#FFFFFF` / `#F8FAFC` | Texto `#475569`, mensagem principal `#0F172A` | Ação sugerida em `#1D4ED8`; não apresentar erro falso quando somente não existem registros |
| **Métricas e barras de progresso** | Superfície neutra | Valor e rótulo visíveis | Azul para informação neutra; âmbar/verde/vermelho somente quando o estado justificar |
| **Alertas de sucesso / atenção / erro** | Definir fundo adequado em etapa de implementação | `#166534` / `#92400E` / `#B91C1C` de acordo com o significado | Sempre incluir ícone e texto, não depender exclusivamente de cor |
| **Banner de staging** | `#FFF4CC` | `#78350F` | Texto persistente **AMBIENTE DE HOMOLOGAÇÃO** |
| **Banner de desenvolvimento** | Preferencialmente `#EFF6FF` | `#1E40AF` | Texto persistente que identifique o ambiente local; sujeito a validação no layout |
| **Rodapé** | `#F8FAFC` ou `#FFFFFF` | `#475569` | Links `#1D4ED8`; separador `#E2E8F0` |
| **Assinatura externa / tela pública** | `#F8FAFC` + painéis `#FFFFFF` | `#0F172A` / `#475569` | Botão primário azul; informação crítica legível e isolada da navegação administrativa |

## 4. Migração de cores existentes (referência de planejamento)

Estas substituições correspondem aos tokens atualmente presentes no `backend/static/gati/css/gati.css` inspecionado. **Não realizar substituição global ingênua de todos os verdes:** há cores funcionais e estados semânticos que precisam ser preservados ou reinterpretados por contexto.

| Token atual | Valor anterior | Valor selecionado | Finalidade |
|---|---|---|---|
| `--ink` | `#172B28` | `#0F172A` | Texto principal |
| `--muted` | `#64746E` | `#475569` | Texto secundário |
| `--accent` | `#116951` | `#1D4ED8` | Cor primária |
| `--accent-dark` | `#09533F` | `#1E40AF` | Hover/active |
| `--line` | `#E1E8E3` | `#E2E8F0` | Bordas/divisórias |
| `--paper` | `#F5F7F4` | `#F8FAFC` | Plano de fundo |
| `--sidebar` | `#112E28` | `#0F253D` | Navegação lateral |

A inspeção anterior identificou cores adicionais diretamente nos seletores para ícones, estados, alertas, tabelas, formulários, páginas públicas e documentos. Essas regras deverão ser mapeadas antes da alteração definitiva.

## 5. Tokens CSS de referência (não aplicados)

O bloco abaixo registra a nomenclatura e os valores selecionados. **É uma especificação inicial, não um patch CSS pronto para substituir o arquivo real**. Na implementação, os valores e aliases Bootstrap deverão ser conciliados com estados de hover, focus, disabled e componentes existentes.

```css
:root {
  /* Identidade, navegacao e interacao */
  --sidebar: #0F253D;
  --sidebar-hover: #183A59;
  --sidebar-active: #244B70;
  --sidebar-text: #CBD5E1;
  --accent: #1D4ED8;
  --accent-dark: #1E40AF;

  /* Superficies, texto e estrutura */
  --surface: #FFFFFF;
  --paper: #F8FAFC;
  --line: #E2E8F0;
  --ink: #0F172A;
  --muted: #475569;
  --primary-soft: #EFF6FF;

  /* Estados semanticamente distintos */
  --success: #166534;
  --warning: #92400E;
  --danger: #B91C1C;

  /* Sinalizacao de ambiente */
  --environment-staging-bg: #FFF4CC;
  --environment-staging-text: #78350F;

  /* Compatibilidade inicial com Bootstrap; verificar estados */
  --bs-primary: var(--accent);
  --bs-link-color: var(--accent);
  --bs-link-hover-color: var(--accent-dark);
}
```

## 6. Acessibilidade e legibilidade

O requisito **RNF-010** define responsividade para desktop, notebook e tablet e **WCAG 2.2 AA** como alvo técnico. A paleta foi selecionada para facilitar esse objetivo, mas conformidade depende do contraste final, tamanho do texto, hierarquia, foco, semântica HTML e testes reais.

### 6.1 Exemplos de combinações e contraste

Razões calculadas pela fórmula WCAG para as cores opacas indicadas:

| Texto / elemento | Fundo | Razão de contraste aproximada | Avaliação para texto normal |
|---|---|---:|---|
| `#FFFFFF` | `#1D4ED8` | **6,70:1** | Atende AA |
| `#FFFFFF` | `#1E40AF` | **8,72:1** | Atende AA |
| `#FFFFFF` | `#244B70` | **9,07:1** | Atende AA |
| `#CBD5E1` | `#0F253D` | **10,46:1** | Atende AA |
| `#0F172A` | `#F8FAFC` | **17,06:1** | Atende AA |
| `#475569` | `#FFFFFF` | **7,58:1** | Atende AA |
| `#78350F` | `#FFF4CC` | **8,24:1** | Atende AA |
| `#166534` | `#FFFFFF` | **7,13:1** | Atende AA |
| `#92400E` | `#FFFFFF` | **7,09:1** | Atende AA |
| `#B91C1C` | `#FFFFFF` | **6,47:1** | Atende AA |

Critérios de referência: **4,5:1** para texto normal; **3:1** para texto grande e componentes não textuais essenciais, quando aplicável. Bordas suaves e ícones de baixa relevância decorativa não substituem limites e estados claramente perceptíveis. Verificar contraste das combinações reais (incluindo fundos sobrepostos e opacidade), não apenas dos hexadecimais isolados.

### 6.2 Regras de uso acessível

1. Não usar apenas cor para comunicar status, erro, sucesso, risco, campo obrigatório ou item selecionado; acrescentar texto e/ou ícone.
2. Manter foco de teclado bem visível em controles, links, menu lateral e modais, inclusive sobre fundo azul-marinho.
3. Evitar legendas excessivamente pequenas; a tela atual usa textos secundários de 9 a 11 px em alguns lugares, que devem ser revistos na etapa de implementação.
4. Preservar o banner textual de homologação: não depender exclusivamente do fundo amarelo para identificar o ambiente.
5. Testar estados normal, hover, focus, active, disabled, erro e carregamento.
6. Testar o dashboard, navegação e formulários em desktop, notebook e tablet e verificar comportamentos adicionais em telas estreitas.
7. Preservar semântica, rotulagem e mensagens de erro; a mudança visual não deve enfraquecer validação nem autorização do lado do servidor.

## 7. Orientações de implementação futura

A alteração deve ser **incremental e reversível**, preservando a arquitetura Django Templates/HTMX/Bootstrap e os fluxos aprovados do MVP.

**Sequência sugerida:**

1. Inspecionar o estado real do repositório e executar a baseline de verificação antes de tocar o código.
2. Centralizar as cores em tokens semânticos, mantendo compatibilidade com variáveis existentes.
3. Aplicar à sidebar, topbar, botões e banners de ambiente.
4. Aplicar aos cards, painéis, indicadores e ações da “Visão geral”.
5. Revisar listagens, formulários, detalhes, Termos, telas de assinatura e estados semânticos.
6. Testar contraste, foco, responsividade, legibilidade, regressão visual e funcional, inclusive no ambiente de staging.
7. Atualizar documentação/rastreabilidade e avaliar `README.md` conforme o alcance real das alterações.

### 7.1 Arquivos relevantes, sujeitos à nova inspeção

| Arquivo | Papel esperado |
|---|---|
| `backend/static/gati/css/gati.css` | Fonte principal de tokens e estilos da aplicação |
| `backend/templates/base.html` | Sidebar, topbar, navegação e banners de ambiente |
| `backend/templates/dashboard.html` | Cards, painéis e estados vazios da visão geral |
| Demais templates relevantes | Avaliação de consistência visual por fluxo |
| Testes existentes | Regra de regressão e proteção de funcionalidades |

### 7.2 Critérios de aceite visual (para a fase de alteração)

- [ ] A sidebar e os itens selecionados usam a diretriz Enterprise Blue com estado ativo inequívoco.
- [ ] Os botões e links primários usam azul corporativo com hover e foco definidos.
- [ ] Todos os cards e painéis mantêm hierarquia e contraste coerentes.
- [ ] Mensagens de sucesso, alerta e erro usam cores semânticas com indicadores textuais.
- [ ] Homologação permanece explicitamente sinalizada e visualmente distinta da produção.
- [ ] Textos, elementos interativos e ícones relevantes são avaliados conforme WCAG 2.2 AA aplicável.
- [ ] Layout permanece utilizável em desktop, notebook e tablet; testes de tela estreita são realizados.
- [ ] Fluxos, permissões, contratos e dados não são alterados pela atualização visual.
- [ ] Testes direcionados, verificação completa e revisão de regressão aprovados antes de qualquer commit de código.

## 8. Governança, escopo e registro de modificações

- **Estado neste documento:** identidade de cores escolhida e registrada; nenhuma mudança de CSS, HTML, repositório ou ambiente foi executada para aplicá-la.
- **Precedência:** este guia orienta a aparência e deve permanecer subordinado aos requisitos, segurança, acessibilidade e decisões arquiteturais aprovadas do GATI.
- **Controle de alterações:** qualquer alteração na paleta definida deve ser documentada em nova revisão com justificativa, impactos e testes, evitando cores ad hoc.
- **Local sugerido no repositório quando o responsável decidir versionar:** `docs/design-system/GATI_Paleta_Cores_Enterprise_Blue_v1.0.0.md` (caminho sugerido, não criado no GitHub).
- **Commit documental opcional (manual):** `docs(ui): registra paleta corporativa Enterprise Blue`.

### Histórico

| Versão | Data | Alteração |
|---|---|---|
| 1.0.0 | 23/11/2026 | Registro inicial da paleta Enterprise Blue, funções por cor, mapeamento de componentes, referências de acessibilidade e plano para adoção futura. |

---

**Resumo da decisão:** azul-marinho `#0F253D` para estrutura; azul corporativo `#1D4ED8` para interação; azul ardósia `#244B70` para seleção; branco `#FFFFFF` e cinza gelo `#F8FAFC` para superfícies; grafite `#0F172A` e cinza ardósia `#475569` para leitura; verde `#166534`, âmbar `#92400E` e vermelho `#B91C1C` exclusivamente como cores funcionais, além da sinalização de staging `#FFF4CC` / `#78350F`.
