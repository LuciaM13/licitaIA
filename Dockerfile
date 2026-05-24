FROM python:3.11-slim

LABEL org.opencontainers.image.title="LicitaIA" \
      org.opencontainers.image.description="Calculadora de presupuestos EMASESA"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build deps para compilar clipspy si PyPI no tiene wheel para la arquitectura.
# Se purgan al final para mantener la imagen ligera.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Capa cacheable: solo se reconstruye si cambia requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Codigo de la app (solo lo que la Streamlit usa en runtime).
COPY app_licitaia.py ./
COPY pages/ ./pages/
COPY .streamlit/ ./.streamlit/

# Modulos src/ usados por la app. validacion_proyectos/ queda fuera: solo lo
# usan tests y el notebook TFG, no la UI.
COPY src/__init__.py ./src/
COPY src/almacenamiento/ ./src/almacenamiento/
COPY src/catalogo/ ./src/catalogo/
COPY src/exportar/ ./src/exportar/
COPY src/modelo/ ./src/modelo/
COPY src/presupuesto/ ./src/presupuesto/
COPY src/sistema_experto/ ./src/sistema_experto/
COPY src/soporte/ ./src/soporte/
COPY src/ui/ ./src/ui/

# Datos minimos para que la app arranque (BD + catalogo + logo).
COPY data/precios.db data/catalogo_oficial.json ./data/
COPY data/static/ ./data/static/

# Usuario no-root con propiedad de /app (la app escribe en data/ al guardar
# presupuestos en historial y al editar catalogo).
RUN useradd --create-home --shell /bin/bash licitaia \
    && chown -R licitaia:licitaia /app
USER licitaia

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').status==200 else 1)"

CMD ["streamlit", "run", "app_licitaia.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
