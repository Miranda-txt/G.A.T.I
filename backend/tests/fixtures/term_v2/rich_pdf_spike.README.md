# PDF rico experimental — T01

Dois motores isolados (ReportLab e WeasyPrint), sem alteração do renderer legado
ou dependências/lock de produção. Entrada estruturada e validada com 100 ativos,
10 signatários, texto pt-BR, imagem PNG sintética explicitamente aprovada e
tabela longa em A4. Nenhum HTML do editor é repassado ao WeasyPrint: toda
marcação HTML/CSS é gerada em código fixo e os textos são escapados.
O fetcher customizado rejeita rede, arquivo e qualquer recurso fora da allowlist.

A partir de `backend/` (ambiente descartável):

```sh
python -m pytest tests/test_term_v2_rich_pdf_spike.py tests/test_term_v2_rich_pdf_benchmark.py -v
python tests/fixtures/term_v2/rich_pdf_benchmark.py --engine reportlab --output /tmp/term-v2-rich --repetitions 5
python tests/fixtures/term_v2/rich_pdf_benchmark.py --engine weasyprint --output /tmp/term-v2-rich --repetitions 5
```

O runner CI instala WeasyPrint 70.0 somente no ambiente de teste, mede latência,
CPU, RSS, bytes e paginação em processos separados, publica PDFs/JSON e usa
veraPDF independente para distinguir conformidade de falha operacional.
Resultados de runner compartilhado não são SLA de produção. Não assumir PDF/A
sem `isCompliant=true` e inspeção de bytes específicos. Versionar dependências
definitivas somente após decisão de arquitetura, segurança/licenças e aceite.
