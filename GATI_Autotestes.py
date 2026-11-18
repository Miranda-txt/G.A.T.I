#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
GATI v1.0.0 - homologacao automatizada segura (Windows / Django / PostgreSQL).

Uso no PowerShell, na raiz do projeto:
    & ".\backend\.venv\Scripts\python.exe" .\GATI_Autotestes.py

Alternativa, se o arquivo estiver em Downloads:
    & ".\backend\.venv\Scripts\python.exe" "$env:USERPROFILE\Downloads\GATI_Autotestes.py" --root .

Seguranca operacional:
* Lê as credenciais que a aplicacao JA possui no backend/.env; nao pede nem registra senhas.
* Banco principal "gati": somente SELECT, em transacao READ ONLY.
* Testes SQL de alteracao: SOMENTE em "gati_segterm_teste", com ROLLBACK.
* Pytest completo: somente em banco temporario UNICO, criado pelo proprio pytest, se
  a conta da aplicacao tiver CREATEDB; caso contrario e indicado como PENDENTE.
* Nao executa DROP em bases existentes, nao cria superusuarios, nao altera pg_hba.conf.
* Nao envia e-mails, nao assina termos e nao testa o token real de assinatura.
* Relatorios JSON e Markdown ficam em %USERPROFILE%/GATI-relatorios.

REQUISITOS: executar com o Python do ambiente virtual do proprio GATI.
Este utilitario auxilia a homologacao: nao substitui testes E2E, auditoria ou pentest.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from urllib.parse import urlsplit
from urllib.request import build_opener, ProxyHandler, Request
from uuid import uuid4

VERSION = "1.0.0"
MAIN_DB = "gati"
TEST_DB = "gati_segterm_teste"
CHECKED_TRIGGERS = {
    "termo_congelado": "termos_termo",
    "assinatura_protegida": "termos_assinaturatermo",
    "item_congelado": "termos_termoitem",
    "processo_protegido": "movimentacoes_processomovimentacao",
    "processo_item_protegido": "movimentacoes_processoitem",
    "responsabilidade_protegida": "movimentacoes_responsabilidadeativo",
    "historico_imutavel": "movimentacoes_movimentacao",
    "auditoria_imutavel": "auditoria_logauditoria",
    "arquivo_protegido": "arquivos_arquivo",
}


class Reporter:
    def __init__(self, root: Path):
        self.root = root
        self.entries: list[dict] = []
        self.started = datetime.now().astimezone().isoformat(timespec="seconds")

    def add(self, title: str, result: str, details: str) -> None:
        assert result in {"APROVADO", "FALHA", "AVISO", "PENDENTE"}
        self.entries.append({"teste": title, "resultado": result, "detalhes": details})
        print(f"[{result}] {title} - {details}", flush=True)

    def write(self, folder: Path) -> tuple[Path, Path]:
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"gati-autotestes-{stamp}-{os.getpid()}"
        json_path = folder / (name + ".json")
        md_path = folder / (name + ".md")
        outcomes = {s: sum(x["resultado"] == s for x in self.entries)
                    for s in ("APROVADO", "FALHA", "AVISO", "PENDENTE")}
        doc = {
            "ferramenta": "GATI_Autotestes.py",
            "versao": VERSION,
            "inicio": self.started,
            "fim": datetime.now().astimezone().isoformat(timespec="seconds"),
            "projeto": str(self.root),
            "politica": "principal somente leitura; negativos somente em banco isolado com rollback",
            "resumo": outcomes,
            "testes": self.entries,
        }
        json_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        rows = [
            "# Relatorio automatico de homologacao GATI",
            "",
            f"- Inicio: {self.started}",
            f"- Projeto: `{self.root}`",
            "- Banco principal: `gati` (somente leitura)",
            "- Banco de testes: `gati_segterm_teste` (transacoes revertidas)",
            "- As senhas, tokens e hashes completos nao integram este relatorio.",
            "",
            "## Resumo",
            "",
        ]
        for status, count in outcomes.items():
            rows.append(f"- **{status}**: {count}")
        rows += ["", "## Resultados", ""]
        for index, item in enumerate(self.entries, start=1):
            rows += [f"{index}. **[{item['resultado']}] {item['teste']}**: {item['detalhes']}"]
        rows += [
            "", "## Limites desta execucao", "",
            "O executor nao troca senhas, nao realiza assinaturas reais, nao envia e-mail,",
            "nao simula todos os fluxos visuais nem garante ausencia de vulnerabilidades.",
            "A suite pytest completa e executada apenas se existir permissao CREATEDB,",
            "sempre em um banco temporario gerado para esta execucao.",
            "", "Uma FALHA de seguranca deve ser corrigida no codigo/migrations e revalidada",
            "em ambiente isolado antes de promover uma alteracao para a base principal.", "",
        ]
        md_path.write_text("\n".join(rows), encoding="utf-8")
        return json_path, md_path


