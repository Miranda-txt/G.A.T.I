import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { EditorState } from '@tiptap/pm/state';
import { createRichSchema, normalizeRichDocument, protectTransaction } from './rich_schema.mjs';

const IMAGE_ID = 'a1c92077-aaaa-4f11-8b22-001122334455';
const baseContent = () => [
  { type: 'heading', attrs: { level: 2 },
    content: [{ type: 'text', text: 'Termo de empréstimo — patrimônio' }] },
  { type: 'paragraph', content: [
    { type: 'text', text: 'Responsável: ', marks: [{ type: 'bold' }] },
    { type: 'variable', attrs: { key: 'responsavel.nome' } },
  ] },
  { type: 'patrimonialBlock' },
];
const table = (rows = 2) => ({ type: 'table', content: Array.from({ length: rows }, (_, i) => ({
  type: 'tableRow', content: [0, 1].map(j => ({
    type: i === 0 ? 'tableHeader' : 'tableCell',
    content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Linha ' + i + ', coluna ' + j }] }],
  })),
})) });
const make = (classification = 'EMPRESTIMO', blocks = []) => ({
  schema_version: 2, classification,
  layout: { paper: 'A4', orientation: 'portrait', margin_mm: 20 },
  content: { type: 'doc', content: [...baseContent(), ...blocks] },
});
const normalize = (doc, allowed = [IMAGE_ID]) =>
  normalizeRichDocument(doc, { allowedResourceIds: allowed });

test('uses real Tiptap/ProseMirror schema for a Portuguese long table', () => {
  const original = make('ENTREGA', [table(100)]);
  const result = normalize(original);
  const schema = createRichSchema();
  const node = schema.nodeFromJSON(result.content);
  assert.doesNotThrow(() => node.check());
  assert.equal(node.child(node.childCount - 1).childCount, 100);
  assert.deepEqual(normalize(result), result);
});

test('includes a sole non-editable atomic patrimonial block in the schema', () => {
  const schema = createRichSchema();
  assert.equal(schema.nodes.patrimonialBlock.spec.atom, true);
  assert.equal(schema.nodes.patrimonialBlock.spec.selectable, false);
  assert.equal(schema.nodes.patrimonialBlock.spec.draggable, false);
  assert.equal(schema.nodes.patrimonialBlock.spec.isolating, true);
  const doc = normalize(make());
  assert.equal(doc.content.content.filter(n => n.type === 'patrimonialBlock').length, 1);
});

test('does not allow deletion of patrimonial block in a transaction', () => {
  const schema = createRichSchema();
  const node = schema.nodeFromJSON(normalize(make()).content);
  const state = EditorState.create({ schema, doc: node });
  let found = null;
  node.descendants((n, pos) => { if (n.type.name === 'patrimonialBlock') found = [pos, n.nodeSize]; });
  const deleteProtected = state.tr.delete(found[0], found[0] + found[1]);
  assert.equal(protectTransaction(deleteProtected, state), false);
  const editHeading = state.tr.insertText('Versão: ', 2);
  assert.equal(protectTransaction(editHeading, state), true);
});

test('rejects removal and duplication of the patrimonial block', () => {
  const missing = make();
  missing.content.content = missing.content.content.filter(n => n.type !== 'patrimonialBlock');
  assert.throws(() => normalize(missing), /patrimonial/i);
  const extra = make();
  extra.content.content.push({ type: 'patrimonialBlock' });
  assert.throws(() => normalize(extra), /patrimonial/i);
});

test('rejects all client-specified attributes or content on protected block', () => {
  for (const value of [
    { type: 'patrimonialBlock', attrs: { editable: true } },
    { type: 'patrimonialBlock', content: [{ type: 'text', text: 'spoof' }] },
  ]) {
    const doc = make();
    doc.content.content[2] = value;
    assert.throws(() => normalize(doc), /attr|patrimonial|campo/i);
  }
});

test('allows only authorized immutable resource IDs, never HTTP or file URLs', () => {
  const valid = { type: 'resourceImage', attrs: {
    resourceId: IMAGE_ID, alt: 'Etiqueta patrimonial', width: 240, height: 180,
  } };
  const out = normalize(make('ENTREGA', [valid]));
  assert.equal(out.content.content.at(-1).attrs.resourceId, IMAGE_ID);
  for (const bad of [
    { ...valid, attrs: { ...valid.attrs, resourceId: 'https://127.0.0.1/secret' } },
    { ...valid, attrs: { ...valid.attrs, resourceId: 'file:///etc/passwd' } },
    { ...valid, attrs: { ...valid.attrs, src: 'https://example.invalid/anything' } },
    { ...valid, attrs: { ...valid.attrs, resourceId: 'b1c92077-bbbb-4f11-8b22-001122334455' } },
  ]) assert.throws(() => normalize(make('ENTREGA', [bad])), /recurso|atributo|imagem|ID/i);
  assert.throws(() => normalize(make('ENTREGA', [valid]), []), /recurso|autoriz/i);
});

test('rejects remote links, scripts, unknown marks and arbitrary HTML/CSS', () => {
  const payloads = [
    { type: 'iframe', attrs: { src: 'https://example.invalid/' } },
    { type: 'paragraph', content: [{ type: 'text', text: 'texto',
      marks: [{ type: 'link', attrs: { href: 'javascript:alert(1)' } }] }] },
    { type: 'paragraph', attrs: { style: 'background:url(file:///etc/passwd)' } },
    { type: 'text', text: '<img src=x onerror=alert(1)>', attrs: { onerror: 'alert(1)' } },
  ];
  for (const injected of payloads) {
    assert.throws(() => normalize(make('ENTREGA', [injected])), /n[oó]|marca|attr|permitid|html|css/i);
  }
});

test('preserves literal script text without executing it', () => {
  const p = { type: 'paragraph',
    content: [{ type: 'text', text: '<script>alert(1)</script> é apenas texto' }] };
  const out = normalize(make('ENTREGA', [p]));
  assert.equal(out.content.content.at(-1).content[0].text, p.content[0].text);
});

test('checks variable catalog against document classification', () => {
  const invalid = make('ENTREGA', [{
    type: 'paragraph',
    content: [{ type: 'variable', attrs: { key: 'emprestimo.prazo_original' } }],
  }]);
  assert.throws(() => normalize(invalid), /vari[aá]vel|classifica/i);
  invalid.classification = 'EMPRESTIMO';
  assert.doesNotThrow(() => normalize(invalid));
});

test('enforces provisional size and schema limits without mutating input', () => {
  const source = make('ENTREGA', [table(100)]);
  const pristine = structuredClone(source);
  normalize(source);
  assert.deepEqual(source, pristine);
  const invalidVersion = make();
  invalidVersion.schema_version = 1;
  assert.throws(() => normalize(invalidVersion), /vers[aã]o|schema/i);
  const oversized = make('ENTREGA', [{
    type: 'paragraph', content: [{ type: 'text', text: 'x'.repeat(4097) }],
  }]);
  assert.throws(() => normalize(oversized), /texto|limite/i);
});

const sharedCases = JSON.parse(readFileSync(new URL('./schema_contract_cases.json', import.meta.url), 'utf8'));
for (const entry of sharedCases) {
  test('shared contract: ' + entry.id, () => {
    const source = structuredClone(entry.document);
    const execute = () => normalize(entry.document, entry.allowed_resource_ids);
    if (entry.accept) {
      assert.deepEqual(execute(), source);
    } else {
      assert.throws(execute, Error);
    }
    assert.deepEqual(entry.document, source);
  });
}
