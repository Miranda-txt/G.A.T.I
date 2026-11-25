# Validação da entrega — 27/10/2026

Ambiente local Windows, Python 3.14.7, Django 5.2.18, PostgreSQL 18.6 e ClamAV 1.4.6 LTS com bases oficiais atualizadas por FreshClam. Todos os dados de teste são sintéticos.

| Verificação | Resultado |
|---|---|
| Suíte completa com ClamAV real habilitado | 67 testes aprovados; zero falhas, erros ou ignorados; 37.26 s |
| Cobertura Python de linhas | 87.97% — mínimo 80% |
| Cobertura de ramificações | 72.58% — mínimo 70% |
| Ruff: análise estática e formatação | Aprovadas |
| Django system check | Sem problemas |
| Django check --deploy com configuração HTTPS de teste | Sem problemas |
| Migrations pendentes | Nenhuma; inicialização aplicada em PostgreSQL 18 real |
| OpenAPI 3.1 | Gerado e validado sem avisos |
| Iniciador local preparado | Verificação de configuração, PostgreSQL e ClamAV aprovada |

A cobertura inclui `gati`, exceto migrations, comandos administrativos e declaração de apps, conforme `pyproject.toml`. Integridade das migrations é verificada nos testes PostgreSQL, inclusive tentativas de alteração por SQL. O comando de expiração recebeu uma checagem adicional após o ajuste de concorrência: teste específico aprovado, preservando exclusão de arquivos somente após commit. Os gatilhos não protegem contra um administrador de banco capaz de desativá-los; produção requer separação de privilégios.

## Fluxos validados

- Cadastro e edição patrimonial, versões concorrentes, duplicidade, inativação e histórico aditivo.
- Matriz de acesso, campos permitidos da API, mascaramento, CSRF, sessões, bloqueio de login e limitação de recuperação de senha.
- Entrega, devolução, avaria, testemunhas e responsabilidades compartilhadas.
- Termos congelados, edição de rascunho, cancelamento, substituição sem repetição de movimento e evidências imutáveis.
- Convites consumidos/expirados, reemissão, cinco falhas de identidade e aceite idempotente. Duas conexões PostgreSQL submeteram o mesmo aceite simultaneamente sem duplicar vínculo ou histórico.
- Importação CSV/XLSX, fórmulas, macros, duplicidade, referências e conflito após prévia, com rollback integral.
- Upload privado, MIME/extensão, integridade de download, falhas do scanner e respostas de infecção controladas.
- **ClamAV real:** PNG sintético anexado, baixado e comparado byte a byte; CSV sintético importado com prévia e confirmação. O teste de resposta de infecção usa simulação do protocolo, sem introduzir malware no computador.

## Verificação no navegador

Chrome local: login, pesquisa HTMX, inventário, wizard completo de sete etapas, termo emitido, início presencial com logout, confirmação dos quatro últimos dígitos fictícios, aceite, retorno administrativo e conferência do ativo Em Uso com responsabilidade aberta e histórico. Capturas mostram somente dados de demonstração.

Painel conferido em desktop e viewport de tablet 768 × 1024, sem transbordamento horizontal do documento; menu abre e fecha por Escape. O tamanho normal da janela foi restaurado. A revisão corrigiu a política de referência que inicialmente impedia formulários, o alvo HTMX da pesquisa e a navegação por teclado do menu.

![Painel local](evidencias/painel.png)

![Aceite fictício concluído](evidencias/assinatura.png)

## Limites da evidência

Não houve publicação, provisionamento Hostinger, execução de GitHub Actions, Docker nesta máquina, teste SMTP contra serviço externo, auditoria completa ASVS/ZAP, teste de carga representativo do RNF-009 ou recuperação de backup produtivo. São atividades de homologação/infraestrutura identificadas em `OPERACAO.md`. O teste local comprova os fluxos e invariantes exercitados, não disponibilidade ou capacidade de uma infraestrutura ainda não configurada.

O código está acompanhado do esquema OpenAPI e de evidência estruturada em `evidencias/validacao.json` e `evidencias/testes.xml`. O pacote portátil exclui `.env`, banco, anexos, e-mails, credenciais de demonstração, ambientes Python e caches.