def error_type(exc: BaseException) -> str:
    # Nao expor detalhes de conexao, SQL, enderecos ou segredos de excecoes.
    return type(exc).__name__


def locate_root(explicit: str | None) -> Path:
    options = []
    if explicit:
        options.append(Path(explicit).expanduser())
    else:
        options += [Path.cwd(), Path(__file__).resolve().parent,
                    Path.home() / "Projetos" / "gati"]
    for root in options:
        root = root.resolve()
        if (root / "backend" / "manage.py").is_file() and (root / "backend" / "config" / "env.py").is_file():
            return root
    raise RuntimeError("Raiz do GATI nao encontrada. Use --root CAMINHO_DO_PROJETO.")


def setup_django(root: Path):
    backend = root / "backend"
    sys.path.insert(0, str(backend))
    os.chdir(str(backend))  # Reproduz comportamento de manage.py; evita importar outro projeto.
    from config.env import configure
    configure()  # Carrega backend/.env; nunca exibe as credenciais.
    import django
    django.setup()
    from django.conf import settings
    return django, settings


def new_pg_conn(psycopg, cfg: dict, database: str, *, readonly: bool):
    opts = cfg.get("OPTIONS", {}) or {}
    connect_kwargs = {
        "dbname": database,
        "user": cfg.get("USER") or "",
        "password": cfg.get("PASSWORD") or "",
        "host": cfg.get("HOST") or "127.0.0.1",
        "port": cfg.get("PORT") or 5432,
        "connect_timeout": min(int(opts.get("connect_timeout", 5)), 10),
        "autocommit": False,
        "options": "-c statement_timeout=10000 -c lock_timeout=3000",
    }
    conn = psycopg.connect(**connect_kwargs)
    if readonly:
        # Primeiro comando executado nessa conexao: nao permitir escrita nem por engano.
        conn.execute("SET TRANSACTION READ ONLY")
    return conn


def scalar(cur, query: str, params=()):
    cur.execute(query, params)
    row = cur.fetchone()
    return row[0] if row else None


