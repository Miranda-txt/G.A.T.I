"""Inicializacao controlada do schema GATI no Neon via GitHub Actions.

O processo nunca imprime a URL de conexao nem a senha PostgreSQL.
Use somente no workflow manual de homologacao; nao substitui o servidor web.
"""

import os
import secrets
import sys
from urllib.parse import unquote, urlsplit

EXPECTED_DATABASE = "gati_homologacao"
EXPECTED_USER = "gati_homologacao_owner"
EXPECTED_HOST = "ep-dawn-queen-b6r6y6dr.c-2.sa-east-1.aws.neon.tech"
APP_USER = "gati_app"
MODES = frozenset({"preflight", "apply", "verify"})


def parse_migration_url(value: str) -> dict[str, str]:
    """Rejeita destinos inesperados antes de abrir qualquer conexao."""
    uri = urlsplit(value.strip())
    if uri.scheme not in {"postgresql", "postgres"} or uri.fragment:
        raise ValueError("A URL deve ser PostgreSQL, sem fragmentos.")
    if uri.hostname != EXPECTED_HOST:
        raise ValueError("Endpoint diferente do Neon de homologacao do GATI.")
    if uri.port not in {None, 5432}:
        raise ValueError("A porta PostgreSQL esperada e 5432.")
    if unquote(uri.path) != f"/{EXPECTED_DATABASE}":
        raise ValueError("Banco diferente de gati_homologacao.")
    if unquote(uri.username or "") != EXPECTED_USER:
        raise ValueError("O workflow exige exclusivamente o proprietario de migrations.")

    password = unquote(uri.password or "")
    if not password:
        raise ValueError("A URL de conexao nao possui senha.")

    # Parametros da URL sao ignorados: a conexao Django forca verify-full.
    return {
        "PGDATABASE": EXPECTED_DATABASE,
        "PGUSER": EXPECTED_USER,
        "PGPASSWORD": password,
        "PGHOST": EXPECTED_HOST,
        "PGPORT": "5432",
        "PGSSLMODE": "verify-full",
    }


def _check_client_tls(connection) -> None:
    """Verifica a sessao TLS do libpq, nao o canal interno do proxy Neon."""
    options = connection.settings_dict.get("OPTIONS", {})
    if options.get("sslmode") != "verify-full" or not options.get("sslrootcert"):
        raise RuntimeError("Conexao remota exige TLS verify-full e CA confiavel.")

    connection.ensure_connection()
    native_connection = connection.connection
    if not getattr(getattr(native_connection, "pgconn", None), "ssl_in_use", False):
        raise RuntimeError("Conexao PostgreSQL do cliente nao usa TLS.")


