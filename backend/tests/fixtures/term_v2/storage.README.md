# Spike privado S3/R2 — T01 (sem credenciais)

Este laboratório contém uma implementação experimental que aceita um cliente
S3 injetado. Os testes usam `FakeR2`, armazenado em memória, com comportamento
condicional simulado. **Não configura R2, não usa conta real, não comprova
política IAM, nem comprova bloqueio público de bucket.**

## Contratos validados pelo laboratório

- chave opaca UUID por emissão/artefato; PDF original/final distintos;
- escrita condicional `IfNoneMatch="*"`; sem substituição de bytes válidos;
- retry ambíguo com `write_id` estável e verificação de mesmo objeto;
- SHA-256 calculado dos bytes, sem confiança no ETag;
- consulta de metadados e leitura limitada, com fechamento do stream;
- negação anterior à leitura sem resultado exato `True` de permissão;
- corrupção de bytes/tamanho/MIME/hash/metadados detectada antes de retornar;
- erros sanitizados e falhas de armazenamento sem publicação falsa.

## Executar o teste

A partir de `backend/`, no ambiente de testes do projeto:

```sh
python -m pytest tests/test_term_v2_storage_spike.py -v
```

## Limitações e gates pendentes

O callback `permit` é somente uma simulação de decisão do servidor, **não um
mecanismo RBAC pronto para uso**. O `FakeR2.anonymous_download` nega por
construção: portanto o teste `public_access_denied` do plano continua
**não comprovado contra R2 real**. Antes de produção são exigidos revisão de
IAM/bucket, política de acesso anônimo, TLS, endpoint/região, credenciais em
secret manager, versão/licença/audit do SDK, validação de comportamento
condicional real, concorrência, erros 412/409, escopo por recurso, upload
com scanner/quarentena, reconciliação PostgreSQL ↔ objetos, backup/restore e
descarte conforme retenção e LGPD. Não migrar anexos genéricos existentes.

**Guardas do laboratório, não políticas aprovadas:** limite de 25 MiB,
somente PDFs e duas classes de artefato. A API/DTO não é contrato de T02/T04.
Não use na aplicação produtiva nem importe em serviços Django. Nenhuma
dependência definitiva precisa ser instalada para rodar este fake.