def basic_checks(report: Reporter, root: Path, settings, django) -> None:
    report.add("Ambiente Python/Django", "APROVADO",
               f"Python {sys.version_info.major}.{sys.version_info.minor}; Django {django.get_version()}")
    backend = settings.EMAIL_BACKEND
    if backend in {
        "django.core.mail.backends.filebased.EmailBackend",
        "django.core.mail.backends.locmem.EmailBackend",
    }:
        report.add("Email de homologacao", "APROVADO", "Backend de arquivos/memoria; nenhum convite sera enviado")
    else:
        report.add("Email de homologacao", "AVISO",
                   "Backend pode permitir envio real. Executor nao envia mensagens")
    public_url = str(getattr(settings, "PUBLIC_BASE_URL", ""))
    parts = urlsplit(public_url)
    if parts.scheme == "http" and parts.hostname in ("127.0.0.1", "localhost") and parts.port == 8000:
        report.add("URL publica de convites", "APROVADO", "URL local na porta 8000")
    elif parts.scheme == "https":
        report.add("URL publica de convites", "APROVADO", "HTTPS configurado")
    else:
        report.add("URL publica de convites", "AVISO", "Conferir dominio/porta configurados")

    # Django system checks (nao cria nem altera registros).
    try:
        from django.core.management import call_command
        buffer = io.StringIO()
        call_command("check", stdout=buffer, stderr=buffer)
        report.add("Django system check", "APROVADO", "Sem erros impeditivos detectados")
    except Exception as exc:
        report.add("Django system check", "FALHA", f"Falhou: {error_type(exc)}")

    # Servidor de desenvolvimento e scanner: consultas de disponibilidade, sem escrita.
    for name, host, port in (
        ("Servidor web GATI", "127.0.0.1", 8000),
        ("Servico ClamAV", str(getattr(settings, "CLAMAV_HOST", "127.0.0.1")),
         int(getattr(settings, "CLAMAV_PORT", 3310))),
    ):
        try:
            with socket.create_connection((host, port), timeout=1.5):
                pass
            report.add(name, "APROVADO", "Porta TCP acessivel")
        except OSError:
            report.add(name, "AVISO", "Nao foi possivel conectar na porta TCP")

    report_dir = getattr(settings, "EMAIL_FILE_PATH", None)
    if report_dir:
        email_path = Path(report_dir)
        files = sorted([p for p in email_path.glob("*.log") if p.is_file()],
                       key=lambda p: p.stat().st_mtime, reverse=True) if email_path.exists() else []
        if files:
            # So verifica a existencia. Conteudo, tokens e URLs nunca sao impressos.
            report.add("Convites locais", "APROVADO", f"{len(files)} arquivo(s) de email identificados")
        else:
            report.add("Convites locais", "AVISO", "Nenhum arquivo de convite encontrado")

    backups = Path.home() / "GATI-backups"
    files = sorted(backups.glob("gati-*.dump"), key=lambda p: p.stat().st_mtime, reverse=True) if backups.exists() else []
    if files:
        report.add("Backup PostgreSQL", "APROVADO", f"{len(files)} arquivo(s) detectados")
        pg_restore = shutil.which("pg_restore")
        fallback = Path("C:/Program Files/PostgreSQL/18/bin/pg_restore.exe")
        pg_restore = pg_restore or (str(fallback) if fallback.is_file() else None)
        if not pg_restore:
            report.add("Inventario do ultimo backup", "PENDENTE", "pg_restore nao encontrado")
        else:
            try:
                check = subprocess.run([pg_restore, "--list", str(files[0])],
                                       capture_output=True, timeout=20)
                report.add("Inventario do ultimo backup",
                           "APROVADO" if check.returncode == 0 else "FALHA",
                           "Arquivo reconhecido pelo pg_restore" if check.returncode == 0 else
                           "pg_restore nao conseguiu ler o inventario")
            except Exception as exc:
                report.add("Inventario do ultimo backup", "PENDENTE", f"Falha: {error_type(exc)}")
    else:
        report.add("Backup PostgreSQL", "AVISO", "Nenhum backup encontrado em GATI-backups")

    if parts.scheme == "http" and parts.hostname in ("127.0.0.1", "localhost") and parts.port == 8000:
        try:
            opener = build_opener(ProxyHandler({}))
            with opener.open(Request("http://127.0.0.1:8000/entrar/", method="GET"), timeout=3) as response:
                ok = response.status == 200
            report.add("HTTP pagina de acesso", "APROVADO" if ok else "AVISO",
                       "Pagina /entrar/ respondeu" if ok else "Status HTTP inesperado")
        except Exception as exc:
            report.add("HTTP pagina de acesso", "AVISO", f"Nao foi possivel validar /entrar/: {error_type(exc)}")


