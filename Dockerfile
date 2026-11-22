# syntax=docker/dockerfile:1
ARG PYTHON_IMAGE=python:3.11-slim-bookworm
FROM ${PYTHON_IMAGE} AS dependencias
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
COPY requirements.txt ./
# Variante CPU de la misma versión; evita descargar CUDA en un servidor sin GPU.
RUN python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.15.0+cpu \
    && python -m pip install -r requirements.txt \
    && python -m pip check

FROM ${PYTHON_IMAGE} AS aplicacion
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 libgomp1 libstdc++6 ca-certificates tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 aula && useradd --uid 10001 --gid aula --no-create-home aula \
    && mkdir -p /app/.local /app/.streamlit && chown aula:aula /app/.local
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/tmp \
    XDG_CACHE_HOME=/tmp/cache NUMBA_CACHE_DIR=/tmp/numba \
    OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
COPY --from=dependencias /app/.venv /app/.venv
COPY principal.py requirements.txt ./
COPY .streamlit/config.toml ./.streamlit/config.toml
COPY src ./src
COPY scripts ./scripts
COPY sql ./sql
COPY static ./static
USER 10001:10001
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3).read()"
ENTRYPOINT ["/usr/bin/tini", "--", "python", "scripts/iniciar_produccion.py"]
