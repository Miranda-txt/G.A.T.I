"""Explicit worker entry point. No automatic startup or external provisioning."""

import signal
from threading import Event

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from gati.apps.termos.services import outbox


class Command(BaseCommand):
    help = "Processa tarefas internas de termos V2 quando explicitamente habilitado."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Processa no maximo uma tarefa e encerra.")

    def handle(self, *args, **options):
        if not outbox.enabled():
            raise CommandError("Modulo de termos V2 desabilitado")
        if not outbox.HANDLERS:
            raise CommandError("Nenhum handler de termos V2 homologado/registrado")
        poll = settings.GATI_TERM_OUTBOX_POLL_SECONDS
        if type(poll) is not int or not 1 <= poll <= 60:
            raise CommandError("Intervalo de polling invalido")
        stop = Event()

        def request_stop(_signal, _frame):
            stop.set()

        previous = {sig: signal.signal(sig, request_stop) for sig in (signal.SIGINT, signal.SIGTERM)}
        try:
            while not stop.is_set() and outbox.enabled():
                close_old_connections()
                processed = outbox.run_one(outbox.Clock.now())
                if options["once"]:
                    break
                if not processed:
                    stop.wait(poll)
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
            close_old_connections()
