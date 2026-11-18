import io
import zipfile
from datetime import timedelta
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone
from openpyxl import Workbook
from PIL import Image

from gati.apps.arquivos.models import Arquivo
from gati.apps.arquivos.services import download_file, storage, upload_file
from gati.apps.ativos.models import Ativo
from gati.apps.importacoes.services import (
    HEADERS,
    cancel_import,
    confirm,
    preview,
    read_preview,
    temp_path,
)
from gati.apps.pessoas.models import Pessoa
from gati.common.errors import Conflict, ScannerUnavailable


def csv_file(rows, kind="pessoas"):
    text = ";".join(HEADERS[kind]) + "\n" + "\n".join(";".join(row) for row in rows)
    return SimpleUploadedFile("entrada.csv", text.encode("utf-8-sig"))


@pytest.fixture
def scanner(monkeypatch):
    monkeypatch.setattr("gati.common.clamav.scan", lambda path: None)


def test_preview_confirmation_atomicity_owner(domain, scanner):
    d = domain
    before = Pessoa.objects.count()
    upload = csv_file(
        [["Importada 1", "90000000789", "TI", "Cargo", ""], ["Importada 2", "90000000790", "TI", "Cargo", ""]]
    )
    job = preview(d.operator, "pessoas", upload)
    assert Pessoa.objects.count() == before and len(read_preview(d.operator, job)) == 2
    with pytest.raises(Conflict):
        read_preview(d.admin, job)
    confirm(d.operator, job)
    assert Pessoa.objects.count() == before + 2 and not temp_path(job).exists()
    confirm(d.operator, job)
    assert Pessoa.objects.count() == before + 2


def test_conflict_after_preview_rolls_back_entire_file(domain, scanner):
    d = domain
    before = Pessoa.objects.count()
    job = preview(
        d.operator,
        "pessoas",
        csv_file(
            [["Nova 1", "90000000789", "TI", "Cargo", ""], ["Nova 2", "90000000790", "TI", "Cargo", ""]]
        ),
    )
    Pessoa.objects.create(nome="Concorrente", documento="90000000790", departamento=d.department)
    with pytest.raises(ValidationError):
        confirm(d.operator, job)
    assert Pessoa.objects.count() == before + 1
    assert not Pessoa.objects.filter(documento="90000000789").exists()
    job.refresh_from_db()
    assert job.estado == "PREVIEW"


@pytest.mark.parametrize(
    "rows",
    [
        [["Dup", "90000000789", "TI", "Cargo", ""], ["Dup", "90000000789", "TI", "Cargo", ""]],
        [["Existe", "90000000123", "TI", "Cargo", ""]],
        [["Sem referência", "90000000789", "Inexistente", "Cargo", ""]],
        [["=EXEC()", "90000000789", "TI", "Cargo", ""]],
        [["Nome", "abc", "TI", "Cargo", ""]],
    ],
)
def test_import_invalid_rows_create_nothing(domain, scanner, rows):
    before = Pessoa.objects.count()
    with pytest.raises(ValidationError):
        preview(domain.operator, "pessoas", csv_file(rows))
    assert Pessoa.objects.count() == before


def test_asset_import_and_unknown_technical_columns(domain, scanner):
    d = domain
    job = preview(
        d.operator,
        "ativos",
        csv_file(
            [["TI-900", "TAG900", "SN900", "Notebook", "Modelo", "Estoque TI", "EM_ESTOQUE", "2027-01-01"]],
            kind="ativos",
        ),
    )
    confirm(d.operator, job)
    assert Ativo.objects.filter(patrimonio="TI-900").exists()
    with pytest.raises(ValidationError):
        preview(d.operator, "ativos", SimpleUploadedFile("a.csv", b"patrimonio;hostname\nA;host"))


def test_xlsx_safe_and_formula_rejected(domain, scanner):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(HEADERS["pessoas"])
    sheet.append(["Importada", "90000000789", "TI", "Cargo", ""])
    data = io.BytesIO()
    workbook.save(data)
    job = preview(domain.operator, "pessoas", SimpleUploadedFile("entrada.xlsx", data.getvalue()))
    cancel_import(domain.operator, job)
    sheet["A2"] = "=1+1"
    data = io.BytesIO()
    workbook.save(data)
    with pytest.raises(ValidationError):
        preview(domain.operator, "pessoas", SimpleUploadedFile("entrada.xlsx", data.getvalue()))


def test_xlsx_zip_expansion_and_macro_rejected(domain, scanner):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr("xl/vbaProject.bin", b"active")
    with pytest.raises(ValidationError):
        preview(domain.operator, "pessoas", SimpleUploadedFile("entrada.xlsx", data.getvalue()))


def test_expired_preview_cleanup(domain, scanner, django_capture_on_commit_callbacks):
    job = preview(domain.operator, "pessoas", csv_file([["Nome", "90000000789", "TI", "Cargo", ""]]))
    type(job).objects.filter(pk=job.pk).update(criado_em=timezone.now() - timedelta(hours=2))
    job.refresh_from_db()
    with pytest.raises(Conflict):
        confirm(domain.operator, job)
    with django_capture_on_commit_callbacks(execute=True):
        call_command("cleanup_temporarios")
    assert not temp_path(job).exists()


def png():
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "green").save(buffer, format="PNG")
    return buffer.getvalue()


def test_file_private_download_and_integrity(domain, scanner, client):
    d = domain
    obj = upload_file(d.operator, SimpleUploadedFile("evidencia.png", png()), d.asset)
    assert obj.tamanho > 0 and obj.sha256
    with download_file(d.operator, obj) as stream:
        assert stream.read() == png()
    assert client.get(f"/arquivos/{obj.pk}/download/").status_code == 302
    client.force_login(d.operator)
    response = client.get(f"/arquivos/{obj.pk}/download/")
    assert response.status_code == 200 and response["Content-Disposition"].startswith("attachment;")
    assert b"".join(response.streaming_content) == png()
    Path(storage().path(str(obj.storage_key))).write_bytes(b"corrupted")
    with pytest.raises(Conflict):
        download_file(d.operator, obj)


@pytest.mark.parametrize(
    "name,data", [("script.html", b"<script>"), ("fake.png", b"%PDF-bad"), ("empty.pdf", b"")]
)
def test_invalid_upload_blocked(domain, scanner, name, data):
    with pytest.raises(ValidationError):
        upload_file(domain.operator, SimpleUploadedFile(name, data), domain.asset)
    assert not Arquivo.objects.exists()


def test_scanner_failure_closed(domain, monkeypatch):
    def unavailable(path):
        raise ScannerUnavailable("Antivírus indisponível")

    monkeypatch.setattr("gati.common.clamav.scan", unavailable)
    with pytest.raises(ScannerUnavailable):
        upload_file(domain.operator, SimpleUploadedFile("a.png", png()), domain.asset)
    with pytest.raises(ScannerUnavailable):
        preview(domain.operator, "pessoas", csv_file([["Nome", "90000000789", "TI", "Cargo", ""]]))
    assert not Arquivo.objects.exists()


def test_malware_rejected(domain, monkeypatch):
    def malware(path):
        raise ValidationError("Malware")

    monkeypatch.setattr("gati.common.clamav.scan", malware)
    with pytest.raises(ValidationError):
        upload_file(domain.operator, SimpleUploadedFile("a.png", png()), domain.asset)
    assert not Arquivo.objects.exists()