def inspect_main(report: Reporter, conn, *, settings) -> dict:
    state = {"has_signed": False, "can_createdb": False, "signed_id": None, "signature_id": None, "process_id": None}
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user, current_setting('server_version')")
        database, user, version = cur.fetchone()
        if database != MAIN_DB:
            report.add("Identidade do banco principal", "FALHA", "Conexao diferente de gati; consulta interrompida")
            return state
        report.add("Identidade do banco principal", "APROVADO", f"Banco gati, usuario {user}, PostgreSQL {version}")
        state["can_createdb"] = bool(scalar(cur,
            "SELECT rolcreatedb OR rolsuper FROM pg_roles WHERE rolname=current_user"))
        applied = set()
        cur.execute("SELECT app, name FROM django_migrations")
        applied.update(cur.fetchall())
        from django.db.migrations.loader import MigrationLoader
        expected = set(MigrationLoader(None).disk_migrations)
        unapplied = expected - applied
        if unapplied:
            report.add("Migracoes Django", "FALHA", f"{len(unapplied)} migracao(oes) nao aplicada(s)")
        else:
            report.add("Migracoes Django", "APROVADO", f"{len(applied)} migracoes registradas")

        cur.execute("""
            SELECT cls.relname, t.tgname, t.tgenabled
            FROM pg_trigger t JOIN pg_class cls ON cls.oid=t.tgrelid
            WHERE NOT t.tgisinternal
        """)
        triggers = {name: (table, enabled) for table, name, enabled in cur.fetchall()}
        bad = [name for name, table in CHECKED_TRIGGERS.items()
               if name not in triggers or triggers[name][0] != table or triggers[name][1] not in ("O", "A")]
        if bad:
            report.add("Triggers de integridade", "FALHA", f"{len(bad)} trigger(s) ausente(s), desabilitado(s) ou divergente(s)")
        else:
            report.add("Triggers de integridade", "APROVADO", f"{len(CHECKED_TRIGGERS)} triggers habilitados")

        # Ativos: sem expor patrimonio, serie ou informacoes de colaboradores.
        cur.execute("""
            SELECT indexname FROM pg_indexes
            WHERE schemaname='public' AND tablename='ativos_ativo'
              AND indexname IN ('ativo_patrimonio_ativo','ativo_service_tag_ativo')
        """)
        indexes = {row[0] for row in cur.fetchall()}
        report.add("Unicidade de ativos", "APROVADO" if len(indexes) == 2 else "FALHA",
                   f"{len(indexes)}/2 indices de unicidade esperados presentes")

        cur.execute("SELECT id, estado, payload, sha256, processo_id FROM termos_termo WHERE estado='ASSINADO' ORDER BY id")
        signed_terms = cur.fetchall()
        if not signed_terms:
            report.add("Termos assinados", "PENDENTE", "Nao ha termo assinado para verificar")
        else:
            invalid = []
            for term_id, term_state, payload, saved_hash, process_id in signed_terms:
                if isinstance(payload, str):
                    payload = json.loads(payload)
                serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                actual_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
                if actual_hash != saved_hash or not re.fullmatch(r"[0-9a-f]{64}", saved_hash or ""):
                    invalid.append(term_id)
                cur.execute("""
                    SELECT COUNT(*), COUNT(*) FILTER (WHERE assinado_em IS NOT NULL
                        AND hash_assinado=%s AND ip IS NOT NULL AND user_agent IS NOT NULL)
                    FROM termos_assinaturatermo WHERE termo_id=%s
                """, (saved_hash, term_id))
                total, valid = cur.fetchone()
                if not total or total != valid:
                    invalid.append(term_id)
                cur.execute("SELECT estado FROM movimentacoes_processomovimentacao WHERE id=%s", (process_id,))
                process_row = cur.fetchone()
                if process_row and process_row[0] == "CONCLUIDO":
                    # Nao presumir que todo termo assinado equivale a um processo concluido.
                    pass
            if invalid:
                report.add("Integridade de termos/assinaturas", "FALHA",
                           f"Inconsistencia em {len(set(invalid))} de {len(signed_terms)} termo(s) assinado(s)")
            else:
                report.add("Integridade de termos/assinaturas", "APROVADO",
                           f"SHA-256, evidencia e assinatura consistentes em {len(signed_terms)} termo(s)")
            state["has_signed"] = True
            state["signed_id"] = signed_terms[0][0]
            state["process_id"] = signed_terms[0][4]
            cur.execute("SELECT id FROM termos_assinaturatermo WHERE termo_id=%s AND assinado_em IS NOT NULL ORDER BY id LIMIT 1", (state["signed_id"],))
            row = cur.fetchone()
            if row:
                state["signature_id"] = row[0]

        count_respons = scalar(cur, "SELECT COUNT(*) FROM movimentacoes_responsabilidadeativo")
        count_bad = scalar(cur, """
            SELECT COUNT(*) FROM movimentacoes_responsabilidadeativo r
            WHERE NOT EXISTS (
                SELECT 1 FROM termos_termo t
                WHERE t.processo_id=r.processo_inicio_id AND t.estado='ASSINADO'
            )
        """)
        report.add("Responsabilidades patrimoniais", "APROVADO" if count_bad == 0 else "FALHA",
                   f"{count_respons} registro(s); {count_bad} sem termo assinado na origem")

        audit_count = scalar(cur, "SELECT COUNT(*) FROM auditoria_logauditoria")
        report.add("Auditoria", "APROVADO" if audit_count else "AVISO",
                   f"{audit_count} evento(s) de auditoria registrados")
    return state