## Atualização de publicação — 17/11/2026

Este documento é a evidência **histórica de 27/10/2026** (67 testes). A revisão local publicada registra 69 aprovados e o primeiro CI da versão revisada, [execução 44210242819](https://github.com/Miranda-txt/G.A.T.I/actions/runs/44210242819), registrou **67 aprovados, 2 ignorados (ClamAV real) e nenhuma falha**. A cobertura mínima do projeto também foi aprovada no CI.

O OpenAPI completo é **gerado durante o CI** com `manage.py spectacular --validate --fail-on-warn` e publicado como artefato `gati-openapi` no [workflow](https://github.com/Miranda-txt/G.A.T.I/actions/workflows/ci.yml). O arquivo versionado anterior continha apenas `paths: {}` e foi removido para evitar confusão. Os artefatos expiram após 30 dias.

O hostname da evidência XML histórica foi mascarado por privacidade na versão corrente do repositório; versões anteriores podem continuar acessíveis no histórico Git. Essas verificações não comprovam SMTP real, disponibilidade em produção ou segurança integral.

## Atualização de validação da interface — 25/11/2026

As seções anteriores preservam evidências históricas de 27/10 e 17/11. Não são indicadores atuais de cobertura, ClamAV real ou homologação em nuvem. O DU05 ainda não está publicado.

| Referência | Aprovados | Falhas | Ignorados | Linhas | Ramificações |
|---|---:|---:|---:|---:|---:|
| [DU04 publicado: 6cde964](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45627071876) | 176 | 0 | 2 | 88,18% | 73,34% |
| [DU05.2: 9d23457](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45648174135) | 182 | 0 | 2 | 88,27% | 73,64% |
| [DU05.3: b13624c, pós-FF](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45657824869) | 183 | 0 | 2 | 88,27% | 73,64% |
| [DU05.4: d7d8347, rodada 2](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45660465571/attempts/2) | 184 | 0 | 2 | 88,64% | 74,40% |
| [DU05.5: 5be66dd, rodada 1](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45669016137/attempts/1) | 185 | 0 | 2 | 88,77% | 74,40% |
| [DU05.5: 5be66dd, rodada 2](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45669016137/attempts/2) | 185 | 0 | 2 | 88,77% | 74,40% |
| [DU05.6 baseline documental: b1d6d59](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45677419470) | 185 | 0 | 2 | 88,77% | 74,40% |

O último CI da tabela coletou 187 testes em 63,29 s; Ruff, Django, migrations, collectstatic, OpenAPI, cobertura (mínimos 80%/70%) e Docker passaram. [Segurança de b1d6d59](https://github.com/Miranda-txt/G.A.T.I/actions/runs/45677419565): SAST, SCA e segredos aprovados. As três rodadas GREEN mais recentes têm conteúdo funcional idêntico. Os dois ignorados exigem ClamAV real em loopback; não representam execução do antivírus externo. A suíte utiliza PostgreSQL temporário no CI.

Matrizes CDP: 11 larguras do dashboard, 9 combinações dos componentes compartilhados, 30 combinações tipográficas, 36 estados de filtros (submatriz do Inventário), 114 combinações adicionais de 19 cenários/6 larguras e 228 estados tipográficos; mais 16 combinações de 8 cenários/2 larguras de contraste. São iterações internas de cinco testes CDP, não testes Pytest independentes nem necessariamente páginas distintas. Os RED de DU05.4 e DU05.5 detectaram 104 e 28 violações respectivamente; os testes correspondentes passaram sem redução de limiares. HTML real é renderizado pelo Django com dados sintéticos, assets locais e CDP offline; isso não equivale a navegação HTTP ponta a ponta nem homologação WCAG integral.

Riscos residuais, requisitos de aceite manual, links de evidência e revisão acumulada: [DU05.6](design-system/DU-UX-DASH-05.6_REVISAO_TECNICA_FINAL.md). O CI desta atualização documental deve ser confirmado antes do encerramento de DU05.6. Os limites históricos de infraestrutura, segurança integral, carga e recuperação de backup produtivo não foram revalidados por este incremento.
