# =============================================================
# Aegis Backend — Multi-stage Dockerfile
# Designed and Developed by NIKHIL CHARY SRIRAMOJU
# =============================================================

FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runtime
LABEL maintainer="Nikhil Chary Sriramoju" \
      org.opencontainers.image.title="Aegis Agentic Platform - Backend" \
      org.opencontainers.image.authors="Nikhil Chary Sriramoju"

RUN apt-get update && apt-get install -y --no-install-recommends docker.io curl && rm -rf /var/lib/apt/lists/* \
    && addgroup --system aegis && adduser --system --ingroup aegis aegis

WORKDIR /app
COPY --from=builder /root/.local /home/aegis/.local
COPY app ./app
COPY workers ./workers

ENV PATH=/home/aegis/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN chown -R aegis:aegis /app
USER aegis

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