def main_connect_and_inspect(report: Reporter, settings, psycopg) -> dict:
    cfg = dict(settings.DATABASES["default"])
    state = {"cfg": cfg, "can_createdb": False, "has_signed": False}
    if cfg.get("ENGINE") != "django.db.backends.postgresql":
        report.add("Configuracao do banco", "FALHA", "Driver nao e PostgreSQL")
        return state
    if str(cfg.get("NAME")) != MAIN_DB:
        report.add("Configuracao do banco", "FALHA", "Banco configurado nao e gati; execucao recusada")
        return state
    # E intencionalmente conservador: homologacao em localhost, nao em producao remota.
    if str(cfg.get("HOST") or "127.0.0.1").lower() not in ("127.0.0.1", "localhost", "::1"):
        report.add("Configuracao do banco", "FALHA", "Servidor PostgreSQL nao e local; execucao recusada")
        return state
    report.add("Configuracao do banco", "APROVADO", "PostgreSQL local, acesso via credencial existente do Django")
    try:
        conn = new_pg_conn(psycopg, cfg, MAIN_DB, readonly=True)
        try:
            state.update(inspect_main(report, conn, settings=settings))
        finally:
            conn.rollback()
            conn.close()
    except Exception as exc:
        report.add("Conexao principal SOMENTE LEITURA", "FALHA",
                   f"Nao foi possivel completar auditoria: {error_type(exc)}. Verifique backend/.env sem exibir a senha")
    return state


def isolated_guard(report: Reporter, cfg: dict, psycopg):
    try:
        conn = new_pg_conn(psycopg, cfg, TEST_DB, readonly=False)
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user, to_regclass('public.termos_termo')")
            db, user, regclass = cur.fetchone()
            if db != TEST_DB or regclass is None or user != str(cfg.get("USER")):
                report.add("Isolamento dos testes negativos", "FALHA", "Identidade/esquema da base isolada incorretos")
                return False
            term_count = scalar(cur, "SELECT COUNT(*) FROM termos_termo WHERE estado='ASSINADO'")
            if not term_count:
                report.add("Isolamento dos testes negativos", "PENDENTE", "Banco isolado sem termo assinado; restaure o backup")
                return False
            if term_count > 0:
                report.add("Isolamento dos testes negativos", "APROVADO",
                           f"Base isolada confirmada, com {term_count} termo(s) assinado(s)")
                return True
    except Exception as exc:
        report.add("Isolamento dos testes negativos", "PENDENTE",
                   f"Banco isolado inacessivel: {error_type(exc)}")
    finally:
        if "conn" in locals():
            conn.rollback()
            conn.close()
    return False


def run_negative_case(report: Reporter, psycopg, cfg: dict, title: str,
                      test_fn, *, allowed_codes=("23514",)):
    """Executa um unico teste em transacao que SEMPRE termina em ROLLBACK."""
    conn = None
    try:
        conn = new_pg_conn(psycopg, cfg, TEST_DB, readonly=False)
        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            if cur.fetchone()[0] != TEST_DB:
                raise RuntimeError("Banco de teste incorreto")
            # Se nao havia conexao com a base errada, o teste pode escrever apenas aqui.
            try:
                test_fn(cur)
            except psycopg.Error as exc:
                if exc.sqlstate in allowed_codes:
                    report.add(title, "APROVADO", f"Bloqueio aplicado pelo PostgreSQL (SQLSTATE {exc.sqlstate})")
                else:
                    report.add(title, "PENDENTE", f"Erro nao esperado: SQLSTATE {exc.sqlstate or 'desconhecido'}")
            else:
                report.add(title, "FALHA", "Alteracao indevida aceita pelo PostgreSQL dentro da transacao de teste")
    except Exception as exc:
        report.add(title, "PENDENTE", f"Teste nao concluiu: {error_type(exc)}")
    finally:
        if conn is not None:
            # NUNCA COMMIT, mesmo se a tentativa de alteracao foi aceita.
            try:
                conn.rollback()
            finally:
                conn.close()


