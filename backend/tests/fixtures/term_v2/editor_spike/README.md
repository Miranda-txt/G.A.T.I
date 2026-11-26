# Editor visual — spike T01 (isolado)

Protótipo **offline, sem rede, sem rotas Django, sem gravação, sem autenticação**.
Abrir `index.html` localmente para avaliar o aspecto e a interação.
Não utilizar dados pessoais ou termos reais. Não é interface de homologação ou produto pronto.

## Funcionalidades demonstradas

- Estilo Enterprise Blue, folha A4 ilustrativa, toolbar de quatro marcas, lista e parágrafo.
- Catálogo de variáveis por classificação, inseridas como chips sem valor real.
- Bloco patrimonial obrigatório visível e fora de `contenteditable`; JSON constrói um nó protegido.
- Colagem convertida em texto puro; drop de arquivo bloqueado; HTML desconhecido falha no export.
- Exporta JSON estruturado local; servidor ainda precisa validar e resolver campos.

**Restrições importantes:** sem renderer server-side ou PDF na UI, sem imagens autorizadas,
tabelas, cabeçalho/rodapé dinâmico, undo/redo garantido ou integração com versões de modelo.
Não atende a promessa de editor equivalente ao Word; não escolhe Tiptap/ProseMirror definitivamente.
A manipulação nativa de seleção não cobre todas as seleções complexas, tecnologias assistivas
ou navegadores; exige E2E manual/automatizado de teclado, foco, colagem, zoom e responsividade.
O esquema experimental `schema.py` valida JSON independentemente do cliente e rejeita
campos desconhecidos, recursos remotos, profundidade/tamanho excessivos e remoção/duplicação
do bloco patrimonial. Limites são provisórios.

Verificar a partir de `backend/`:
```sh
python -m pytest tests/test_term_v2_editor_spike.py -v
node --check tests/fixtures/term_v2/editor_spike/editor.js
node --test tests/fixtures/term_v2/editor_spike/model.test.cjs
```

A execução E2E com navegador e escolha de biblioteca são gates pendentes da T01.
