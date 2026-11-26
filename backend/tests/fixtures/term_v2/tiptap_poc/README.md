# PoC Tiptap OSS — T01 (somente laboratório)

Esta prova testa o **schema ProseMirror real** por meio de `getSchema` do Tiptap
3.35.0. É headless: não é a interface visual definitiva do GATI.
Sem Cloud, Pro, contas, credenciais, URLs externas ou gravação produtiva.

## Limites do experimento

- Documento `schema_version=2` (v1 permanece inalterado no backend).
- Tabela até 100 linhas/12 colunas; total de 1.000 nós/128 KiB.
- Recurso por UUID opaco existente na allowlist, PNG resolvido exclusivamente
  pelo servidor após scanner; nenhum URL `src` é aceito no JSON.
- Exatamente um `patrimonialBlock`, atômico, sem edição e sem atributos do usuário.
- Guard de transação no cliente e normalizador estrito no laboratório;
  **a validação produtiva no servidor ainda NÃO existe**.

O `package.json` fixa as dependências OSS na versão 3.35.0. O CI gera um
`package-lock.json` transitório, verifica seu hash em `package-lock.sha256`,
executa `npm ci`/audit e publica o lock como artefato. O lock completo deve
ser versionado após aceite da PoC; a estratégia de hash temporária não é
substituto permanente do lock reproduzível versionado.

Execução em runner isolado com acesso ao registry:

```sh
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
sha256sum -c package-lock.sha256
npm ci --ignore-scripts --no-audit --no-fund
npm audit --omit=dev --audit-level=high
npm test
```

Faltam ensaio visual em Chromium da implementação Tiptap, integração
servidor/editor, undo/redo, IME, leitores de tela, seleção entre tabelas,
headings/footers, imagens de recursos aprovados e renderização WYSIWYG.
Nenhuma escolha de Tiptap/ProseMirror está aprovada para T04.
