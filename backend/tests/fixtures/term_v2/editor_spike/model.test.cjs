'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const model = require('./model.js');

test('JSON contém layout A4, variável e bloco patrimonial', () => {
  const doc = model.createDocument({title: 'Termo', blocks: [
    {type: 'paragraph', content: [model.text('Responsável: '), model.variable('responsavel.nome', 'ENTREGA')]},
  ]});
  assert.equal(doc.schema_version, 1);
  assert.deepEqual(doc.content.content[1], {type: 'patrimonialBlock'});
  assert.equal(doc.layout.paper, 'A4');
  assert.equal(doc.content.content[2].content[1].attrs.key, 'responsavel.nome');
});

test('catálogo vincula variáveis à classificação', () => {
  assert.throws(() => model.variable('emprestimo.prazo_original', 'ENTREGA'), /incompatível/);
  assert.deepEqual(model.variable('emprestimo.prazo_original', 'EMPRESTIMO'), {
    type: 'variable', attrs: {key: 'emprestimo.prazo_original'},
  });
  assert.throws(() => model.variable('invalido', 'ENTREGA'), /incompatível/);
});

test('não aceita links, marcas duplicadas nem textos longos', () => {
  assert.throws(() => model.text('clique', ['link']), /Marca inválida/);
  assert.throws(() => model.text('clique', ['bold', 'bold']), /Marca inválida/);
  assert.throws(() => model.text('x'.repeat(4097)), /excede/);
  assert.throws(() => model.createDocument({title: '', blocks: []}), /Título/);
});

test('HTML aparente é serializado como texto, não markup executável', () => {
  assert.deepEqual(model.text('<script>alert(1)</script>'), {
    type: 'text', text: '<script>alert(1)</script>',
  });
});
