import csv
import io
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

from defusedxml.ElementTree import fromstring
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from openpyxl import load_workbook

from gati.apps.arquivos.services import sha, write_temp
from gati.apps.ativos.models import Ativo
from gati.apps.auditoria.services import audit
from gati.apps.cadastros.models import CategoriaAtivo, Departamento, Localizacao, StatusAtivo
from gati.apps.pessoas.models import Pessoa
from gati.apps.usuarios.permissions import authorize
from gati.common import clamav
from gati.common.catalog import check_references, save_record
from gati.common.errors import Conflict

from ..models import ImportacaoExecucao

HEADERS = {
    "pessoas": ["nome", "documento", "departamento", "cargo", "email"],
    "ativos": [
        "patrimonio",
        "service_tag",
        "numero_serie",
        "categoria",
        "modelo",
        "localizacao",
        "status_codigo",
        "garantia_fim",
    ],
}


def parse(path, kind, extension):
    if kind not in HEADERS:
        raise ValidationError("Entidade inválida.")
    if extension == ".csv":
        try:
            text = path.read_text(encoding="utf-8-sig")
            first = text.splitlines()[0]
            separators = [s for s in [";", ","] if next(csv.reader([first], delimiter=s)) == HEADERS[kind]]
            if len(separators) != 1:
                raise ValueError()
            rows = list(csv.reader(io.StringIO(text), delimiter=separators[0], strict=True))
        except ValueError, UnicodeError, csv.Error, IndexError:
            raise ValidationError("CSV inválido. Use UTF-8 e o cabeçalho do modelo oficial.") from None
    elif extension == ".xlsx":
        try:
            with zipfile.ZipFile(path) as z:
                if sum(i.file_size for i in z.infolist()) > 100 * 1024 * 1024 or len(z.infolist()) > 2000:
                    raise ValueError()
                for member in z.infolist():
                    name = member.filename.lower()
                    if any(
                        term in name for term in ["vbaproject", "externallinks/", "embeddings/", "activex/"]
                    ):
                        raise ValueError()
                    if name.endswith((".xml", ".rels")):
                        root = fromstring(z.read(member))
                        for node in root.iter():
                            if (
                                node.tag.split("}")[-1] in {"f", "externalLink"}
                                or node.attrib.get("TargetMode") == "External"
                            ):
                                raise ValueError()
            # O nome físico é UUID sem extensão; o parser recebe bytes, não o caminho.
            workbook = load_workbook(
                io.BytesIO(path.read_bytes()), read_only=True, data_only=False, keep_links=False
            )
            if len(workbook.worksheets) != 1:
                raise ValueError()
            sheet = workbook.active
            if sheet.max_row > 5001 or sheet.max_column != len(HEADERS[kind]):
                raise ValueError()
            rows = []
            for row in sheet.iter_rows():
                if any(c.data_type == "f" for c in row):
                    raise ValueError()
                rows.append([c.value if c.value is not None else "" for c in row])
            workbook.close()
        except Exception:
            raise ValidationError(
                "XLSX inválido: use uma planilha, até 5.000 linhas, sem fórmulas, macros ou links externos."
            ) from None
    else:
        raise ValidationError("Use CSV ou XLSX.")
    if not rows or rows[0] != HEADERS[kind] or len(rows) < 2 or len(rows) > 5001:
        raise ValidationError("Cabeçalho inválido ou quantidade fora do limite de 1 a 5.000 linhas.")
    result = []
    for index, row in enumerate(rows[1:], start=2):
        if len(row) != len(HEADERS[kind]):
            raise ValidationError(f"Linha {index}: quantidade de colunas inválida.")
        values = []
        for value in row:
            if isinstance(value, (date, datetime)):
                value = value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
            value = str(value).strip()
            if value.startswith(("=", "+", "-", "@")):
                raise ValidationError(f"Linha {index}: conteúdo ativo/fórmula não permitido.")
            values.append(value)
        result.append(dict(zip(HEADERS[kind], values)))
    return result


def reference(model, field, value):
    try:
        return model.objects.get(**{field: value, "ativo": True})
    except model.DoesNotExist, model.MultipleObjectsReturned:
        raise ValidationError("Referência inexistente, inativa ou ambígua; confira os catálogos.") from None


