/** T01: browser-only Tiptap/ProseMirror visual proof. Do not ship to production. */
import { Editor } from '@tiptap/core';
import { Plugin } from '@tiptap/pm/state';
import { history, undo, redo } from '@tiptap/pm/history';
import { createRichExtensions, normalizeRichDocument, protectTransaction } from './rich_schema.mjs';

const RESOURCE = 'a1c92077-aaaa-4f11-8b22-001122334455';
const resources = [RESOURCE];
const template = {
  schema_version: 2,
  classification: 'EMPRESTIMO',
  layout: { paper: 'A4', orientation: 'portrait', margin_mm: 20 },
  content: { type: 'doc', content: [
    { type: 'heading', attrs: { level: 2 },
      content: [{ type: 'text', text: 'Termo de empréstimo de equipamentos' }] },
    { type: 'paragraph', content: [
      { type: 'text', text: 'Responsável: ' },
      { type: 'variable', attrs: { key: 'responsavel.nome' } },
      { type: 'text', text: ' — data e local serão preenchidos na emissão.' },
    ] },
    { type: 'patrimonialBlock' },
    { type: 'table', content: [
      { type: 'tableRow', content: [
        { type: 'tableHeader', content: [{ type: 'paragraph',
          content: [{ type: 'text', text: 'Patrimônio' }] }] },
        { type: 'tableHeader', content: [{ type: 'paragraph',
          content: [{ type: 'text', text: 'Descrição sintética' }] }] },
      ] },
      { type: 'tableRow', content: [
        { type: 'tableCell', content: [{ type: 'paragraph',
          content: [{ type: 'text', text: 'GATI-TESTE-0001' }] }] },
        { type: 'tableCell', content: [{ type: 'paragraph',
          content: [{ type: 'text', text: 'Equipamento de demonstração' }] }] },
      ] },
    ] },
  ] },
};
const status = document.getElementById('editor-status');
const output = document.getElementById('export-json');
const report = (message, error = false) => {
  status.textContent = message;
  status.dataset.error = String(error);
};
const editor = new Editor({
  element: document.getElementById('editor'),
  extensions: createRichExtensions(),
  content: normalizeRichDocument(template, { allowedResourceIds: resources }).content,
  editorProps: {
    attributes: {
      'aria-label': 'Editor do corpo do termo sintético',
      'aria-multiline': 'true',
      'spellcheck': 'true',
    },
    handlePaste(view, event) {
      // Avoid injecting untrusted HTML into the editor. Text only, with the
      // ProseMirror schema as a second limit; server validation remains required.
      const text = event.clipboardData?.getData('text/plain');
      if (typeof text !== 'string') return false;
      event.preventDefault();
      if (text.length > 4096) {
        report('Colagem rejeitada: limite experimental de 4096 caracteres.', true);
        return true;
      }
      view.dispatch(view.state.tr.insertText(text));
      return true;
    },
    handleDrop(view, event) {
      event.preventDefault();
      report('Arrastar conteúdo não está disponível neste laboratório.', true);
      return true;
    },
  },
});
editor.registerPlugin(history());
editor.registerPlugin(new Plugin({
  filterTransaction(tr, state) {
    return protectTransaction(tr, state);
  },
}));
const buttons = document.querySelectorAll('#editor-toolbar button');
const refresh = () => {
  for (const button of buttons) {
    if (button.dataset.action === 'bold' || button.dataset.action === 'italic') {
      button.setAttribute('aria-pressed', String(editor.isActive(button.dataset.action)));
    }
  }
};
editor.on('selectionUpdate', refresh);
editor.on('update', () => {
  output.value = '';
  report('Documento modificado; valide novamente antes de exportar.');
  refresh();
});

/**
 * TableKit uses standard ProseMirror table default attrs (colspan/rowspan).
 * The GATI laboratory contract does not permit arbitrary persisted attrs:
 * omit only known structural defaults; reject non-default or unknown attrs.
 */
function canonical(node) {
  if (!node || typeof node !== 'object' || typeof node.type !== 'string') {
    throw new Error('Nó do editor inválido');
  }
  const out = { type: node.type };
  if (node.type === 'text') {
    out.text = node.text;
    if (node.marks?.length) out.marks = node.marks.map(mark => {
      if (mark.attrs && Object.keys(mark.attrs).length) throw new Error('Marca desconhecida');
      return { type: mark.type };
    });
    return out;
  }
  if (node.type === 'heading') out.attrs = { level: node.attrs?.level };
  if (node.type === 'variable') out.attrs = { key: node.attrs?.key };
  if (node.type === 'resourceImage') {
    out.attrs = {
      resourceId: node.attrs?.resourceId, alt: node.attrs?.alt,
      width: node.attrs?.width, height: node.attrs?.height,
    };
  }
  if (node.type === 'tableCell' || node.type === 'tableHeader') {
    const a = node.attrs || {};
    if (a.colspan !== 1 || a.rowspan !== 1 || a.colwidth != null ||
      (a.background !== undefined && a.background !== null) ||
      Object.keys(a).some(k => !['colspan', 'rowspan', 'colwidth', 'background'].includes(k))) {
      throw new Error('Célula contém atributos fora do contrato do GATI');
    }
  } else if (!['heading', 'variable', 'resourceImage'].includes(node.type) &&
      node.attrs && Object.values(node.attrs).some(x => x != null)) {
    throw new Error('Atributos fora do contrato');
  }
  if (node.content) out.content = node.content.map(canonical);
  return out;
}
function exportDocument() {
  const documentData = { ...template, content: canonical(editor.getJSON()) };
  return normalizeRichDocument(documentData, { allowedResourceIds: resources });
}
const actions = {
  bold: () => editor.chain().focus().toggleBold().run(),
  italic: () => editor.chain().focus().toggleItalic().run(),
  undo: () => undo(editor.state, editor.view.dispatch),
  redo: () => redo(editor.state, editor.view.dispatch),
  table: () => editor.chain().focus().insertTable({ rows: 2, cols: 2, withHeaderRow: true }).run(),
  image: () => editor.chain().focus().insertContent({
    type: 'resourceImage',
    attrs: { resourceId: RESOURCE, alt: 'Etiqueta patrimonial sintética', width: 240, height: 180 },
  }).run(),
  export: () => {
    const documentData = exportDocument();
    output.value = JSON.stringify(documentData, null, 2);
    report('JSON versionado validado em memória. Nenhum termo foi publicado.');
    return true;
  },
};
document.getElementById('editor-toolbar').addEventListener('click', event => {
  const action = event.target.closest('button[data-action]')?.dataset.action;
  if (!action || !actions[action]) return;
  try {
    if (!actions[action]()) report('Comando sem alteração no documento.', true);
    refresh();
  } catch (error) {
    output.value = '';
    report('Documento inválido: ' + (error instanceof Error ? error.message : 'erro'), true);
  }
});
window.__gatiVisual = { editor, exportDocument, RESOURCE };
window.__gatiVisualReady = true;
refresh();
report('Editor experimental preparado. Nenhum serviço externo foi acessado.');
