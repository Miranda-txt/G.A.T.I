import io
import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from gati.apps.arquivos.services import download_file, upload_file
from gati.apps.importacoes.services import confirm, preview
from gati.apps.pessoas.models import Pessoa

pytestmark = pytest.mark.skipif(
    os.environ.get("GATI_TEST_CLAMAV") != "1", reason="Smoke opcional: exige ClamAV real em loopback"
)


def test_real_antivirus_file_roundtrip(domain):
    data = io.BytesIO()
    Image.new("RGB", (24, 24), "green").save(data, format="PNG")
    obj = upload_file(
        domain.operator, SimpleUploadedFile("evidencia-sintetica.png", data.getvalue()), domain.asset
    )
    with download_file(domain.operator, obj) as stream:
        assert stream.read() == data.getvalue()


def test_real_antivirus_import(domain):
    data = b"nome;documento;departamento;cargo;email\nPessoa teste AV;90000000999;TI;Analista;\n"
    job = preview(domain.operator, "pessoas", SimpleUploadedFile("teste.csv", data))
    confirm(domain.operator, job)
    assert Pessoa.objects.filter(documento="90000000999").exists()
