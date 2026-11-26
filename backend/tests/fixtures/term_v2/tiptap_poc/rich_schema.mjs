/**
 * T01: Contrato experimental de documento rico. Não importar no GATI produtivo.
 * O cliente/editor Tiptap NUNCA é a fonte de autorização.
 */
import { getSchema, Node } from '@tiptap/core';
import Document from '@tiptap/extension-document';
import Paragraph from '@tiptap/extension-paragraph';
import Text from '@tiptap/extension-text';
import Heading from '@tiptap/extension-heading';
import Bold from '@tiptap/extension-bold';
import Italic from '@tiptap/extension-italic';
import Underline from '@tiptap/extension-underline';
import { TableKit } from '@tiptap/extension-table';

const COMMON = new Set([
  'responsavel.nome', 'responsavel.documento_mascarado',
  'responsavel.departamento', 'processo.tipo', 'processo.data',
  'processo.localizacao', 'emissao.numero', 'emissao.data',
]);
const LOAN = new Set(['emprestimo.inicio', 'emprestimo.prazo_original', 'emprestimo.finalidade']);
const RESOURCE_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const NODE_SET = new Set([
  'doc', 'heading', 'paragraph', 'text', 'variable', 'patrimonialBlock',
  'table', 'tableRow', 'tableCell', 'tableHeader', 'resourceImage',
]);
const MARK_SET = new Set(['bold', 'italic', 'underline']);
const MAX_NODES = 1000, MAX_DEPTH = 8, MAX_BYTES = 131072, MAX_TEXT = 4096;
const exact = (obj, required, optional = []) => {
  if (obj === null || typeof obj !== 'object' || Array.isArray(obj) ||
      required.some(key => !Object.hasOwn(obj, key)) ||
      Object.keys(obj).some(key => !required.includes(key) && !optional.includes(key))) {
    throw new Error('Atributos ou campos não permitidos');
  }
};
const strictText = value => {
  if (typeof value !== 'string' || value.length < 1 || value.length > MAX_TEXT ||
      /[\u0000-\u0008\u000b-\u001f\u007f]/u.test(value)) {
    throw new Error('Texto inválido ou excede limite');
  }
};

const ProtectedBlock = Node.create({
  name: 'patrimonialBlock',
  group: 'block',
  atom: true,
  isolating: true,
  selectable: false,
  draggable: false,
  parseHTML() { return [{ tag: 'aside[data-gati-patrimonial]' }]; },
  renderHTML() { return ['aside', { 'data-gati-patrimonial': '', contenteditable: 'false', role: 'note' },
    'Bloco patrimonial proveniente do processo — somente leitura']; },
});

const Variable = Node.create({
  name: 'variable', group: 'inline', inline: true, atom: true, selectable: true,
  addAttributes() { return { key: { default: null } }; },
  parseHTML() { return [{ tag: 'span[data-gati-variable]' }]; },
  renderHTML({ node }) {
    return ['span', { 'data-gati-variable': node.attrs.key, contenteditable: 'false' }, '{{' + node.attrs.key + '}}'];
  },
});

const ResourceImage = Node.create({
  name: 'resourceImage', group: 'block', atom: true, selectable: true,
  addAttributes() {
    return {
      resourceId: { default: null },
      alt: { default: '' },
      width: { default: null },
      height: { default: null },
    };
  },
  parseHTML() { return [{ tag: 'figure[data-gati-resource-id]' }]; },
  // Never synthesize a src from JSON. Only the authenticated application may
  // resolve opaque ids to scanned private assets after server-side checks.
  renderHTML({ node }) {
    return ['figure', { 'data-gati-resource-id': node.attrs.resourceId, role: 'img',
      'aria-label': node.attrs.alt }, 'Recurso aprovado'];
  },
});

export function createRichSchema() {
  return getSchema([
    Document, Paragraph, Text, Heading.configure({ levels: [1, 2, 3] }),
    Bold, Italic, Underline, TableKit, Variable, ProtectedBlock, ResourceImage,
  ]);
}

