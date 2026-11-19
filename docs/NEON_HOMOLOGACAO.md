# Neon PostgreSQL — homologacao do GATI

## Estado do provisionamento

- Projeto Neon: `gati-homologacao` (plano Free).
- Banco: `gati_homologacao`; branch: `main`.
- Regiao: AWS Sao Paulo (`aws-sa-east-1`).
- PostgreSQL: 18 (a versao observada na criacao foi 18.7).
- Ambiente: **homologacao vazia**, sem importacao de dados ou anexos do Windows.
- Credencial proprietaria: `gati_homologacao_owner` — somente migrations e manutencao controlada.
- Credencial de execucao: `gati_app` — leitura e escrita de dados, sem CREATE no schema publico.
- O banco foi criado, os papeis foram configurados e consultas simples foram executadas. **As migrations Django ainda nao foram aplicadas.**

## Conexao segura (Django e psycopg)

A configuracao do Django le `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST` e `PGPORT`.
O arquivo `backend/config/settings/database.py` adota:

- PostgreSQL local em loopback: `sslmode=disable`, preservando o Docker e os testes existentes.
- Host remoto (incluindo Neon): `sslmode=verify-full` **obrigatorio**.
- Autoridade certificadora: pacote Mozilla mantido por `certifi`, compativel com Windows e Linux.
- Sobrescrita opcional `PGSSLROOTCERT` somente por caminho de um bundle PEM confiavel ou `system`, quando suportado.
- `PGSSLMODE` pode ser definido como `verify-full`, mas nenhum valor mais fraco e aceito para host remoto.
- `CONN_HEALTH_CHECKS=True` para verificar conexoes persistentes ao reutiliza-las.

Exemplo de **nomes de variaveis**, sem credenciais:

```dotenv
PGDATABASE=gati_homologacao
PGUSER=gati_app
PGPASSWORD=<definir_exclusivamente_no_gerenciador_de_segredos>
PGHOST=<hostname_DNS_real_do_endpoint_Neon>
PGPORT=5432
PGSSLMODE=verify-full
```

Para migrations, use temporariamente `PGUSER=gati_homologacao_owner` e sua credencial exclusiva em um
ambiente de execucao protegido, conectado ao endpoint direto. Nunca disponibilize esse usuario
ao processo web. Para uso normal da aplicacao, utilize somente `gati_app`.

**Nao copie o exemplo acima como `.env` funcional.** Os valores entre `<...>` nao sao reais.
O hostname deve vir do painel Neon; nunca inclua o segredo da URL de conexao em chat,
issue, pull request, log, captura de tela ou commit.

## Limites da etapa e proximos controles

1. O repositório GitHub e o banco Neon sao ambientes distintos. Alterar as configuracoes no GitHub
   nao atualiza automaticamente o `.env` do Windows nem faz deploy.
2. Sincronize as mudancas na copia local por fluxo Git controlado antes de usar esse codigo.
3. Aplique migrations **somente** com o proprietario, apos revisar os objetos SQL irreversiveis
   e validar a estrategia de backup/rollback. Em particular, preserve `SEG-TERM-001`.
4. Apos as migrations, valide `django_migrations`, conte tabelas, triggers e funcoes, teste
   SQL proibido como `gati_app`, e execute regressao usando dados **sinteticos**.
5. A conexao ao servidor deve comprovar TLS por `pg_stat_ssl`, alem da configuracao
   `verify-full` no cliente. Uma consulta por ferramenta administrativa nao valida
   automaticamente o TLS usado pelo Django.
6. Arquivos privados, antivirus ClamAV, SMTP, DNS, proxy HTTPS, logs e backup consistente
   ainda precisam de infraestrutura separada. Neon armazena somente PostgreSQL.
7. Nao executar `seed_demo` ou `bootstrap_gati --admin` neste banco ate o ambiente
   e o acesso estarem homologados. Nao migrar dados reais do Windows nesta etapa.

## Referencias

- [PostgreSQL 18 — libpq, sslmode verify-full](https://www.postgresql.org/docs/18/libpq-connect.html)
- [Neon — verificacao de identidade TLS](https://neon.com/blog/avoid-mitm-attacks-with-psql-postgres-16)
- [Neon — acesso a bancos e roles](https://neon.com/docs/manage/database-access)
- [Certifi — bundle Mozilla](https://pypi.org/project/certifi/)
