/* Interface de autoria T01: nunca persiste, injeta HTML ou acessa endpoints. */
(function () {
  'use strict';
  const model = window.GatiEditorModel;
  const blocks = document.getElementById('editable-blocks');
  const title = document.getElementById('document-title');
  const classification = document.getElementById('classification');
  const variableSelect = document.getElementById('variable');
  const status = document.getElementById('editor-status');
  let savedRange = null;

  // Título é um único nó textual no schema: não aceitar markup, quebras ou drop.
  title.addEventListener('paste', (event) => {
    event.preventDefault();
    const clipboard = event.clipboardData;
    const plain = clipboard ? clipboard.getData('text/plain') : '';
    const normalized = plain.replace(/\s*[\r\n]+\s*/g, ' ').slice(0, 4096);
    const selection = window.getSelection();
    if (!selection || !selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    if (!title.contains(range.commonAncestorContainer) && range.commonAncestorContainer !== title) {
      announce('Selecione o título antes de colar.', true);
      return;
    }
    range.deleteContents();
    const inserted = document.createTextNode(normalized);
    range.insertNode(inserted);
    range.setStartAfter(inserted);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    announce('Título colado como texto simples, sem quebra de linha.');
  });
  title.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      announce('O título deve ocupar uma única linha.');
    }
  });
  title.addEventListener('beforeinput', (event) => {
    if (event.inputType === 'insertParagraph' || event.inputType === 'insertLineBreak') {
      event.preventDefault();
    }
  });
  title.addEventListener('drop', (event) => {
    event.preventDefault();
    announce('Arrastar conteúdo para o título não está disponível.', true);
  });

  function announce(message, error = false) {
    status.textContent = message;
    status.classList.toggle('error', error);
  }

  function editableNode(node) {
    const el = node && (node.nodeType === Node.TEXT_NODE ? node.parentElement : node);
    return !!(el && el.closest && el.closest('#editable-blocks [contenteditable="true"]'));
  }

  document.addEventListener('selectionchange', () => {
    const selection = window.getSelection();
    if (selection && selection.rangeCount && editableNode(selection.anchorNode)) {
      savedRange = selection.getRangeAt(0).cloneRange();
    }
  });

  blocks.addEventListener('paste', (event) => {
    event.preventDefault();
    const plain = (event.clipboardData || window.clipboardData).getData('text/plain').slice(0, 4096);
    const selection = window.getSelection();
    if (!selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    if (!editableNode(range.startContainer)) return;
    range.deleteContents();
    const textNode = document.createTextNode(plain);
    range.insertNode(textNode);
    range.setStartAfter(textNode);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    announce('Conteúdo colado como texto simples.');
  });
  blocks.addEventListener('drop', (event) => {
    event.preventDefault();
    announce('Arrastar arquivos e HTML não está disponível neste experimento.', true);
  });

  const markTags = {bold: 'strong', italic: 'em', underline: 'u', strike: 's'};
  for (const button of document.querySelectorAll('[data-mark]')) {
    button.addEventListener('mousedown', (event) => event.preventDefault());
    button.addEventListener('click', () => {
      if (!savedRange || savedRange.collapsed || !editableNode(savedRange.commonAncestorContainer)) {
        announce('Selecione um trecho dentro do parágrafo para formatá-lo.', true);
        return;
      }
      try {
        savedRange.surroundContents(document.createElement(markTags[button.dataset.mark]));
        savedRange = null;
        announce('Formatação aplicada ao trecho selecionado.');
      } catch (_) {
        announce('Selecione somente um trecho sem cruzar elementos de formatação.', true);
      }
    });
  }

  function enableEditing(element, label) {
    element.className = 'editable';
    element.contentEditable = 'true';
    element.setAttribute('role', 'textbox');
    element.setAttribute('aria-label', label);
    element.setAttribute('aria-multiline', 'true');
    element.spellcheck = true;
    return element;
  }

  document.getElementById('add-paragraph').addEventListener('click', () => {
    const paragraph = enableEditing(document.createElement('p'), 'Parágrafo adicional');
    paragraph.textContent = 'Novo parágrafo';
    blocks.appendChild(paragraph);
    paragraph.focus();
    announce('Parágrafo adicionado.');
  });

  document.getElementById('add-list').addEventListener('click', () => {
    const list = document.createElement('ul');
    const item = enableEditing(document.createElement('li'), 'Item de lista');
    item.textContent = 'Novo item';
    list.appendChild(item);
    blocks.appendChild(list);
    item.focus();
    announce('Lista adicionada.');
  });

  function refreshVariables() {
    variableSelect.replaceChildren();
    for (const key of model.allowedVariables(classification.value)) {
      const option = document.createElement('option');
      option.value = key;
      option.textContent = key.replaceAll('_', ' ').replaceAll('.', ' · ');
      variableSelect.appendChild(option);
    }
    announce('Catálogo de campos atualizado.');
  }
  classification.addEventListener('change', refreshVariables);
  refreshVariables();

  document.getElementById('insert-variable').addEventListener('click', () => {
    if (!savedRange || !editableNode(savedRange.startContainer)) {
      announce('Posicione o cursor em um parágrafo antes de inserir o campo.', true);
      return;
    }
    try {
      const key = variableSelect.value;
      model.variable(key, classification.value);
      const token = document.createElement('span');
      token.className = 'variable';
      token.contentEditable = 'false';
      token.dataset.variable = key;
      token.textContent = '⟦' + key + '⟧';
      savedRange.deleteContents();
      savedRange.insertNode(token);
      savedRange.setStartAfter(token);
      savedRange.collapse(true);
      window.getSelection().removeAllRanges();
      window.getSelection().addRange(savedRange);
      savedRange = null;
      announce('Campo inserido: ' + key);
    } catch (error) {
      announce('Campo não inserido: ' + error.message, true);
    }
  });

  const tagMarks = {STRONG: 'bold', B: 'bold', EM: 'italic', I: 'italic',
    U: 'underline', S: 'strike', STRIKE: 'strike'};
  function tokens(node, active = []) {
    if (node.nodeType === Node.TEXT_NODE) {
      return node.textContent ? [model.text(node.textContent, active)] : [];
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return [];
    if (node.matches('span.variable[data-variable]')) {
      return [model.variable(node.dataset.variable, classification.value)];
    }
    const mark = tagMarks[node.tagName];
    if (mark) {
      if (active.includes(mark)) throw new Error('Marca duplicada');
      return [...node.childNodes].flatMap((child) => tokens(child, [...active, mark]));
    }
    if (node.tagName === 'BR') return [model.text('\n', active)];
    throw new Error('Elemento HTML não permitido: ' + node.tagName);
  }
  function inlineContents(element) {
    return [...element.childNodes].flatMap((child) => tokens(child));
  }

  document.getElementById('export-document').addEventListener('click', () => {
    try {
      const content = [];
      for (const block of blocks.children) {
        if (block.tagName === 'P') {
          content.push({type: 'paragraph', content: inlineContents(block)});
        } else if (block.tagName === 'UL') {
          const listItems = [];
          for (const child of block.children) {
            if (child.tagName !== 'LI') throw new Error('Item de lista inválido');
            listItems.push({
              type: 'listItem',
              content: [{type: 'paragraph', content: inlineContents(child)}],
            });
          }
          content.push({type: 'bulletList', content: listItems});
        } else {
          throw new Error('Bloco não permitido: ' + block.tagName);
        }
      }
      const result = model.createDocument({
        title: title.textContent.trim(), blocks: content, classification: classification.value,
      });
      document.getElementById('json-output').value = JSON.stringify(result, null, 2);
      announce('JSON exportado localmente. A validação final deve ocorrer no backend.');
    } catch (error) {
      document.getElementById('json-output').value = '';
      announce('Não foi possível exportar o documento: ' + error.message, true);
    }
  });
})();
