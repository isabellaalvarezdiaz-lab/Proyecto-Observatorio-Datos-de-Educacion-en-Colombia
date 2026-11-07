# Imagen de la API. Se construye desde la RAÍZ del repositorio:
#   docker build -f backend/Dockerfile -t observatorio-api .
# Multi-stage: la etapa 1 instala dependencias en un entorno virtual; la etapa 2 copia solo ese
# entorno y el código, y corre como usuario sin privilegios. data/ (microdatos) nunca entra:
# está en .dockerignore y no hay ningún COPY que lo nombre.

FROM python:3.11.9-slim-bookworm AS dependencias
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv && /opt/venv/bin/pip install -r /tmp/requirements.txt

FROM python:3.11.9-slim-bookworm AS ejecucion
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENTORNO=produccion \
    DATABASE_URL=sqlite:////tmp/observatorio.db
RUN useradd --create-home --uid 10001 api
COPY --from=dependencias /opt/venv /opt/venv
WORKDIR /app
# Solo agregados y documentos: resultados por universidad, el modelo en JSON y los textos del asistente
COPY resultados/*.csv resultados/
COPY modelos/imputador_escrita.json modelos/
COPY README.md ./
COPY docs/*.md docs/informe_final.pdf docs/
COPY backend/app backend/app
USER api
WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/salud' % os.environ.get('PORT', '8000'))"
# Render inyecta $PORT; exec para que uvicorn reciba SIGTERM directamente
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
