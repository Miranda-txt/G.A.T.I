#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Promote the reviewed SEG-TERM-001 migration to the local GATI homologation DB.

Safe default: --verificar (read-only preflight).
With --aplicar: make a PostgreSQL custom backup, verify its TOC, and then
apply ONLY termos.0004_seg_term_001 to the local database named 'gati'.
No passwords are printed or stored in this script. The existing Django
configuration supplies credentials to pg_dump through a child-process env.

Scope: Windows 11, local GATI v1.0.0 homologation environment only.
WARNING: migration is irreversible; restore / forward-fix needs a plan.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

MAIN = "gati"
ISOLATED = "gati_segterm_teste"
TARGET = ("termos", "0004_seg_term_001")
EXPECTED_MIGRATION_SHA256 = "5788b8bcbf3fa1de39af943c8a2ea31b8a374af9912705a4b2f90e715a7673d3"
PUBLIC_URL = "http://127.0.0.1:8000"


def require(test: bool, message: str) -> None:
    if not test:
        raise RuntimeError(message)


def root_and_django():
    require(sys.platform == "win32", "Este executor foi preparado apenas para Windows.")
    root = Path(__file__).resolve().parent
    backend = root / "backend"
    migration = backend / "gati" / "apps" / "termos" / "migrations" / "0004_seg_term_001.py"
    require((backend / "manage.py").is_file(), "Coloque o script na raiz do projeto GATI.")
    require(migration.is_file(), "Migration 0004_seg_term_001.py nao encontrada.")
    digest = hashlib.sha256(migration.read_bytes()).hexdigest()
    require(digest == EXPECTED_MIGRATION_SHA256, "Migration difere do pacote revisado; interrompa para revisao.")
    require((backend / ".env").is_file(), "Arquivo backend/.env nao encontrado.")

    # Read only the DB name in the dotenv file; never print or expose credentials.
    from dotenv import dotenv_values
    dotenv_name = dotenv_values(backend / ".env").get("PGDATABASE", MAIN)
    require(dotenv_name == MAIN, "backend/.env aponta para um banco diferente de gati.")
    require(os.environ.get("PGDATABASE", MAIN) == MAIN, "PGDATABASE no ambiente aponta para outro banco.")
    require(os.environ.get("GATI_ENV", "development") == "development", "GATI_ENV nao e development.")
    require(os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.development") == "config.settings.development",
            "DJANGO_SETTINGS_MODULE inesperado.")

    os.environ["GATI_ENV"] = "development"
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.development"
    sys.path.insert(0, str(backend))
    os.chdir(backend)

    from config.env import configure
    configure()
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection, connections
    from django.db.migrations.executor import MigrationExecutor
    from django.apps import apps
    return root, settings, connection, connections, MigrationExecutor, apps


def check_cfg(settings) -> dict:
    cfg = settings.DATABASES["default"]
    require(cfg.get("ENGINE") == "django.db.backends.postgresql", "Banco nao e PostgreSQL.")
    require(cfg.get("NAME") == MAIN and cfg.get("USER") == "gati", "Banco/usuario principal inesperado.")
    require(str(cfg.get("HOST", "")).lower() in {"127.0.0.1", "localhost", "::1"},
            "Banco nao esta em localhost.")
    require(str(cfg.get("PORT") or "5432") == "5432", "Porta do PostgreSQL inesperada.")
    require(bool(cfg.get("PASSWORD")), "Senha do Django indisponivel; nao alterar autenticacao.")
    require(settings.PUBLIC_BASE_URL == PUBLIC_URL, "PUBLIC_BASE_URL inesperada.")
    require(settings.EMAIL_BACKEND in {
        "django.core.mail.backends.filebased.EmailBackend",
        "django.core.mail.backends.locmem.EmailBackend",
    }, "Backend de e-mail nao e local; ambiente nao e o homologado.")
    return cfg


