#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply SEG-TERM-001 migration ONLY to the existing isolated GATI database.

This program NEVER connects to or migrates the main `gati` database. It uses
existing Django credentials, does not show secrets, and aborts on unknown setup.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys


MAIN_DB = "gati"
TEST_DB = "gati_segterm_teste"
MIGRATION_NAME = "0004_seg_term_001"


def run() -> int:
    root = Path(__file__).resolve().parent
    backend = root / "backend"
    migration_file = (
        backend / "gati" / "apps" / "termos" / "migrations" / f"{MIGRATION_NAME}.py"
    )
    if not (backend / "manage.py").is_file() or not migration_file.is_file():
        print("[BLOQUEADO] Posicione este script e a migration nos caminhos descritos no README.")
        return 2

    # Do not read or display credentials. Validate expected source database.
    from dotenv import dotenv_values
    declared_name = dotenv_values(backend / ".env").get("PGDATABASE", MAIN_DB)
    if declared_name != MAIN_DB:
        print("[BLOQUEADO] backend/.env nao aponta para o banco principal esperado.")
        return 2

    # PostgreSQL database name is chosen BEFORE Django settings are loaded.
    # Any stored PGDATABASE=... variable must not override this isolation.
    os.environ["PGDATABASE"] = TEST_DB
    os.environ["GATI_ENV"] = "development"
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.development"
    sys.path.insert(0, str(backend))
    os.chdir(backend)

    from config.env import configure
    configure()
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from django.core.management import call_command

    cfg = settings.DATABASES["default"]
    if (cfg.get("ENGINE") != "django.db.backends.postgresql"
        or cfg.get("NAME") != TEST_DB
        or cfg.get("USER") != "gati"
        or str(cfg.get("HOST", "127.0.0.1")).lower() not in ("127.0.0.1", "localhost", "::1")
    ):
        print("[BLOQUEADO] Conexao Django nao corresponde ao banco isolado autorizado.")
        return 2

    with connection.cursor() as cur:
        cur.execute("SELECT current_database(), current_user")
        database, role = cur.fetchone()
        if (database, role) != (TEST_DB, "gati"):
            print("[BLOQUEADO] Banco ou usuario diferente do esperado.")
            return 2
        cur.execute("SELECT COUNT(*) FROM public.termos_termo WHERE estado = 'ASSINADO'")
        count = cur.fetchone()[0]
        if count < 1:
            print("[BLOQUEADO] Base isolada sem o termo assinado restaurado.")
            return 2
        cur.execute("""
            SELECT COUNT(*) FROM pg_trigger
            WHERE tgrelid = 'public.termos_termo'::regclass
              AND tgname = 'termo_congelado' AND tgenabled IN ('O', 'A')
        """)
        if cur.fetchone()[0] != 1:
            print("[BLOQUEADO] Trigger original nao esta habilitado na base isolada.")
            return 2

    # Never run a migration plan that includes unexpected/other app migrations.
    executor = MigrationExecutor(connection)
    target = ("termos", MIGRATION_NAME)
    plan = executor.migration_plan([target])
    unexpected = [(m.app_label, m.name) for m, backward in plan if backward or (m.app_label, m.name) != target]
    if unexpected or len(plan) > 1:
        print("[BLOQUEADO] Plano de migrations inesperado; revise dependencias sem alterar a base.")
        return 2

    if not plan:
        print("[AVISO] Migration ja aplicada no banco isolado; seguindo para verificacao.")
    else:
        print("[ISOLADO] Aplicando apenas SEG-TERM-001 em", TEST_DB, flush=True)
        call_command("migrate", "termos", MIGRATION_NAME, interactive=False, verbosity=1)

    with connection.cursor() as cur:
        cur.execute("SELECT current_database()")
        if cur.fetchone()[0] != TEST_DB:
            raise RuntimeError("Conexao inesperadamente alterada")
        cur.execute("""
            SELECT COUNT(*) FROM django_migrations
            WHERE app = 'termos' AND name = %s
        """, [MIGRATION_NAME])
        migration_ok = cur.fetchone()[0] == 1
        cur.execute("""
            SELECT pg_get_triggerdef(oid), tgenabled
            FROM pg_trigger
            WHERE tgrelid = 'public.termos_termo'::regclass
              AND tgname = 'termo_congelado'
        """)
        row = cur.fetchone()
        trigger_ok = bool(row and row[1] in ("O", "A") and "INSERT" in row[0]
                          and "UPDATE" in row[0] and "DELETE" in row[0])
        cur.execute("SELECT COUNT(*) FROM public.termos_termo WHERE estado = 'ASSINADO'")
        preserved = cur.fetchone()[0] >= 1

    if not (migration_ok and trigger_ok and preserved):
        print("[FALHA] Verificacao pos-migration inconsistente. Nao aplique no banco principal.")
        return 3

    print("[APROVADO] ISOLADO: MIGRACAO APLICADA", flush=True)
    print("[APROVADO] Trigger protege INSERT, UPDATE e DELETE", flush=True)
    print("[APROVADO] Termo assinado da base isolada permanece presente", flush=True)
    print("[PENDENTE] Reexecute GATI_Autotestes.py para testar os bloqueios SQL", flush=True)
    print("[SEGURANCA] Nenhuma migration foi executada no banco principal gati", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        # Do not expose SQL strings, DB credentials, or connection details.
        print("[FALHA] Execucao interrompida:", type(exc).__name__)
        print("Nao altere o banco principal; revise o ambiente e a migration.")
        raise SystemExit(3)