def run_negative_tests(report: Reporter, psycopg, cfg: dict) -> None:
    if not isolated_guard(report, cfg, psycopg):
        report.add("Testes negativos", "PENDENTE", "Nao executados por falta de base isolada valida")
        return

    def signed_term_id(cur):
        value = scalar(cur, "SELECT id FROM termos_termo WHERE estado='ASSINADO' ORDER BY id LIMIT 1")
        if value is None:
            raise RuntimeError("Termo assinado indisponivel")
        return value

    def signature_id(cur):
        value = scalar(cur, """
            SELECT s.id FROM termos_assinaturatermo s
            JOIN termos_termo t ON t.id=s.termo_id
            WHERE t.estado='ASSINADO' AND s.assinado_em IS NOT NULL
            ORDER BY s.id LIMIT 1
        """)
        if value is None:
            raise RuntimeError("Assinatura concluida indisponivel")
        return value

    def text_tamper(cur):
        cur.execute("UPDATE termos_termo SET texto=texto || %s WHERE id=%s",
                    (" [GATI-TESTE-NEGATIVO]", signed_term_id(cur)))

    def hash_tamper(cur):
        cur.execute("UPDATE termos_termo SET sha256=%s WHERE id=%s",
                    ("0" * 64, signed_term_id(cur)))

    def term_delete(cur):
        cur.execute("DELETE FROM termos_termo WHERE id=%s", (signed_term_id(cur),))

    def signature_tamper(cur):
        cur.execute("UPDATE termos_assinaturatermo SET user_agent=%s WHERE id=%s",
                    ("GATI-AUTO-TESTE", signature_id(cur)))

    def signature_delete(cur):
        cur.execute("DELETE FROM termos_assinaturatermo WHERE id=%s", (signature_id(cur),))

    for name, test in (
        ("Negativo: alterar texto assinado", text_tamper),
        ("Negativo: alterar SHA-256 assinado", hash_tamper),
        ("Negativo: excluir termo assinado", term_delete),
        ("Negativo: adulterar evidencia de assinatura", signature_tamper),
        ("Negativo: excluir assinatura concluida", signature_delete),
    ):
        run_negative_case(report, psycopg, cfg, name, test)

    # SEG-TERM-001: cria processo e termo sintenticos com todas as referencias validas
    # na MESMA transacao. Caso o gatilho aceite a transicao, o achado e confirmado.
    def term_transition(cur):
        term_id = -1_500_000_000 - (uuid4().int % 100_000_000)
        process_id = -1_600_000_000 - (uuid4().int % 100_000_000)
        cur.execute("""
            INSERT INTO movimentacoes_processomovimentacao
            (id, criado_em, atualizado_em, versao, tipo, responsavel_id,
             localizacao_id, data, observacoes, estado, criado_por_id, concluido_em)
            SELECT %s, NOW(), NOW(), 1, tipo, responsavel_id,
                   localizacao_id, data, observacoes, 'EM_EDICAO', criado_por_id, NULL
            FROM movimentacoes_processomovimentacao WHERE id=(
                SELECT processo_id FROM termos_termo WHERE estado='ASSINADO' ORDER BY id LIMIT 1
            )
        """, (process_id,))
        if cur.rowcount != 1:
            raise RuntimeError("Processo sintentico nao criado")
        cur.execute("""
            INSERT INTO termos_termo
            (id, criado_em, atualizado_em, versao, substitui_id, processo_id,
             modelo_id, texto, estado, payload, sha256, emitido_em,
             cancelado_em, motivo_cancelamento)
            SELECT %s, NOW(), NOW(), 1, NULL, %s, modelo_id,
                   'TESTE SEG-TERM-001 SEM VALOR', 'EM_EDICAO', '{}'::jsonb,
                   '', NULL, NULL, ''
            FROM termos_termo WHERE estado='ASSINADO' ORDER BY id LIMIT 1
        """, (term_id, process_id))
        if cur.rowcount != 1:
            raise RuntimeError("Termo sintentico nao criado")
        # Verifica explicitamente que nao ha signatarios.
        if scalar(cur, "SELECT COUNT(*) FROM termos_assinaturatermo WHERE termo_id=%s", (term_id,)) != 0:
            raise RuntimeError("Termo sintentico possui signatarios")
        cur.execute("UPDATE termos_termo SET estado='ASSINADO' WHERE id=%s", (term_id,))
        if cur.rowcount != 1:
            raise RuntimeError("Transicao nao afetou linha")
        # Exigir FKs consistentes no proprio teste, sem COMMIT.
        cur.execute("SET CONSTRAINTS ALL IMMEDIATE")
        if scalar(cur, "SELECT estado FROM termos_termo WHERE id=%s", (term_id,)) != "ASSINADO":
            raise RuntimeError("Transicao nao persistiu dentro da transacao")

    run_negative_case(report, psycopg, cfg,
                      "SEG-TERM-001: bloquear assinatura sem signatario", term_transition)

    # Confirma que as bases nao ficaram com os IDs temporarios, sem publicar qualquer dado.
    try:
        conn = new_pg_conn(psycopg, cfg, TEST_DB, readonly=True)
        with conn.cursor() as cur:
            count = scalar(cur, "SELECT COUNT(*) FROM termos_termo WHERE id < -1500000000")
            count_process = scalar(cur, "SELECT COUNT(*) FROM movimentacoes_processomovimentacao WHERE id < -1600000000")
            report.add("Rollback dos testes negativos", "APROVADO" if count == 0 and count_process == 0 else "FALHA",
                       f"Termos temporarios: {count}; processos temporarios: {count_process}")
    except Exception as exc:
        report.add("Rollback dos testes negativos", "PENDENTE", f"Verificacao inconclusiva: {error_type(exc)}")
    finally:
        if "conn" in locals():
            conn.rollback()
            conn.close()