def validated(kind, rows):
    output = []
    seen = set()
    seen_tags = set()
    for number, row in enumerate(rows, 2):
        try:
            data = dict(row)
            if kind == "pessoas":
                model = Pessoa
                data["departamento"] = reference(Departamento, "nome", row["departamento"])
                if not row["documento"].isdigit() or len(row["documento"]) < 4:
                    raise ValidationError("Documento deve conter de 4 a 32 dígitos.")
                key = row["documento"]
                exists = Pessoa.objects.filter(documento=key).exists()
            else:
                model = Ativo
                data["categoria"] = reference(CategoriaAtivo, "nome", row["categoria"])
                data["localizacao"] = reference(Localizacao, "nome", row["localizacao"])
                data["status"] = reference(StatusAtivo, "codigo", data.pop("status_codigo"))
                data["garantia_fim"] = (
                    date.fromisoformat(row["garantia_fim"]) if row["garantia_fim"] else None
                )
                data["patrimonio"] = row["patrimonio"].upper()
                data["service_tag"] = row["service_tag"].upper()
                key = data["patrimonio"]
                exists = Ativo.objects.filter(patrimonio__iexact=key).exists()
                tag = data["service_tag"]
                if tag and (tag in seen_tags or Ativo.objects.filter(service_tag__iexact=tag).exists()):
                    raise ValidationError("Service Tag duplicada, inclusive entre inativos.")
                seen_tags.add(tag)
            if key in seen or exists:
                raise ValidationError("Registro duplicado, existente ou inativo. A importação somente cria.")
            seen.add(key)
            obj = model(**data)
            check_references(obj)
            obj.full_clean()
            output.append(data)
        except (ValidationError, ValueError) as error:
            message = (
                "; ".join(error.messages)
                if isinstance(error, ValidationError)
                else "Data inválida; use AAAA-MM-DD."
            )
            raise ValidationError(f"Linha {number}: {message}") from None
    return output


def temp_path(job):
    return settings.RUNTIME / "imports" / str(job.pk)


def preview(user, kind, upload, ip=None):
    authorize(user)
    ext = Path(upload.name).suffix.lower()
    if ext not in {".csv", ".xlsx"}:
        raise ValidationError("Use CSV ou XLSX.")
    path, size = write_temp(upload, 10 * 1024 * 1024)
    try:
        clamav.scan(path)
        rows = parse(path, kind, ext)
        validated(kind, rows)
        with transaction.atomic():
            job = ImportacaoExecucao.objects.create(
                usuario=user, entidade=kind, formato=ext, sha256=sha(path), tamanho=size, quantidade=len(rows)
            )
            target = temp_path(job)
            target.parent.mkdir(parents=True, exist_ok=True)
            path.replace(target)
            audit(user, "PREVIEW_IMPORTACAO", job, ip, {"quantidade": len(rows)})
        return job
    finally:
        path.unlink(missing_ok=True)


def read_preview(user, job):
    authorize(user)
    if (
        job.usuario_id != user.pk
        or job.estado != "PREVIEW"
        or timezone.now() - job.criado_em > timedelta(hours=1)
    ):
        raise Conflict("Prévia indisponível ou expirada.")
    path = temp_path(job)
    if not path.exists() or sha(path) != job.sha256:
        raise Conflict("Arquivo temporário indisponível ou alterado.")
    return parse(path, job.entidade, job.formato)


def confirm(user, job, ip=None):
    authorize(user)
    try:
        with transaction.atomic():
            job = ImportacaoExecucao.objects.select_for_update().get(pk=job.pk)
            if job.usuario_id != user.pk:
                raise Conflict("Importação pertence a outro usuário.")
            if job.estado == "CONCLUIDA":
                return job
            rows = read_preview(user, job)
            data = validated(job.entidade, rows)
            model = Pessoa if job.entidade == "pessoas" else Ativo
            # Cada criação usa o serviço do domínio; conflito faz rollback de todo o lote.
            for values in data:
                save_record(user, model, values, ip=ip, audit_record=False)
            job.estado = "CONCLUIDA"
            job.concluido_em = timezone.now()
            job.save()
            audit(user, "CONCLUIR_IMPORTACAO", job, ip, {"quantidade": job.quantidade, "sha256": job.sha256})
        temp_path(job).unlink(missing_ok=True)
        return job
    except IntegrityError:
        raise Conflict("Conflito concorrente. Nenhum registro do lote foi criado.") from None


@transaction.atomic
def cancel_import(user, job, ip=None):
    authorize(user)
    job = ImportacaoExecucao.objects.select_for_update().get(pk=job.pk)
    if job.usuario_id != user.pk or job.estado != "PREVIEW":
        raise Conflict("Não é possível cancelar esta importação.")
    job.estado = "CANCELADA"
    job.concluido_em = timezone.now()
    job.save()
    transaction.on_commit(lambda: temp_path(job).unlink(missing_ok=True))
    audit(user, "CANCELAR_IMPORTACAO", job, ip)
