# Revisão para publicação — 17/11/2026

Origem: versão local do GATI. Destino: `Miranda-txt/G.A.T.I`, branch `main`, conta `Miranda-Principal` (`Miranda-txt`). A revisão foi feita em uma cópia isolada: os arquivos e o ambiente Python da aplicação local não foram alterados.

## Segurança e ajustes

- `.env`, cópias de configuração, `runtime` (inclusive e-mails, tokens e anexos), ambiente virtual e caches foram excluídos.
- A varredura dos arquivos selecionados, do texto do PDF e do conteúdo do ZIP não encontrou correspondências com as credenciais locais nem os padrões de chaves privadas e tokens pesquisados. `.env.example` contém somente campos vazios e valores de exemplo.
- Django REST Framework atualizado de 3.17.2 para 3.18.2 e pypdf de 6.21.3 para 6.21.4. As seis vulnerabilidades identificadas pela auditoria inicial deixaram de ser reportadas após essas atualizações. Os limites em `requirements.in` acompanham as versões corrigidas do lock.
- Auditoria final com pip-audit 2.10.1: 38 dependências verificadas, nenhuma vulnerabilidade conhecida reportada. A consulta usou o lock completo com versões fixadas; não foi usado `--fix` automático.
- Bandit 1.9.4: nenhum achado de severidade média ou alta. Dois avisos baixos B105 foram revisados: atribuições de string vazia que apagam hashes de tokens consumidos; não são senhas embutidas.
- Permissões de acesso, CSRF, configuração HTTPS, upload privado, ClamAV, tokens de assinatura e SQL parametrizado foram revisados nos pontos relevantes. Não equivale a auditoria de segurança exaustiva.
- Uma linha em branco excedente na migration `0004_seg_term_001.py` foi removida para satisfazer Ruff. O SQL não mudou. O hash esperado no script de promoção e a cópia da migration dentro do ZIP foram sincronizados; `.gitattributes` preserva LF nessa migration para permitir a conferência do hash também em checkouts Windows.
- `.gitignore` ampliado para arquivos de chave, backups e resultados locais. README ajustado para remover atalhos de uma entrega anterior que não existem neste repositório. Manifesto SHA-256 regenerado para os arquivos publicados.

Referências dos mantenedores: [DRF — correção 3.18.2](https://github.com/encode/django-rest-framework/security/advisories/GHSA-33wh-fxxf-88vv) e [pypdf — correção 6.21.4](https://github.com/py-pdf/pypdf/releases/tag/6.21.4).

## Validação executada antes do envio

Ambiente: Windows, Python 3.14.7, PostgreSQL 18.6 temporário em loopback, dependências do lock corrigido instaladas em ambiente Python separado. A conta do banco da aplicação não recebeu novas permissões. A instância PostgreSQL criada para testes foi encerrada ao final.

| Verificação | Resultado |
|---|---|
| Sintaxe Python | Aprovada |
| Consistência de dependências (`pip check`) | Aprovada |
| Ruff e formatação de 151 arquivos Python do backend | Aprovadas |
| Django `check` | Sem problemas |
| Django `check --deploy --fail-level WARNING` com configuração HTTPS sintética | Sem problemas |
| `makemigrations --check --dry-run` | Nenhuma mudança pendente |
| Aplicação das migrations em PostgreSQL novo | Aprovada, incluindo `termos.0004_seg_term_001` |
| `collectstatic` | Aprovado |
| OpenAPI com `--validate --fail-on-warn` | Aprovado |
| Suíte pytest com `GATI_TEST_CLAMAV=1` | 69 aprovados, 0 falhas, 0 ignorados; 23,77 s |
| Cobertura de linhas | 87,97% (mínimo 80%) |
| Cobertura de ramificações | 72,58% (mínimo 70%) |
| Auditoria final das dependências | 0 vulnerabilidades conhecidas reportadas |

Os testes usam dados sintéticos e incluem os dois testes de regressão SEG-TERM-001, testes de integridade, concorrência, permissões, API, importações e dois testes com o ClamAV local real. Os relatórios de 27/10/2026 em `docs/evidencias` são evidências históricas, não os resultados desta execução. A execução no GitHub Actions ocorre após o envio e deve ser consultada na aba Actions.

## Migrations e recuperação

A migration `termos.0004_seg_term_001` é intencionalmente irreversível e reforça as transições de estado e a exigência de assinaturas. Ela foi validada somente em banco temporário. A publicação no GitHub não executa migrations no banco usado pela aplicação.

O commit anterior à substituição é `4340fdcfaad786c9f129cac077f9eefa8f00747f`. A referência [backup/pre-publicacao-2026-11-17-4340fdc](https://github.com/Miranda-txt/G.A.T.I/tree/backup/pre-publicacao-2026-11-17-4340fdc) preserva esse estado. A nova versão deve ser um commit descendente desse commit, substituindo a árvore de arquivos, sem reescrever histórico ou usar force push. Para recuperar o código, use essa referência ou reverta o commit de publicação em um novo commit.

A referência Git recupera código; recuperação de banco exige backup próprio. Não houve implantação de servidor, envio de e-mails, alteração de dados reais, restauração de banco produtivo, teste de carga ou nova validação visual no navegador. As capturas históricas incluídas foram inspecionadas e mostram somente demonstração.

## Verificação pós-publicação e endurecimento do CI — 17/11/2026

O [workflow CI da publicação](https://github.com/Miranda-txt/G.A.T.I/actions/runs/44210242819) concluiu com sucesso no GitHub: **67 testes aprovados, 2 ignorados (exigem ClamAV real) e 0 falhas**, incluindo regressão SEG-TERM-001. Esses números se referem ao runner GitHub e não substituem os 69 testes locais documentados acima.

O CI agora exporta o **OpenAPI gerado** como artefato `gati-openapi`, com retenção de 30 dias, em vez de publicar o placeholder vazio `docs/openapi.yml`. Um workflow independente, [Segurança](https://github.com/Miranda-txt/G.A.T.I/actions/workflows/security.yml), verifica dependências com `pip-audit`, código Python com Bandit e segredos com Gitleaks v3; seu resultado deve ser consultado separadamente antes de promover a aplicação. Nenhum destes workflows executa deploy, migrations em bancos remotos ou publicação de dados.

O ZIP redundante da correção foi retirado da árvore atual (os scripts permanecem individualmente disponíveis); o hostname do XML histórico foi mascarado. Por se tratar de repositório público, **a remoção atual não elimina cópias do histórico**. Para incidente real, rotacione credenciais expostas e trate o histórico de forma controlada. Veja `docs/SEGURANCA_CI.md`.
