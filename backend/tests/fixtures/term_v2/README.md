# Fixtures e provas experimentais — T01

Dados sintéticos exclusivamente destinados a testes, sem CPF, e-mail, credenciais ou documentos reais.
As quatro combinações cobrem 1/100 ativos e 1/10 signatários, incluindo o máximo combinado.

O arquivo `test_term_v2_capabilities.py` inicia o gate de renderização em português e rejeição de recurso remoto.
O contrato de laboratório `renderer_spike.py: render_document(document) -> bytes` é provisório, não a API de produção.
A ausência do candidato é uma falha explícita de capacidade (não uma prova de segurança nem falha comportamental do candidato).
A prova deve evoluir para verificar saída real, paginação, integridade do texto, ausência de requisições ao canary de loopback,
rejeição de acesso arbitrário a arquivo e limites de recursos. O canary não prova sozinho isolamento completo de rede.
Editor, storage e worker ainda exigem seus testes próprios; não simular aprovação ou usar R2/Neon reais.
Nenhuma biblioteca nova é instalada por este commit. ADR continua em avaliação.

## Executar candidato de laboratório

A partir de backend/, em ambiente de testes descartável Python 3.14:

    python -m pip install -r requirements.lock
    python -m pip install --only-binary=:all: --no-deps -r tests/fixtures/term_v2/requirements-spike.txt
    python -m pip check
    python -m pytest tests/test_term_v2_capabilities.py -v

Não instalar no ambiente produtivo. O candidato ReportLab gera texto literal A4 em memória; não é o renderizador definitivo. O SCA do CI audita também o arquivo experimental. Não usar documentos ou credenciais reais. Resultados GREEN e medições ainda pendentes.
