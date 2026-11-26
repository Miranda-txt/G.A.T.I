"""R2/S3 capability proof in a disposable, credential-free in-memory fake."""

import hashlib
import io
import runpy
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from pypdf import PdfWriter

SPIKE = Path(__file__).parent / "fixtures" / "term_v2" / "storage_spike.py"


def _api():
    assert SPIKE.is_file(), "T01: adapter de storage privado ainda nao implementado"
    return runpy.run_path(str(SPIKE))


def _pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


class PreconditionFailed(Exception):
    response = {"Error": {"Code": "PreconditionFailed"}}


class RemoteUnavailable(ConnectionError):
    pass


class NotFound(Exception):
    response = {"Error": {"Code": "NoSuchKey"}}


class FakeR2:
    """Contract fake, not Cloudflare R2 or evidence of bucket configuration."""

    def __init__(self):
        self.objects = {}
        self.calls = []
        self.lock = threading.Lock()
        self.fail_before_put = 0
        self.fail_after_put = 0
        self.fail_get = False
        self.fail_head = False
        self.last_body = None

    def put_object(self, **kwargs):
        self.calls.append(("put_object", kwargs.copy()))
        with self.lock:
            if self.fail_before_put:
                self.fail_before_put -= 1
                raise RemoteUnavailable("connection lost")
            if kwargs["Key"] in self.objects:
                raise PreconditionFailed("412")
            if kwargs["IfNoneMatch"] != "*":
                raise AssertionError("write must be conditional")
            self.objects[kwargs["Key"]] = {
                "body": kwargs["Body"],
                "metadata": dict(kwargs["Metadata"]),
                "type": kwargs["ContentType"],
                "etag": '"untrusted-etag"',
            }
            if self.fail_after_put:
                self.fail_after_put -= 1
                raise RemoteUnavailable("response lost after commit")
        return {"ETag": '"untrusted-etag"'}

    def head_object(self, **kwargs):
        self.calls.append(("head_object", kwargs.copy()))
        if self.fail_head:
            raise RemoteUnavailable("head down")
        item = self.objects.get(kwargs["Key"])
        if item is None:
            raise NotFound("404")
        return {
            "ContentLength": len(item["body"]),
            "ContentType": item["type"],
            "Metadata": dict(item["metadata"]),
            "ETag": item["etag"],
        }

    def get_object(self, **kwargs):
        self.calls.append(("get_object", kwargs.copy()))
        if self.fail_get:
            raise RemoteUnavailable("get down")
        item = self.objects.get(kwargs["Key"])
        if item is None:
            raise NotFound("404")
        self.last_body = io.BytesIO(item["body"])
        return {"Body": self.last_body, "ContentLength": len(item["body"])}

    def anonymous_download(self, key):
        raise PermissionError("private fake bucket")


def _service(client=None):
    symbols = _api()
    return symbols["StorageSpike"](client or FakeR2(), "gati-t01-synthetic"), symbols


def _ids():
    return uuid.uuid4(), uuid.uuid4(), uuid.uuid4()


def test_storage_capability():
    api = _api()
    client = FakeR2()
    service = api["StorageSpike"](client, "gati-t01-synthetic")
    issuance, artifact, write = _ids()
    uploaded_bytes = _pdf()
    ref = service.put_once(issuance, artifact, "original", uploaded_bytes, write)
    downloaded_bytes = service.read_verified(ref, lambda: True)
    verified_hash = hashlib.sha256(downloaded_bytes).hexdigest()
    assert downloaded_bytes == uploaded_bytes
    assert verified_hash == ref.sha256
    assert ref.size_bytes == len(uploaded_bytes)
    assert ref.key == f"termos/{issuance}/original/{artifact}.pdf"
    with pytest.raises(PermissionError):
        client.anonymous_download(ref.key)
    assert client.last_body.closed
    assert client.objects[ref.key]["etag"] != ref.sha256


def test_storage_denies_unauthorized_before_remote_read():
    client = FakeR2()
    service, symbols = _service(client)
    issuance, artifact, write = _ids()
    ref = service.put_once(issuance, artifact, "original", _pdf(), write)
    before = len(client.calls)
    with pytest.raises(PermissionError):
        service.read_verified(ref, lambda: False)
    assert len(client.calls) == before
    with pytest.raises(PermissionError):
        service.read_verified(ref)
    assert len(client.calls) == before


def test_storage_enforces_no_overwrite_and_true_idempotency():
    client = FakeR2()
    service, symbols = _service(client)
    issuance, artifact, write = _ids()
    data = _pdf()
    ref = service.put_once(issuance, artifact, "original", data, write)
    same = service.put_once(issuance, artifact, "original", data, write)
    assert ref == same
    assert client.objects[ref.key]["body"] == data
    with pytest.raises(symbols["StorageConflict"]):
        service.put_once(issuance, artifact, "original", data, uuid.uuid4())
    with pytest.raises(symbols["StorageConflict"]):
        service.put_once(issuance, artifact, "original", data + b"mismatch", write)
    assert client.objects[ref.key]["body"] == data
    assert all(k[1]["IfNoneMatch"] == "*" for k in client.calls if k[0] == "put_object")
    assert all("ACL" not in args for _, args in client.calls)
    assert not hasattr(service, "presign_url")


