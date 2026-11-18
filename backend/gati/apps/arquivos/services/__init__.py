import hashlib
import re
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from PIL import Image
from pypdf import PdfReader

from gati.apps.auditoria.services import audit
from gati.apps.usuarios.permissions import authorize
from gati.common import clamav
from gati.common.errors import Conflict

from ..models import Arquivo


def storage():
    return FileSystemStorage(location=settings.RUNTIME / "private", base_url=None)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write_temp(upload, limit, area="quarantine"):
    directory = settings.RUNTIME / area
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / str(uuid.uuid4())
    size = 0
    try:
        with path.open("xb") as dest:
            for chunk in upload.chunks():
                size += len(chunk)
                if size > limit:
                    raise ValidationError("O arquivo excede o limite permitido.")
                dest.write(chunk)
        if not size:
            raise ValidationError("Arquivo vazio.")
        return path, size
    except Exception:
        path.unlink(missing_ok=True)
        raise


def mime_for(path, ext):
    try:
        if ext == ".pdf":
            if path.read_bytes()[:5] != b"%PDF-":
                raise ValueError()
            reader = PdfReader(path, strict=True)
            if reader.is_encrypted or not reader.pages:
                raise ValueError()
            return "application/pdf"
        with Image.open(path) as img:
            expected = "PNG" if ext == ".png" else "JPEG"
            if img.format != expected:
                raise ValueError()
            img.verify()
        return "image/png" if ext == ".png" else "image/jpeg"
    except Exception:
        raise ValidationError("O conteúdo não corresponde à extensão ou está corrompido.") from None


def upload_file(user, upload, target, ip=None):
    authorize(user)
    fields = {
        "ativos.ativo": "ativo_vinculado",
        "manutencoes.manutencao": "manutencao",
        "movimentacoes.processomovimentacao": "processo",
    }
    if target._meta.label_lower not in fields:
        raise ValidationError("Vínculo de arquivo inválido.")
    ext = Path(upload.name).suffix.lower()
    if ext not in {".pdf", ".png", ".jpg", ".jpeg"}:
        raise ValidationError("Envie PDF, JPG, JPEG ou PNG, com até 25 MiB.")
    path, size = write_temp(upload, 25 * 1024 * 1024)
    dest = None
    try:
        mime = mime_for(path, ext)
        checksum = sha(path)
        clamav.scan(path)
        key = uuid.uuid4()
        private = storage()
        Path(private.location).mkdir(parents=True, exist_ok=True)
        dest = Path(private.path(str(key)))
        with transaction.atomic():
            safe_name = re.sub(r"[^\w.() -]", "_", Path(upload.name).name)[:180] or "arquivo" + ext
            obj = Arquivo.objects.create(
                storage_key=key,
                nome_original=safe_name,
                mime=mime,
                tamanho=size,
                sha256=checksum,
                criado_por=user,
                **{fields[target._meta.label_lower]: target},
            )
            path.replace(dest)
            audit(user, "UPLOAD_ARQUIVO", obj, ip, {"sha256": checksum, "tamanho": size})
        return obj
    except Exception:
        if dest:
            dest.unlink(missing_ok=True)
        raise
    finally:
        path.unlink(missing_ok=True)


def download_file(user, obj, ip=None):
    authorize(user)
    if not obj.ativo:
        raise Conflict("Vínculo de arquivo inativo.")
    path = Path(storage().path(str(obj.storage_key)))
    if not path.is_file() or sha(path) != obj.sha256:
        raise Conflict("Arquivo indisponível ou integridade divergente.")
    audit(user, "DOWNLOAD_ARQUIVO", obj, ip)
    return path.open("rb")
