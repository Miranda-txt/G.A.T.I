"""Standalone S3-shaped private object store capability spike, not GATI production code.

Exclusively injected clients; it never constructs SDK clients, connects to R2,
uses secrets, emits public links, or writes database metadata.
"""

import hashlib
import io
import re
import uuid
from typing import NamedTuple

from pypdf import PdfReader

MAX_OBJECT_BYTES = 25 * 1024 * 1024  # Provisional laboratory guard, not a PDF policy.
_KEY = re.compile(r"termos/[0-9a-f-]{36}/(?:original|final)/[0-9a-f-]{36}\.pdf\Z")


class StorageConflict(Exception):
    """Object exists with another intent or with content that cannot be reused."""


class StorageIntegrityError(Exception):
    """Stored bytes/metadata fail verification."""


class StorageUnavailable(Exception):
    """Remote storage unavailable; there is no proof that the artifact is ready."""


class StoredArtifact(NamedTuple):
    key: str
    sha256: str
    size_bytes: int
    mime: str
    write_id: str


def _error_code(exc):
    response = getattr(exc, "response", {})
    if isinstance(response, dict):
        error = response.get("Error", {})
        if isinstance(error, dict):
            return error.get("Code")
    return None


class StorageSpike:
    """Conditional PUT, exact byte verification, and fail-closed authenticated read.

    The injected S3-compatible client is assumed private. Public access policy,
    server-side authorization and database state are NOT implemented here.
    """

    def __init__(self, client, bucket):
        if not isinstance(bucket, str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{2,62}", bucket):
            raise ValueError("Invalid laboratory bucket")
        self._client = client
        self._bucket = bucket

    def _read_and_verify(self, ref):
        if not isinstance(ref, StoredArtifact) or not _KEY.fullmatch(ref.key):
            raise StorageIntegrityError("Invalid artifact reference")
        if not isinstance(ref.size_bytes, int) or not 1 <= ref.size_bytes <= MAX_OBJECT_BYTES:
            raise StorageIntegrityError("Invalid expected length")
        if not re.fullmatch(r"[0-9a-f]{64}", ref.sha256):
            raise StorageIntegrityError("Invalid expected checksum")
        try:
            head = self._client.head_object(Bucket=self._bucket, Key=ref.key)
        except Exception:
            raise StorageUnavailable("Artifact metadata unavailable") from None
        if (
            head.get("ContentLength") != ref.size_bytes
            or head.get("ContentType") != ref.mime
            or ref.mime != "application/pdf"
            or head.get("Metadata", {}).get("sha256") != ref.sha256
            or head.get("Metadata", {}).get("write-id") != ref.write_id
        ):
            raise StorageIntegrityError("Artifact metadata mismatch")
        try:
            result = self._client.get_object(Bucket=self._bucket, Key=ref.key)
        except Exception:
            raise StorageUnavailable("Artifact bytes unavailable") from None
        body = result["Body"]
        try:
            data = body.read(ref.size_bytes + 1)
        except Exception:
            raise StorageUnavailable("Unable to read complete artifact") from None
        finally:
            body.close()
        if len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256:
            raise StorageIntegrityError("Artifact bytes are corrupted")
        return data

    def _check_existing(self, ref):
        try:
            self._read_and_verify(ref)
        except StorageIntegrityError:
            # Existing object may have another intent; never overwrite it.
            raise StorageConflict("Existing object is not the intended artifact") from None
        return ref

    def put_once(self, issuance_id, artifact_id, kind, data, write_id):
        if any(type(x) is not uuid.UUID for x in (issuance_id, artifact_id, write_id)):
            raise ValueError("Only opaque UUID identifiers are allowed")
        if kind not in ("original", "final"):
            raise ValueError("Unknown artifact type")
        if not isinstance(data, bytes) or not 1 <= len(data) <= MAX_OBJECT_BYTES:
            raise ValueError("PDF bytes are missing or exceed the laboratory cap")
        if not data.startswith(b"%PDF-"):
            raise ValueError("Not a PDF")
        try:
            reader = PdfReader(io.BytesIO(data), strict=True)
            if reader.is_encrypted or not reader.pages:
                raise ValueError("Invalid PDF")
        except Exception:
            raise ValueError("Invalid PDF") from None
        key = f"termos/{issuance_id}/{kind}/{artifact_id}.pdf"
        digest = hashlib.sha256(data).hexdigest()
        ref = StoredArtifact(key, digest, len(data), "application/pdf", str(write_id))
        request = {
            "Bucket": self._bucket,
            "Key": key,
            "Body": data,
            "ContentType": "application/pdf",
            "CacheControl": "private, no-store",
            "Metadata": {"sha256": digest, "write-id": str(write_id)},
            "IfNoneMatch": "*",
        }
        # A network failure after commit is ambiguous. Retry with the SAME
        # conditional header + intent; never use an unconditional overwrite.
        for attempt in range(2):
            try:
                self._client.put_object(**request)
            except ConnectionError, TimeoutError:
                if attempt == 0:
                    continue
                raise StorageUnavailable("Write status unknown; reconcile manually") from None
            except Exception as exc:
                if _error_code(exc) in ("PreconditionFailed", "412"):
                    return self._check_existing(ref)
                raise StorageUnavailable("Conditional storage write failed") from None
            self._read_and_verify(ref)
            return ref
        raise StorageUnavailable("Write was not confirmed")

    def read_verified(self, ref, permit=None):
        # A server-side callback is required. Caller-provided booleans or
        # predicates from an external request are NOT an authorization API.
        try:
            authorized = callable(permit) and permit() is True
        except Exception:
            authorized = False
        if not authorized:
            raise PermissionError("Artifact not accessible")
        return self._read_and_verify(ref)
