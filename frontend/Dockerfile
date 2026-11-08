# Tablero. Desde la raíz del repositorio: docker build -f frontend/Dockerfile -t observatorio-tablero .
FROM python:3.11.9-slim-bookworm
ENV PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 tablero
COPY frontend/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
WORKDIR /app
COPY frontend/app.py frontend/cliente.py ./
USER tablero
EXPOSE 8501
# Render inyecta $PORT; en local se usa 8501
CMD ["sh", "-c", "exec streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true"]
