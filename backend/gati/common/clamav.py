import socket
import struct

from django.conf import settings
from django.core.exceptions import ValidationError

from gati.common.errors import ScannerUnavailable


def scan(path):
    try:
        with socket.create_connection(
            (settings.CLAMAV_HOST, settings.CLAMAV_PORT), settings.CLAMAV_TIMEOUT
        ) as conn:
            conn.settimeout(settings.CLAMAV_TIMEOUT)
            conn.sendall(b"zINSTREAM\0")
            with open(path, "rb") as stream:
                while chunk := stream.read(65536):
                    conn.sendall(struct.pack("!I", len(chunk)) + chunk)
            conn.sendall(struct.pack("!I", 0))
            reply = b""
            while len(reply) < 4096 and not reply.endswith(b"\0"):
                part = conn.recv(4096)
                if not part:
                    break
                reply += part
    except OSError:
        raise ScannerUnavailable(
            "Antivírus indisponível. Nenhum arquivo foi disponibilizado; tente novamente após restabelecer o ClamAV."
        ) from None
    if b"FOUND" in reply:
        raise ValidationError("Arquivo rejeitado pelo antivírus.")
    if reply.strip(b"\0\n ") != b"stream: OK":
        raise ScannerUnavailable("Não foi possível confirmar a segurança do arquivo.")
