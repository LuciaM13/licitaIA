FROM python:3.11-slim

LABEL org.opencontainers.image.title="LicitaIA" \
      org.opencontainers.image.description="Calculadora de presupuestos EMASESA" \
      org.opencontainers.image.source="https://github.com/LuciaM13/licitaIA"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias del sistema necesarias para compilar clipspy cuando PyPI no
# sirve wheel para la arquitectura del contenedor. Se purgan tras instalar
# los paquetes Python para mantener la imagen final pequeña.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Capa cacheable: solo se reconstruye si cambia requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia del código (app_licitaia.py, pages/, src/, data/, .streamlit/)
COPY . .

# Usuario no-root: propietario de /app para poder escribir en data/
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