function walk(node, context, depth, parent) {
  if (depth > MAX_DEPTH) throw new Error('Profundidade acima do limite');
  exact(node, ['type'], ['attrs', 'content', 'text', 'marks']);
  if (!NODE_SET.has(node.type)) throw new Error('Nó não permitido');
  context.count += 1;
  if (context.count > MAX_NODES) throw new Error('Limite de nós atingido');
  const type = node.type;
  const allowed = {
    doc: ['heading', 'paragraph', 'patrimonialBlock', 'table', 'resourceImage'],
    heading: ['text', 'variable'], paragraph: ['text', 'variable'],
    table: ['tableRow'], tableRow: ['tableCell', 'tableHeader'],
    tableCell: ['paragraph'], tableHeader: ['paragraph'],
  };
  if (parent && !(allowed[parent] || []).includes(type)) throw new Error('Hierarquia de nós inválida');
  if (type === 'text') {
    exact(node, ['type', 'text'], ['marks']);
    strictText(node.text);
    if (node.marks !== undefined) {
      if (!Array.isArray(node.marks) || node.marks.length > 3) throw new Error('Marcas inválidas');
      const seen = new Set();
      for (const mark of node.marks) {
        exact(mark, ['type']);
        if (!MARK_SET.has(mark.type) || seen.has(mark.type)) throw new Error('Marca não permitida');
        seen.add(mark.type);
      }
    }
    return;
  }
  if (type === 'patrimonialBlock') {
    exact(node, ['type']);
    context.protected += 1;
    return;
  }
  if (type === 'variable') {
    exact(node, ['type', 'attrs']);
    exact(node.attrs, ['key']);
    const key = node.attrs.key;
    if (typeof key !== 'string' || !(COMMON.has(key) ||
        (context.classification === 'EMPRESTIMO' && LOAN.has(key)))) {
      throw new Error('Variável incompatível com classificação');
    }
    return;
  }
  if (type === 'resourceImage') {
    exact(node, ['type', 'attrs']);
    exact(node.attrs, ['resourceId', 'alt', 'width', 'height']);
    const { resourceId, alt, width, height } = node.attrs;
    if (typeof resourceId !== 'string' || !RESOURCE_ID.test(resourceId) ||
      !context.allowed.has(resourceId)) throw new Error('ID de recurso não autorizado');
    if (typeof alt !== 'string' || !alt.trim() || alt.length > 160 ||
        !Number.isInteger(width) || !Number.isInteger(height) ||
        width < 16 || height < 16 || width > 2000 || height > 2000) {
      throw new Error('Atributos da imagem inválidos');
    }
    return;
  }
  if (type === 'heading') {
    exact(node, ['type', 'attrs', 'content']);
    exact(node.attrs, ['level']);
    if (![1, 2, 3].includes(node.attrs.level)) throw new Error('Cabeçalho inválido');
  } else if (type === 'paragraph') {
    exact(node, ['type'], ['content']);
  } else if (type === 'doc' || type === 'table' || type === 'tableRow' ||
             type === 'tableCell' || type === 'tableHeader') {
    exact(node, ['type', 'content']);
  }
  const children = node.content ?? [];
  if (!Array.isArray(children) || (type !== 'paragraph' && children.length === 0)) {
    throw new Error('Conteúdo obrigatório');
  }
  if (type === 'table' && (children.length > 100 || children.length < 1)) {
    throw new Error('Limite de linhas da tabela');
  }
  if (type === 'tableRow' && (children.length > 12 || children.length < 1)) {
    throw new Error('Limite de células da tabela');
  }
  if (type === 'tableCell' || type === 'tableHeader') {
    if (children.length !== 1) throw new Error('Célula deve ter exatamente um parágrafo');
  }
  for (const child of children) walk(child, context, depth + 1, type);
}

/**
 * Enforce the allowlist before parsing ProseMirror JSON, because ProseMirror
 * intentionally ignores unknown properties and can default missing attrs.
 */
export function normalizeRichDocument(document, { allowedResourceIds = [] } = {}) {
  exact(document, ['schema_version', 'classification', 'layout', 'content']);
  if (document.schema_version !== 2) throw new Error('Versão de schema não suportada');
  if (!['ENTREGA', 'DEVOLUCAO', 'EMPRESTIMO'].includes(document.classification)) {
    throw new Error('Classificação inválida');
  }
  exact(document.layout, ['paper', 'orientation', 'margin_mm']);
  if (document.layout.paper !== 'A4' ||
      !['portrait', 'landscape'].includes(document.layout.orientation) ||
      !Number.isInteger(document.layout.margin_mm) ||
      document.layout.margin_mm < 10 || document.layout.margin_mm > 30) {
    throw new Error('Layout inválido');
  }
  if (!Array.isArray(allowedResourceIds) || allowedResourceIds.some(id =>
    typeof id !== 'string' || !RESOURCE_ID.test(id))) {
    throw new Error('Catálogo de recursos inválido');
  }
  const data = JSON.stringify(document);
  if (new TextEncoder().encode(data).length > MAX_BYTES) throw new Error('Documento acima do limite');
  const context = { classification: document.classification, allowed: new Set(allowedResourceIds),
    count: 0, protected: 0 };
  walk(document.content, context, 0, null);
  if (context.protected !== 1) throw new Error('Bloco patrimonial obrigatório e único');
  // Preserve exact JSON; never accept loose HTML or serialize via innerHTML.
  const result = JSON.parse(data);
  const node = createRichSchema().nodeFromJSON(result.content);
  node.check();
  return result;
}

/** Extra guard for the browser; validation on save is still mandatory. */
export function protectTransaction(transaction, state) {
  if (!transaction.docChanged) return true;
  const original = state.doc, next = transaction.doc;
  const blocks = doc => {
    const found = [];
    doc.descendants((node, pos) => {
      if (node.type.name === 'patrimonialBlock') found.push(node.toJSON());
    });
    return found;
  };
  const before = blocks(original), after = blocks(next);
  return before.length === 1 && after.length === 1 &&
    JSON.stringify(before) === JSON.stringify(after);
}
