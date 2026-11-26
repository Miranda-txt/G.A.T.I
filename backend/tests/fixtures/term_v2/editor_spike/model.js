/* Modelo de autoria experimental; backend Python permanece autoritativo. */
(function (scope) {
  'use strict';
  const common = [
    'responsavel.nome', 'responsavel.documento_mascarado', 'responsavel.departamento',
    'processo.tipo', 'processo.data', 'processo.localizacao', 'emissao.numero', 'emissao.data',
  ];
  const loan = ['emprestimo.inicio', 'emprestimo.prazo_original', 'emprestimo.finalidade'];
  const classes = ['ENTREGA', 'DEVOLUCAO', 'EMPRESTIMO'];
  const marks = ['bold', 'italic', 'underline', 'strike'];

  function allowedVariables(classification) {
    if (!classes.includes(classification)) throw new Error('Classificação inválida');
    return classification === 'EMPRESTIMO' ? [...common, ...loan] : [...common];
  }

  function text(value, activeMarks = []) {
    if (typeof value !== 'string' || !value.length || value.length > 4096) {
      throw new Error('Texto inválido ou excede 4.096 caracteres');
    }
    if (activeMarks.length > 4 || new Set(activeMarks).size !== activeMarks.length ||
        activeMarks.some((name) => !marks.includes(name))) throw new Error('Marca inválida');
    const node = {type: 'text', text: value};
    if (activeMarks.length) node.marks = activeMarks.map((type) => ({type}));
    return node;
  }

  function variable(key, classification) {
    if (!allowedVariables(classification).includes(key)) throw new Error('Campo incompatível');
    return {type: 'variable', attrs: {key}};
  }

  function createDocument({title, blocks, classification = 'ENTREGA'}) {
    if (typeof title !== 'string' || !title.trim()) throw new Error('Título obrigatório');
    if (!Array.isArray(blocks) || blocks.length > 200) throw new Error('Blocos acima do limite');
    allowedVariables(classification);
    const content = [
      {type: 'heading', attrs: {level: 2}, content: [text(title)]},
      {type: 'patrimonialBlock'},
      ...blocks,
    ];
    const result = {schema_version: 1, classification,
      layout: {paper: 'A4', orientation: 'portrait', margin_mm: 20},
      content: {type: 'doc', content}};
    if (new TextEncoder().encode(JSON.stringify(result)).length > 65536) {
      throw new Error('Documento excede limite de bytes');
    }
    return result;
  }

  const api = Object.freeze({allowedVariables, text, variable, createDocument});
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  scope.GatiEditorModel = api;
})(typeof window !== 'undefined' ? window : globalThis);