def _check_preflight(connection) -> None:
    """Confere TLS do cliente, identidade, privilegio DDL e banco inicial vazio."""
    _check_client_tls(connection)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT current_database(), current_user,
                   has_schema_privilege(current_user, 'public', 'CREATE'),
                   (SELECT count(*) FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE')
            """
        )
        db_name, db_user, can_create, table_count = cursor.fetchone()
        if (db_name, db_user) != (EXPECTED_DATABASE, EXPECTED_USER):
            raise RuntimeError("Identidade do banco ou usuario divergente.")
        if not can_create:
            raise RuntimeError("O usuario de migrations nao pode criar objetos no schema public.")
        if table_count:
            raise RuntimeError("O banco nao esta vazio; a inicializacao nao deve ser repetida.")
        cursor.execute(
            """
            SELECT rolcanlogin, rolcreatedb, rolcreaterole, rolsuper, rolbypassrls
            FROM pg_roles WHERE rolname = %s
            """,
            [APP_USER],
        )
        role = cursor.fetchone()
        if role is None or not role[0] or any(role[1:]):
            raise RuntimeError("Permissoes do usuario da aplicacao divergentes.")
        cursor.execute(
            "SELECT has_schema_privilege(%s, 'public', 'CREATE')",
            [APP_USER],
        )
        if cursor.fetchone()[0]:
            raise RuntimeError("O usuario da aplicacao possui CREATE no schema publico.")
    print("Preflight aprovado: destino, TLS, papeis e banco vazio verificados.")


def _check_applied(connection) -> None:
    """Verifica integridade estrutural apos migrations, sem inserir dados reais."""
    _check_client_tls(connection)
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), current_user")
        name, user = cursor.fetchone()
        if (name, user) != (EXPECTED_DATABASE, EXPECTED_USER):
            raise RuntimeError("Identidade do banco ou usuario divergente.")
        cursor.execute("SELECT count(*) FROM django_migrations")
        count = cursor.fetchone()[0]
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM django_migrations
                WHERE app = 'termos' AND name = '0004_seg_term_001'
            )
            """
        )
        if not cursor.fetchone()[0]:
            raise RuntimeError("A migration SEG-TERM-001 nao foi registrada.")
        cursor.execute(
            """
            SELECT t.tgenabled, t.tgtype
            FROM pg_trigger AS t
            WHERE t.tgrelid = 'public.termos_termo'::regclass
              AND t.tgname = 'termo_congelado' AND NOT t.tgisinternal
            """
        )
        trigger = cursor.fetchone()
        if trigger is None or trigger[0] != "O" or trigger[1] & 30 != 30:
            raise RuntimeError("Trigger de protecao do termo ausente ou incompleto.")
        cursor.execute("SELECT pg_get_functiondef('public.gati_term_guard()'::regprocedure)")
        body = cursor.fetchone()[0]
        if "Signatario obrigatorio" not in body or "Faltam assinaturas validas" not in body:
            raise RuntimeError("Funcao de protecao do termo esta divergente.")
        cursor.execute(
            """
            SELECT has_schema_privilege(%s, 'public', 'CREATE'),
                   has_table_privilege(%s, 'public.termos_termo', 'SELECT'),
                   has_table_privilege(%s, 'public.termos_termo', 'INSERT'),
                   has_table_privilege(%s, 'public.termos_termo', 'UPDATE'),
                   has_table_privilege(%s, 'public.termos_termo', 'DELETE')
            """,
            [APP_USER] * 5,
        )
        grants = cursor.fetchone()
        if grants[0] or not all(grants[1:]):
            raise RuntimeError("Privilegios de leitura/escrita do usuario GATI divergentes.")
        cursor.execute("SELECT count(*) FROM auth_permission")
        if cursor.fetchone()[0] < 1:
            raise RuntimeError("Permissoes padrao do Django nao foram inicializadas.")
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    if executor.migration_plan(executor.loader.graph.leaf_nodes()):
        raise RuntimeError("Ainda existem migrations pendentes no banco remoto.")
    print(f"Validacao aprovada: {count} migrations registradas, SEG-TERM-001 e privilegios corretos.")


def main(mode: str) -> None:
    if mode not in MODES:
        raise ValueError("Modo invalido. Use preflight, apply ou verify.")
    source = os.environ.get("GATI_NEON_MIGRATION_URL", "")
    if not source:
        raise ValueError("Configure o segredo GitHub GATI_NEON_MIGRATION_URL.")
    config = parse_migration_url(source)

    # Nao ler .env local; nao permitir rebaixamento de SSL por variaveis herdadas.
    os.environ.update(config)
    os.environ.pop("PGSSLROOTCERT", None)
    os.environ["GATI_ENV"] = "staging"
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.staging"
    os.environ["GATI_SECRET_KEY"] = secrets.token_urlsafe(64)
    os.environ["GATI_ALLOWED_HOSTS"] = "localhost"
    os.environ["GATI_CSRF_ORIGINS"] = "https://localhost"
    os.environ["GATI_PUBLIC_URL"] = "https://localhost"

    import django
    from django.core.management import call_command
    from django.db import connection

    django.setup()
    if mode == "verify":
        _check_applied(connection)
        return

    _check_preflight(connection)
    call_command("migrate", plan=True, verbosity=1)
    if mode == "preflight":
        print("Apenas preflight: nenhuma migration foi aplicada.")
        return

    call_command("migrate", interactive=False, verbosity=1)
    _check_applied(connection)
    print("Inicializacao de homologacao concluida; nenhum usuario ou dado real foi criado.")


if __name__ == "__main__":
    try:
        main(sys.argv[1] if len(sys.argv) == 2 else "")
    except Exception as exc:
        # Mesmo em falha de conexao nunca imprimir senha/URL em logs publicos de Actions.
        message = str(exc)
        for secret_value in (
            os.environ.get("GATI_NEON_MIGRATION_URL", ""),
            os.environ.get("PGPASSWORD", ""),
        ):
            if secret_value:
                message = message.replace(secret_value, "[REDACTED]")
        print(f"Falha de inicializacao ({type(exc).__name__}): {message[:800]}", file=sys.stderr)
        raise SystemExit(1) from None
