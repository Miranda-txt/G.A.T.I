"""Settings de homologacao para a borda HTTPS gerenciada pelo Render.

Nao utilizar em localhost ou em VPS com proxy diferente: os cabecalhos
encaminhados so podem ser confiados quando a borda os controla.
"""

import os

from django.core.exceptions import ImproperlyConfigured

from .staging import *  # noqa: F403

if not os.environ.get("RENDER_SERVICE_ID"):
    raise ImproperlyConfigured("Settings Render exigem a identificacao da plataforma Render.")
if os.environ.get("GATI_ENV") != "staging":
    raise ImproperlyConfigured("A imagem Render somente pode executar em homologacao.")
if os.environ.get("PGDATABASE") != "gati_homologacao" or os.environ.get("PGUSER") != "gati_app":
    raise ImproperlyConfigured("A aplicacao Render exige o banco e o usuario de menor privilegio.")
if not os.environ.get("PGHOST", "").lower().endswith(".neon.tech"):
    raise ImproperlyConfigured("A homologacao Render exige o hostname PostgreSQL remoto do Neon.")

# Render termina o TLS na borda, encaminha HTTP e sinaliza o esquema original.
# Validar em smoke test que a borda reescreve X-Forwarded-Proto recebido do cliente.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Evita HSTS permanente/preload na subdominio compartilhado onrender.com de staging.
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Nao gravar tokens de recuperacao ou assinatura no filesystem efemero do Render.
# E-mails reais serao ativados somente depois de integrar o provedor HTTPS.
EMAIL_BACKEND = "gati.common.email.FailClosedEmailBackend"
