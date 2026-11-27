# PoC Tiptap OSS — T01 (somente laboratório)

Esta prova testa o **schema ProseMirror real** por meio de `getSchema` do Tiptap
3.35.0 e inclui uma **PoC visual real no Chromium**. Não é a interface
definitiva, nem uma rota/API produtiva do GATI.
Sem Cloud, Pro, contas, credenciais, URLs externas ou gravação produtiva.

## Limites do experimento

- Documento `schema_version=2` (v1 permanece inalterado no backend).
- Tabela até 100 linhas/12 colunas; total de 1.000 nós/128 KiB.
- Recurso por UUID opaco existente na allowlist, PNG resolvido exclusivamente
  pelo servidor após scanner; nenhum URL `src` é aceito no JSON.
- Exatamente um `patrimonialBlock`, atômico, sem edição e sem atributos do usuário.
- Guard de transação no cliente e normalizador estrito no laboratório;
  **a validação produtiva no servidor ainda NÃO existe**.

O `package.json` fixa as dependências OSS na versão 3.35.0. O
`package-lock.json` experimental completo foi recuperado do artefato
[15196270278](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45995627126/artifacts/15196270278)
do CI GREEN de `e78af56`, conferido byte a byte pelo SHA-256 já registrado
em `package-lock.sha256` e pelo Git blob. O CI passa a consumir esse lock
diretamente, sem resolver novamente as versões transitivas; verifica o
hash, executa `npm ci`/audit, verifica ausência de alteração no lock e
publica o artefato. O primeiro CI dessa mudança ainda deve confirmar a
instalação a partir do lock versionado. Não é aprovação da dependência
para produção.

Execução em runner isolado com acesso ao registry:

```sh
sha256sum -c package-lock.sha256
npm ci --ignore-scripts --no-audit --no-fund
git diff --exit-code -- package-lock.json
npm audit --omit=dev --audit-level=high
npm test
```

## Interface visual experimental — 26/11/2026

Arquivos de laboratório: `visual.html`, `visual.css`, `visual_app.mjs`
e `rich_schema.py`. A página usa a identidade Enterprise Blue do GATI,
com edição direta de texto e tabela, toolbar acessível, negrito/itálico,
desfazer/refazer, placeholder de recurso aprovado (sem buscar imagem remota),
campo de variável e bloco patrimonial não editável.

O `visual_app.mjs` importa **Tiptap OSS real**, ProseMirror history e
guardas de transação. Um bundle local estático é gerado no CI com
esbuild `0.27.0` e embutido pelo harness CDP no teste, sem HTTP/CDN externos.
O `package-lock.json` de Tiptap continua experimental; esbuild está
versionado no comando, mas **não está no lock**, portanto não é
estratégia definitiva de build reproduzível.

O teste `tests/test_term_v2_tiptap_visual_browser.py` usa Chromium real
nos viewports de 320, 375 e 1366 px, checa reflow com fonte raiz a 200%,
foco visível, semântica da barra de ferramentas, unicidade do bloco protegido,
formatação, undo/redo, inserção de tabela e recurso autorizado sem URL,
tentativa de excluir o bloco e roundtrip de JSON com validador Python
experimental. Duas capturas sintéticas de 375 e 1366 px são publicadas como
artefato na execução do CI. **O validador Python não substitui a validação,
permissão por recurso, versionamento nem a persistência do servidor real.**

[CI GREEN do código, commit 927b0f0](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45863153297):
**299 coletados, 297 aprovados, 2 ignorados, 0 falhas**; segurança no
[mesmo commit](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45863153300)
aprovada. Capturas mobile/desktop foram inspecionadas visualmente.

Para executar a página em laboratório local isolado, após o setup de Node
e das dependências Tiptap já indicado:

```sh
npm exec --yes --package=esbuild@0.27.0 -- esbuild visual_app.mjs --bundle --platform=browser --format=iife --target=es2022 --outfile=dist/visual.bundle.js
python -m http.server 8765 --bind 127.0.0.1
```

Acessar `http://127.0.0.1:8765/visual.html` apenas em ambiente de testes.
Não colocar o servidor experimental em rede ou anexá-lo às rotas Django.
O bundle não é versionado no Git e o build envolve obtenção de pacotes
via registry. Não usar dados reais nem inferir permissões do usuário a
partir da interface.

**Pendências:** leitores de tela, IME, mobile touch real, acessibilidade
abrangente, tabelas complexas/mescladas, edição arbitrária dentro de células,
colagem de conteúdo rico, integração com snapshot/assinatura, imagem real
aprovada após scanner e persistência/validação/autorização Django.
Nenhuma escolha de Tiptap/ProseMirror está aprovada para T04.

## Contrato adversarial compartilhado — 27/11/2026

Decisão aprovada para a correção experimental: JavaScript valida para feedback;
Python é a autoridade de validação estrutural no futuro backend, sem confiar
em DOM, HTML ou no catálogo fornecido pelo cliente. O corpus
`schema_contract_cases.json` é consumido pelos testes Node e Pytest.

- Raiz obrigatoriamente `doc`; conteúdo ausente permitido somente quando
  previsto, mas `null` não equivale a ausência.
- UUID v4 canônico minúsculo, inclusive no catálogo de recursos.
- Limites de 4.096 pontos de código Unicode por nó de texto e 160 por
  descrição de imagem; rejeitar C0 exceto TAB/LF, DEL e substitutos isolados.
  Descrições exclusivamente compostas por whitespace (incluindo NEL e BOM)
  são inválidas. Não se trata de contagem de grafemas.
- Tipos malformados devem ser rejeitados de forma controlada; validar
  hierarquia e profundidade antes de serializar e medir os bytes UTF-8.
- Permanecem os limites de 128 KiB, 1.000 nós, profundidade 8, 100 linhas
  e 12 células por linha, catálogo por classificação e bloco patrimonial
  obrigatório e único. Nenhum URL externo ou atributo desconhecido.

RED: [CI do commit a71b539](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45994004106),
24/33 testes Node aprovados, 9 falhas; reprodução local dos 23 casos
Python em 3.13.5 (adaptação de sintaxe da exceção somente na cópia RED):
14 aprovados, 9 falhas. Após a correção, os 23 casos Python passaram
localmente. O CI de `8699fcf` confirmou 33/33 testes Node, mas falhou
exclusivamente no Ruff format. Após correção de formatação em `e78af56`,
[Núcleo Patrimonial](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45995627126)
e [Segurança](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45995627009)
ficaram GREEN: 33/33 Node (23 compartilhados), 320/322 Pytest (2 smoke
ClamAV opcionais ignorados), 1 aviso, 193 arquivos formatados, Chromium,
Django, OpenAPI, cobertura e Docker aprovados. Não declarar equivalência
exaustiva: limites
numéricos na fronteira JSON, canonicalização, clipboard rico, validação
HTTP e autorização por recurso ainda exigem homologação. Nenhuma alteração
produtiva, nova dependência ou liberação de T02.