def verify_signed_data(connection, apps):
    T = apps.get_model("termos", "Termo")
    A = apps.get_model("termos", "AssinaturaTermo")
    R = apps.get_model("movimentacoes", "ResponsabilidadeAtivo")
    terms = list(T.objects.filter(estado="ASSINADO").order_by("pk"))
    require(bool(terms), "Nao ha termo assinado no banco principal.")
    require(T.objects.filter(pk=1, estado="ASSINADO").exists(), "Termo de homologacao #1 nao esta ASSINADO.")
    for term in terms:
        raw = json.dumps(term.payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        calculated = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        require(bool(term.sha256) and calculated == term.sha256,
                "Payload/hash divergentes em termo assinado; nenhuma migration sera aplicada.")
        signatures = list(A.objects.filter(termo_id=term.pk))
        require(bool(signatures), "Termo assinado sem signatarios; nenhuma migration sera aplicada.")
        require(all(s.assinado_em is not None and s.hash_assinado == term.sha256 for s in signatures),
                "Assinatura ou hash divergente; nenhuma migration sera aplicada.")
    return len(terms), A.objects.filter(assinado_em__isnull=False).count(), R.objects.count()


def check_isolated(connections, cfg):
    alias = "gati_preflight_isolado"
    require(alias not in connections.databases, "Alias de base isolada ja existe.")
    mirror = deepcopy(cfg)
    mirror["NAME"] = ISOLATED
    connections.databases[alias] = mirror
    try:
        with connections[alias].cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user")
            require(cursor.fetchone() == (ISOLATED, "gati"), "Banco isolado ou usuario incorreto.")
            cursor.execute("""SELECT COUNT(*) FROM django_migrations
                              WHERE app=%s AND name=%s""", list(TARGET))
            require(cursor.fetchone()[0] == 1, "Migration ainda nao aplicada no banco isolado.")
            cursor.execute("""SELECT pg_get_triggerdef(oid), tgenabled
                              FROM pg_trigger WHERE tgrelid='public.termos_termo'::regclass
                              AND tgname='termo_congelado'""")
            row = cursor.fetchone()
            require(bool(row and row[1] in ("O", "A") and all(
                word in row[0] for word in ("INSERT", "UPDATE", "DELETE"))),
                "Trigger novo ausente ou inativo no banco isolado.")
    finally:
        connections[alias].close()
        connections.databases.pop(alias, None)


def check_main(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), current_user, current_setting('server_version_num')")
        db, role, version = cursor.fetchone()
        require((db, role) == (MAIN, "gati"), "Conexao nao e gati com usuario gati.")
        require(int(version) // 10000 == 18, "Versao PostgreSQL nao e 18.x.")
        cursor.execute("""SELECT pg_get_triggerdef(oid), tgenabled
                          FROM pg_trigger WHERE tgrelid='public.termos_termo'::regclass
                          AND tgname='termo_congelado'""")
        row = cursor.fetchone()
        require(row is not None and row[1] in ("O", "A"), "Trigger atual nao esta habilitado.")
        return row[0]


def inspect_migration_plan(connection, executor_cls):
    executor = executor_cls(connection)
    disk = set(executor.loader.disk_migrations)
    applied = set(executor.loader.applied_migrations)
    if TARGET in applied:
        return "already_applied"
    require(disk - applied == {TARGET}, "Existem migrations pendentes alem da 0004; revise antes.")
    plan = executor.migration_plan([TARGET])
    require(len(plan) == 1 and plan[0][0].app_label == TARGET[0]
            and plan[0][0].name == TARGET[1] and plan[0][1] is False,
            "Plano de migration inesperado; abortado.")
    return "one_migration"


def make_backup(cfg: dict) -> Path:
    pg_bin = Path(r"C:\Program Files\PostgreSQL\18\bin")
    pg_dump = pg_bin / "pg_dump.exe"
    pg_restore = pg_bin / "pg_restore.exe"
    require(pg_dump.is_file() and pg_restore.is_file(), "pg_dump/pg_restore 18 nao encontrados.")

    directory = Path.home() / "GATI-backups"
    directory.mkdir(parents=True, exist_ok=True)
    filename = (f"gati-pre-promocao-segterm001-"
                f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}.dump")
    target = directory / filename
    require(not target.exists(), "Backup ja existe; nao sobrescrever.")

    # No password in command line, stdout, logs, files or parent process env.
    child_env = os.environ.copy()
    child_env["PGPASSWORD"] = str(cfg["PASSWORD"])
    args = [str(pg_dump), "--host", str(cfg.get("HOST") or "127.0.0.1"),
            "--port", str(cfg.get("PORT") or "5432"), "--username", "gati",
            "--no-password", "--dbname", MAIN, "--format=custom", "--file", str(target)]
    try:
        result = subprocess.run(args, env=child_env, capture_output=True,
                                text=True, timeout=180, check=False)
    except Exception as exc:
        raise RuntimeError(f"pg_dump falhou ao iniciar ({type(exc).__name__}); migration nao executada.") from None
    require(result.returncode == 0 and target.is_file() and target.stat().st_size > 1024,
            "Backup falhou ou ficou incompleto; migration nao executada.")
    result = subprocess.run([str(pg_restore), "--list", str(target)],
                            capture_output=True, text=True, timeout=30, check=False)
    require(result.returncode == 0 and "TOC Entries:" in result.stdout,
            "pg_restore nao reconheceu o backup; migration nao executada.")
    print("[APROVADO] Backup PostgreSQL criado e inventario reconhecido.", flush=True)
    print("[BACKUP]", target, flush=True)
    print("[AVISO] Backup contem dados; mantenha-o privado e fora do Git.", flush=True)
    return target


def verify_patch(connection, before):
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), current_user")
        require(cursor.fetchone() == (MAIN, "gati"), "Conexao mudou apos migration.")
        cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app=%s AND name=%s", list(TARGET))
        require(cursor.fetchone()[0] == 1, "Migration 0004 nao registrada no principal.")
        cursor.execute("""SELECT pg_get_triggerdef(oid), tgenabled FROM pg_trigger
                          WHERE tgrelid='public.termos_termo'::regclass
                          AND tgname='termo_congelado'""")
        row = cursor.fetchone()
        require(bool(row and row[1] in ("O", "A") and all(
            word in row[0] for word in ("INSERT", "UPDATE", "DELETE"))),
            "Trigger principal pos-migration inconsistente.")


def main():
    parser = argparse.ArgumentParser(description="Promocao controlada SEG-TERM-001 no banco GATI local")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--verificar", action="store_true", help="Somente leitura (padrao)")
    selection.add_argument("--aplicar", action="store_true", help="Backup e aplicacao no banco principal")
    args = parser.parse_args()
    print("GATI SEG-TERM-001 | Modo:", "APLICAR" if args.aplicar else "VERIFICAR", flush=True)
    root, settings, connection, connections, migration_executor, apps = root_and_django()
    cfg = check_cfg(settings)
    check_isolated(connections, cfg)
    print("[APROVADO] Base isolada ja contem a migration revisada.", flush=True)
    before_trigger = check_main(connection)
    before = verify_signed_data(connection, apps)
    print(f"[APROVADO] Banco principal gati; {before[0]} termo(s) assinado(s); "
          f"{before[1]} aceite(s); {before[2]} responsabilidade(s).", flush=True)
    status = inspect_migration_plan(connection, migration_executor)

    if status == "already_applied":
        verify_patch(connection, before)
        print("[APROVADO] Migration 0004 ja aplicada; nada a modificar.", flush=True)
        return 0
    require("BEFORE" in before_trigger and "UPDATE" in before_trigger,
            "Trigger principal original inesperado.")
    print("[APROVADO] Plano de migrations: somente termos.0004_seg_term_001.", flush=True)
    if not args.aplicar:
        print("[SEGURO] Nenhum dado alterado. Para promover com backup: --aplicar", flush=True)
        return 0

    make_backup(cfg)
    from django.core.management import call_command
    print("[PRINCIPAL] Aplicando somente termos.0004_seg_term_001 no banco gati...", flush=True)
    try:
        call_command("migrate", TARGET[0], TARGET[1], interactive=False, verbosity=1)
    except Exception as exc:
        raise RuntimeError(f"Migration falhou ({type(exc).__name__}). Nao repita sem investigar; backup preservado.") from None
    verify_patch(connection, before)
    after = verify_signed_data(connection, apps)
    require(after == before, "Contagens de evidencias diferem apos migration; investigar imediatamente.")
    print("[APROVADO] Migration no principal; trigger ativo; evidencias assinadas preservadas.", flush=True)
    print("[PENDENTE] Reexecutar GATI_Autotestes.py --sem-pytest e tratar suite pytest/HTTP.", flush=True)
    print("[AVISO] Migration irreversivel; recuperacao exige migration de ajuste ou backup.", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("[BLOQUEADO]", str(exc), flush=True)
        print("Nao execute migrate manualmente nem altere triggers ate revisar a causa.", flush=True)
        raise SystemExit(2)