def pytest_suite(report: Reporter, root: Path, settings, state: dict,
                 *, enabled: bool, timeout: int = 300) -> None:
    test_dir = root / "backend" / "tests"
    if not test_dir.is_dir():
        report.add("Suite pytest do projeto", "PENDENTE", "Pasta backend/tests nao encontrada")
        return
    if not importlib.util.find_spec("pytest") or not importlib.util.find_spec("pytest_django"):
        report.add("Suite pytest do projeto", "PENDENTE", "pytest ou pytest-django indisponivel no ambiente")
        return
    if not enabled:
        report.add("Suite pytest do projeto", "PENDENTE", "Execucao desabilitada por --sem-pytest")
        return
    if not state.get("can_createdb"):
        # A descoberta de testes nao exige CREATE DATABASE. Isola o nome de conexao
        # para que importacoes com efeitos colaterais nao usem o banco principal.
        env = os.environ.copy()
        env.update({
            "PGDATABASE": "gati_auto_coleta_" + uuid4().hex[:12],
            "DJANGO_SETTINGS_MODULE": "config.settings.test",
            "GATI_ENV": "test",
            "PYTHONDONTWRITEBYTECODE": "1",
        })
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q",
                 "-p", "no:cacheprovider"],
                cwd=str(root / "backend"), env=env,
                capture_output=True, text=True, timeout=45,
                encoding="utf-8", errors="replace",
            )
            match = re.search(r"(\d+) tests? collected", result.stdout)
            total = match.group(1) if match else "quantidade nao identificada"
            report.add("Suite pytest do projeto", "PENDENTE",
                       f"Coleta: {total} teste(s); execucao bloqueada por falta de CREATEDB")
        except Exception as exc:
            report.add("Suite pytest do projeto", "PENDENTE",
                       f"Conta sem CREATEDB; coleta falhou: {error_type(exc)}")
        return

    # Cria base com nome aleatorio/exclusivo para a sessao; pytest criara 'test_' + base.
    unique = uuid4().hex[:16]
    base_name = f"gati_auto_{unique}"
    test_name = f"test_{base_name}"
    cfg = state["cfg"]
    import psycopg
    try:
        check_conn = new_pg_conn(psycopg, cfg, MAIN_DB, readonly=True)
        with check_conn.cursor() as cur:
            existing = scalar(cur, "SELECT COUNT(*) FROM pg_database WHERE datname IN (%s,%s)",
                              (base_name, test_name))
        check_conn.rollback()
        check_conn.close()
        if existing:
            report.add("Suite pytest do projeto", "PENDENTE", "Nome temporario inesperadamente existente")
            return
    except Exception as exc:
        report.add("Suite pytest do projeto", "PENDENTE", f"Falha na verificacao previa: {error_type(exc)}")
        return

    env = os.environ.copy()
    # Configura o banco BASE do pytest para nome aleatorio, nunca gati/gati_segterm_teste.
    env.update({
        "PGDATABASE": base_name,
        "PGUSER": str(cfg["USER"]),
        "PGPASSWORD": str(cfg.get("PASSWORD", "")),
        "PGHOST": str(cfg.get("HOST", "127.0.0.1")),
        "PGPORT": str(cfg.get("PORT", 5432)),
        "DJANGO_SETTINGS_MODULE": "config.settings.test",
        "GATI_ENV": "test",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    args = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--disable-warnings"]
    try:
        # Validacao adicional do banco resolvido no SUBPROCESSO, antes da suite.
        verify = subprocess.run(
            [sys.executable, "-c",
             "from config.env import configure; configure(); from django.conf import settings; "
             f"assert settings.DATABASES['default']['NAME']=='{base_name}'"],
            cwd=str(root / "backend"), env=env, capture_output=True, text=True, timeout=20,
            encoding="utf-8", errors="replace",
        )
        if verify.returncode != 0:
            report.add("Suite pytest do projeto", "PENDENTE", "Preflight do banco temporario nao foi aprovado")
            return
        completed = subprocess.run(args, cwd=str(root / "backend"), env=env,
                                   capture_output=True, text=True, timeout=timeout,
                                   encoding="utf-8", errors="replace")
        lines = (completed.stdout + "\n" + completed.stderr).splitlines()
        summaries = [line.strip()[:180] for line in lines if re.search(
            r"\b(passed|failed|error|skipped|warnings?)\b", line, re.I)]
        summary = "; ".join(summaries[-3:])[:350] if summaries else "Sem resumo identificado"
        report.add("Suite pytest do projeto",
                   "APROVADO" if completed.returncode == 0 else "FALHA",
                   f"Codigo {completed.returncode}; {summary}")
    except subprocess.TimeoutExpired:
        report.add("Suite pytest do projeto", "PENDENTE", f"Tempo limite atingido ({timeout}s)")
    except Exception as exc:
        report.add("Suite pytest do projeto", "PENDENTE", f"Falha ao iniciar: {error_type(exc)}")
    # A base test_<random> e descartada automaticamente pelo pytest no fluxo normal.
    # Nao efetuamos DROP para evitar qualquer exclusao automatica de banco de dados.
    # Se pytest falhar durante a limpeza, relatar pendencia sem tocar em outro banco.
    try:
        check_conn = new_pg_conn(psycopg, cfg, MAIN_DB, readonly=True)
        with check_conn.cursor() as cur:
            remaining = scalar(cur, "SELECT COUNT(*) FROM pg_database WHERE datname=%s", (test_name,))
        check_conn.rollback()
        check_conn.close()
        if remaining:
            report.add("Limpeza do banco pytest", "AVISO",
                       "Banco temporario da suite permaneceu; nao foi apagado automaticamente por seguranca")
        else:
            report.add("Limpeza do banco pytest", "APROVADO", "Nenhum banco temporario remanescente")
    except Exception:
        report.add("Limpeza do banco pytest", "AVISO", "Nao foi possivel verificar a limpeza")


def parse_args():
    p = argparse.ArgumentParser(description="GATI: executor de testes automaticos, sem senha interativa.")
    p.add_argument("--root", help="Raiz do projeto GATI (pasta que contem backend/manage.py)")
    p.add_argument("--sem-pytest", action="store_true", help="Nao tentar executar pytest mesmo com CREATEDB")
    p.add_argument("--sem-negativos", action="store_true", help="Executar apenas testes de leitura")
    p.add_argument("--relatorios", help="Diretorio para os relatorios (padrao: ~/GATI-relatorios)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = None
    report = Reporter(Path.cwd())
    try:
        root = locate_root(args.root)
        report.root = root
        print(f"\nGATI AUTOTESTES v{VERSION} | raiz: {root}\n", flush=True)
        django, settings = setup_django(root)
        basic_checks(report, root, settings, django)
        try:
            import psycopg
        except ImportError:
            report.add("Driver PostgreSQL", "FALHA", "psycopg ausente no Python utilizado")
            return finish(report, args)
        state = main_connect_and_inspect(report, settings, psycopg)
        if state.get("cfg") and state.get("has_signed") and str(state["cfg"].get("NAME")) == MAIN_DB:
            if args.sem_negativos:
                report.add("Testes negativos", "PENDENTE", "Desabilitados por --sem-negativos")
            else:
                run_negative_tests(report, psycopg, state["cfg"])
            pytest_suite(report, root, settings, state, enabled=not args.sem_pytest)
        else:
            report.add("Testes adicionais", "PENDENTE", "Audit principal indisponivel; nao executar testes mutaveis")
    except Exception as exc:
        report.add("Inicializacao do executor", "FALHA", f"Erro: {error_type(exc)}")
    return finish(report, args)


def finish(report: Reporter, args) -> int:
    folder = Path(args.relatorios).expanduser() if args.relatorios else Path.home() / "GATI-relatorios"
    try:
        json_path, md_path = report.write(folder)
        print("\nRELATORIOS:")
        print(json_path)
        print(md_path)
    except Exception as exc:
        print("FALHA ao criar relatorios:", error_type(exc))
        return 2
    counts = {s: sum(x["resultado"] == s for x in report.entries)
              for s in ("APROVADO", "FALHA", "AVISO", "PENDENTE")}
    print("\nRESUMO:", counts)
    return 1 if counts["FALHA"] else 0


if __name__ == "__main__":
    sys.exit(main())
