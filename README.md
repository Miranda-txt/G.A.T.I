# GATI — núcleo de gerenciamento de ativos

Aplicação funcional de inventário patrimonial, desenvolvida a partir dos cinco documentos em `docs/referencias`. Mantém o monólito modular Django, PostgreSQL, telas Django Templates com HTMX, API interna e regras de integridade da documentação.

**Escopo desta entrega:** ativos, pessoas, catálogos, manutenção, entregas e devoluções, termos, assinaturas, anexos, importação, painel, usuários e auditoria. Endpoint Windows, agentes, coleta técnica, drivers, comunicação máquina-servidor e infraestrutura Hostinger foram excluídos conforme o pedido. A API interna da aplicação foi mantida porque sustenta o núcleo patrimonial.

## Versão revisada para publicação

A revisão de 17/11/2026, as correções de segurança, os resultados dos testes e a referência de recuperação estão em [docs/PUBLICACAO_2026-11-17.md](docs/PUBLICACAO_2026-11-17.md). O [GitHub Actions](https://github.com/Miranda-txt/G.A.T.I/actions) executa testes com PostgreSQL temporário e verificações de segurança. Na execução inicial foram **67 testes aprovados e 2 ignorados** por exigirem ClamAV real; a execução local registrada na documentação teve 69 aprovados.

## Instalação em outro computador

Requisitos: Python 3.14, PostgreSQL 18 e ClamAV 1.4 LTS atualizado. Docker Desktop é uma alternativa para os dois serviços locais. Reserve memória para o banco e para o ClamAV.

No Windows, abra PowerShell na raiz do projeto:

```powershell
# Com Docker Desktop já instalado e em execução:
.\scripts\setup-local.ps1 -UseDocker

# Crie o administrador funcional (não é um superusuário Django):
.\backend\.venv\Scripts\python.exe backend/manage.py bootstrap_gati --admin

# Execute a aplicação:
.\INICIAR.ps1
```

Sem Docker, execute `python scripts/prepare_env.py`, configure `backend/.env` para seu PostgreSQL e ClamAV existentes e execute `scripts/setup-local.ps1` sem `-UseDocker`. O usuário do banco deve poder criar as tabelas e funções durante a instalação; a suíte de testes também precisa criar seu banco efêmero `test_gati`.

Em Linux/macOS:

```sh
python3.14 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.lock
backend/.venv/bin/python scripts/prepare_env.py
docker compose --env-file backend/.env -f infra/local/compose.yml up -d --wait
cd backend
.venv/bin/python manage.py migrate
.venv/bin/python manage.py bootstrap_gati --admin
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py runserver 127.0.0.1:8765
```

Os serviços Docker só expõem portas em `127.0.0.1`. A primeira atualização das definições do antivírus pode demorar. Nunca use `docker compose down -v` para apenas desligar: a opção `-v` remove os volumes de dados. Use `docker compose --env-file backend/.env -f infra/local/compose.yml stop`.

## Primeiro uso

1. Em **Cadastros auxiliares**, crie departamentos, categorias e localizações. Os status operacionais obrigatórios já são preparados pela instalação.
2. Cadastre as **Pessoas** e os **Ativos**. Patrimônio e Service Tag não se repetem entre ativos vigentes. A pessoa precisa ter documento com pelo menos quatro dígitos para confirmação de identidade.
3. Crie um **Modelo de termo** com texto adequado ao uso da organização. A tela mostra as variáveis permitidas. Operadores podem editar modelos existentes; criação e inativação ficam com Administradores.
4. Em **Entregas e devoluções**, preencha as sete etapas, confira a prévia e salve um rascunho ou emita o termo.
5. No termo emitido, inicie a assinatura presencial ou envie o convite por e-mail. **A responsabilidade e o status só mudam após todos os aceites obrigatórios.**
6. Na devolução, informe conferência, acessórios, divergências e avarias. A conclusão encerra o vínculo e coloca o ativo em estoque ou manutenção, respeitando os vínculos compartilhados restantes.

O modo presencial encerra a sessão administrativa antes de pedir os últimos quatro dígitos do documento. O aceite é eletrônico e registra evidências; não implementa certificação ICP-Brasil ou integração Gov.br. Na demonstração entregue, o documento de teste declara expressamente não ter validade jurídica.

## Importação e anexos

O botão **Importar** fica no Inventário e em Pessoas. Baixe o modelo da própria tela; os exemplos sintéticos também estão em `examples/`. Os nomes de departamento, categoria, localização e código de status precisam corresponder a cadastros existentes e ativos. CSV usa UTF-8, `;` ou `,`, com cabeçalho exato. XLSX aceita uma planilha sem fórmulas, macros ou vínculos externos.

Limites: **10 MiB e 5.000 linhas por importação**, **25 MiB por anexo** (PDF, PNG, JPEG). A prévia não cria registros; a confirmação revalida tudo e grava o lote inteiro ou nada. Importação somente cria: não atualiza, não reativa e não aceita identificadores de registros inativos. Documentos e identificadores com zeros iniciais devem ser células de texto no Excel.

ClamAV é obrigatório para importações e anexos. Se ficar indisponível, o arquivo é rejeitado sem ser disponibilizado. Os anexos ficam em armazenamento privado com nome UUID e hash, acessíveis somente por download autenticado. Nunca publique `backend/runtime` como conteúdo estático.

## E-mail e ambientes

Em `development` e `staging`, mensagens são gravadas em `backend/runtime/emails`, sem envio externo. Essa pasta pode conter links de uso único e redefinição de senha; trate-a como privada. Para testar o convite local, use a URL da parte `text/plain` da mensagem, incluindo o fragmento após `#`.

Produção exige `GATI_ENV=production`, chave aleatória exclusiva, hosts e origens explícitos, URL HTTPS e SMTP configurado em `backend/.env` ou no ambiente. O SMTP usa TLS implícito na porta 465. Credenciais de banco e e-mail não são distribuídas. Servidor WSGI de produção, domínio, proxy HTTPS, backups e implantação são responsabilidade da etapa de hospedagem excluída desta entrega.

## Validação e manutenção do código

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check --config pyproject.toml .
.\.venv\Scripts\python.exe -m ruff format --config pyproject.toml --check .
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pytest --cov=gati --cov-report=json:coverage.json
.\.venv\Scripts\python.exe ../scripts/check_coverage.py coverage.json
```

Para incluir os testes com ClamAV real, defina `GATI_TEST_CLAMAV=1`. Os demais testes usam respostas controladas do antivírus para verificar aprovação, infecção e falha de conexão. PostgreSQL real é usado em toda a suíte; SQLite não substitui os testes de transação e de gatilhos.

A configuração de GitHub Actions executa as verificações, sem publicar nem implantar nada. A revisão atual está em [docs/PUBLICACAO_2026-11-17.md](docs/PUBLICACAO_2026-11-17.md); o histórico da validação inicial está em [docs/VALIDACAO.md](docs/VALIDACAO.md).

Execute periodicamente `python manage.py cleanup_temporarios` para remover prévias expiradas e arquivos de quarentena abandonados. Não há exclusão física de termos, histórico ou auditoria pelas interfaces operacionais. Guarde backups consistentes de PostgreSQL **e** `runtime/private`; restaure primeiro em ambiente isolado e confira integridade e desidentificações antes de liberar o acesso.

## Organização

- `backend/config`: configurações separadas por ambiente, rotas e inicialização.
- `backend/gati/apps`: domínios patrimoniais, modelos, serviços transacionais, interfaces web e migrations.
- `backend/gati/common`: validações e utilitários compartilhados, catálogo de formulários, pesquisa e antivírus.
- `backend/gati/api`: API interna `/api/v1`, paginação, contratos e erros padronizados.
- `backend/templates` e `backend/static`: interface local; bibliotecas front-end vendorizadas.
- `backend/tests`: testes de domínio, integração, segurança, API e fluxos web.
- `specs/001-nucleo`: especificação e plano do recorte implementado.
- `docs`: rastreabilidade, decisões, operação e evidências.
- `infra/local`: apenas dependências locais; não provisiona Hostinger.

Consulte [ARQUITETURA.md](docs/ARQUITETURA.md), [RASTREABILIDADE.md](docs/RASTREABILIDADE.md), [OPERACAO.md](docs/OPERACAO.md) e [SEGURANCA_CI.md](docs/SEGURANCA_CI.md). O contrato OpenAPI real é gerado e validado pelo [workflow CI](https://github.com/Miranda-txt/G.A.T.I/actions/workflows/ci.yml) e disponibilizado como artefato **gati-openapi** (retenção de 30 dias); o placeholder `docs/openapi.yml` foi removido para não apresentar um esquema vazio como contrato público. A documentação original foi mantida para comparação. As solicitações atuais de escopo e autonomia prevalecem sobre instruções históricas de aguardar autorização a cada fase.
