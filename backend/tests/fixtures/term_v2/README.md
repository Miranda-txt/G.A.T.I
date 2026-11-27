# Fixtures e provas experimentais — T01

Dados sintéticos exclusivamente destinados a testes, sem CPF, e-mail, credenciais ou documentos reais.
As quatro combinações cobrem 1/100 ativos e 1/10 signatários, incluindo o máximo combinado.

O arquivo `test_term_v2_capabilities.py` inicia o gate de renderização em português e rejeição de recurso remoto.
O contrato de laboratório `renderer_spike.py: render_document(document) -> bytes` é provisório, não a API de produção.
A ausência do candidato é uma falha explícita de capacidade (não uma prova de segurança nem falha comportamental do candidato).
A prova deve evoluir para verificar saída real, paginação, integridade do texto, ausência de requisições ao canary de loopback,
rejeição de acesso arbitrário a arquivo e limites de recursos. O canary não prova sozinho isolamento completo de rede.
Editor, storage e worker possuem testes próprios na T01: editor com schema Python, modelo Node e Chromium; storage com fake em memória; worker com PostgreSQL 18 de testes. Estes testes NÃO comprovam Tiptap, R2 real, execução contínua do worker nem homologação produtiva.
Nenhuma biblioteca nova é instalada por este commit. ADR continua em avaliação.

## Executar candidato de laboratório

A partir de backend/, em ambiente de testes descartável Python 3.14:

    python -m pip install -r requirements.lock
    python -m pip install --only-binary=:all: --no-deps -r tests/fixtures/term_v2/requirements-spike.txt
    python -m pip check
    python -m pytest tests/test_term_v2_capabilities.py -v

Não instalar no ambiente produtivo. O candidato ReportLab gera texto literal A4 em memória; não é o renderizador definitivo. O SCA do CI audita também o arquivo experimental. Não usar documentos ou credenciais reais. A baseline mais recente registrada no gate T01 é o commit af04340 (285 testes aprovados, 2 ignorados). O resultado não libera T02, dependências definitivas, serviços de nuvem, merge ou deploy. Ver docs/adr/term-v2-t01-gate-review.md.

## Benchmark Linux e avaliação PDF/A

Em backend/, no ambiente descartável descrito acima, executar cada cenário separadamente:

    python tests/fixtures/term_v2/benchmark_spike.py --case maximo_combinado --output /tmp/gati-term-v2 --repetitions 10

Casos: minimo, ativos_maximos, signatarios_maximos, maximo_combinado. Um aquecimento antes das repetições; RSS em KiB do processo inteiro em Linux. Saídas PDF e JSON. CI usa veraPDF isolado, perfil 2b; preserva XML, stderr e digest da imagem no artefato gati-term-v2-renderer-evidence. Apenas arquivos sintéticos. Não conformidade não permite rotular PDF como PDF/A; falha operacional deve ser corrigida. Medições não são SLA de produção.

## Status atualizado do laboratório — 26/11/2026

- Renderer ReportLab 5.1.2: 40 medições nos 4 cenários, determinismo SHA-256 e paginação de PDF simples; 4/4 PDFs não conformes PDF/A-2b no veraPDF. Dados sintéticos, sem SLA produtivo.
- Editor: 25 testes Python + 4 testes Node e E2E Chromium; teste de colagem, teclado, reflow e schema restrito; sem editor rico definitivo.
- Storage: 26 testes de capacidade com fake S3/R2; sem bucket/IAM/R2 real.
- Worker: 10 testes PostgreSQL/lease/deduplicação; sem scheduler ou runner contínuo.
- [Gate e matriz de decisões](../../../../docs/adr/term-v2-t01-gate-review.md): os testes experimentais não autorizam T02 nem uso de dados reais.

## Corpus adversarial JSON v2 — 27/11/2026

Em backend/, somente no ambiente de testes Linux com dependências experimentais instaladas:

    python -m pytest tests/test_term_v2_json_pdf_adversarial.py -v
    python tests/fixtures/term_v2/json_pdf_adversarial.py --output /tmp/gati-adversarial-novo

Usar diretório vazio. 16 cenários por motor/orientação, 64 jobs em pares concorrentes, reutilizando o envelope de capacidade existente. 28 casos válidos esperados e 36 rejeições explícitas (sem PDF). Limites de laboratório: 4096 caracteres por nó, 100 linhas, 12 células, 1000 nós e 131072 bytes de JSON canônico. Casos adicionais: imagens repetidas, expansão de variável, tabela irregular, variável ausente, recurso não autorizado e bloco protegido adulterado. O subprocesso verifica integridade textual e ordem (desconsiderando espaços de extração e rodapé experimental), 100 ativos, 10 signatários, operações de imagem, páginas A4, hash e ausência de mutação. O processo pai verifica relatório, hash e limites antes de publicar os bytes sintéticos. Sem interpretação como PDF/A, sem prova de geometria visual, sandbox completo ou política produtiva. O CI guarda as evidências no artefato gati-term-v2-renderer-evidence/adversarial. Consultar o parecer T01 para resultados e pendências.
