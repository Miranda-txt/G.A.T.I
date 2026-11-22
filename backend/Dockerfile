# Imagem de homologacao sem ClamAV e sem segredos de build.
FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# O requirements.lock e a fonte de versoes. Nenhuma migration roda durante o build.
COPY requirements.lock /app/requirements.lock
RUN python -m pip install --disable-pip-version-check -r requirements.lock \
    && python -m pip check

COPY . /app

# A configuracao de teste nao consulta o Neon na coleta de arquivos estaticos.
RUN GATI_ENV=test python manage.py collectstatic --noinput \
    && groupadd --system gati \
    && useradd --system --gid gati --home-dir /app --no-create-home gati \
    && mkdir -p /app/runtime \
    && chown -R gati:gati /app/runtime

USER gati

# A imagem nao contem segredos e exige variaveis externas para executar no Render.
ENV GATI_ENV=staging \
    DJANGO_SETTINGS_MODULE=config.settings.render

EXPOSE 10000

# Um worker e duas threads reduzem o consumo inicial de memoria no plano Free.
# A porta vem da variavel PORT disponibilizada pelo Render.
CMD ["sh", "-c", "exec python -m gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 2 --worker-class gthread --no-control-socket --timeout 60 --error-logfile -"]