def test_storage_two_writers_compete_atomically():
    client = FakeR2()
    service, symbols = _service(client)
    issuance, artifact, _ = _ids()
    data = _pdf()
    barrier = threading.Barrier(2)

    def write(_):
        barrier.wait(timeout=5)
        try:
            return service.put_once(issuance, artifact, "final", data, uuid.uuid4())
        except symbols["StorageConflict"]:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, range(2)))
    assert sum(x == "conflict" for x in results) == 1
    assert len(client.objects) == 1


def test_storage_corruption_detected_before_return():
    client = FakeR2()
    service, symbols = _service(client)
    issuance, artifact, write = _ids()
    ref = service.put_once(issuance, artifact, "original", _pdf(), write)
    original = client.objects[ref.key]["body"]
    client.objects[ref.key]["body"] = original[:-1] + bytes([original[-1] ^ 1])
    with pytest.raises(symbols["StorageIntegrityError"]):
        service.read_verified(ref, lambda: True)
    assert client.last_body.closed


@pytest.mark.parametrize("tamper", ["sha256", "write-id", "size", "mime"])
def test_storage_metadata_corruption_detected(tamper):
    client = FakeR2()
    service, symbols = _service(client)
    issuance, artifact, write = _ids()
    ref = service.put_once(issuance, artifact, "original", _pdf(), write)
    item = client.objects[ref.key]
    if tamper == "size":
        item["body"] = item["body"][:-4]
    elif tamper == "mime":
        item["type"] = "text/html"
    else:
        item["metadata"][tamper] = "wrong"
    with pytest.raises(symbols["StorageIntegrityError"]):
        service.read_verified(ref, lambda: True)


def test_storage_ambiguous_response_reconciles_without_overwrite():
    client = FakeR2()
    service, symbols = _service(client)
    issuance, artifact, write = _ids()
    client.fail_after_put = 1
    ref = service.put_once(issuance, artifact, "original", _pdf(), write)
    assert ref.key in client.objects
    assert sum(action == "put_object" for action, _ in client.calls) == 2
    assert service.read_verified(ref, lambda: True) == client.objects[ref.key]["body"]


def test_storage_failed_write_does_not_claim_availability():
    client = FakeR2()
    service, symbols = _service(client)
    client.fail_before_put = 2
    issuance, artifact, write = _ids()
    with pytest.raises(symbols["StorageUnavailable"]):
        service.put_once(issuance, artifact, "original", _pdf(), write)
    assert not client.objects


def test_storage_recovery_with_other_write_id_is_conflict():
    client = FakeR2()
    service, symbols = _service(client)
    issuance, artifact, write = _ids()
    service.put_once(issuance, artifact, "original", _pdf(), write)
    with pytest.raises(symbols["StorageConflict"]):
        service.put_once(issuance, artifact, "original", _pdf(), uuid.uuid4())


def test_storage_missing_or_unavailable_read_fails_closed():
    client = FakeR2()
    service, symbols = _service(client)
    issuance, artifact, write = _ids()
    ref = service.put_once(issuance, artifact, "original", _pdf(), write)
    original = client.objects.pop(ref.key)
    with pytest.raises(symbols["StorageUnavailable"]):
        service.read_verified(ref, lambda: True)
    client.objects[ref.key] = original
    client.fail_get = True
    with pytest.raises(symbols["StorageUnavailable"]):
        service.read_verified(ref, lambda: True)


@pytest.mark.parametrize("invalid", [b"", b"bad", b"%PDF", None, "str"])
def test_storage_rejects_invalid_pdf_data(invalid):
    service, symbols = _service()
    issuance, artifact, write = _ids()
    with pytest.raises(ValueError):
        service.put_once(issuance, artifact, "original", invalid, write)


@pytest.mark.parametrize("kind", ["", "../original", "image", "resource", None])
def test_storage_rejects_unapproved_kind(kind):
    service, symbols = _service()
    issuance, artifact, write = _ids()
    with pytest.raises(ValueError):
        service.put_once(issuance, artifact, kind, _pdf(), write)


def test_storage_rejects_non_uuid_identifier():
    service, symbols = _service()
    with pytest.raises(ValueError):
        service.put_once("person.name", uuid.uuid4(), "original", _pdf(), uuid.uuid4())
    with pytest.raises(ValueError):
        service.put_once(uuid.uuid4(), uuid.uuid4(), "original", _pdf(), "token")


def test_storage_scope_invalid_permission_result_fails_closed():
    client = FakeR2()
    service, symbols = _service(client)
    issuance, artifact, write = _ids()
    ref = service.put_once(issuance, artifact, "original", _pdf(), write)
    with pytest.raises(PermissionError):
        service.read_verified(ref, lambda: "true")
    with pytest.raises(PermissionError):
        service.read_verified(ref, lambda: (_ for _ in ()).throw(RuntimeError("auth offline")))


def test_storage_rejects_oversized_input_before_remote_write():
    client = FakeR2()
    service, symbols = _service(client)
    issuance, artifact, write = _ids()
    with pytest.raises(ValueError):
        service.put_once(issuance, artifact, "original", b"%PDF-" + b"x" * (25 * 1024 * 1024), write)
    assert not client.calls
