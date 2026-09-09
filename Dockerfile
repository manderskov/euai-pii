FROM python:3.12.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    XDG_CACHE_HOME=/tmp/.cache

RUN addgroup --system --gid 10001 euai \
    && adduser --system --uid 10001 --ingroup euai --home /nonexistent --no-create-home euai

WORKDIR /app
COPY requirements.lock pyproject.toml README.md ./
RUN python -m pip install --upgrade pip==26.2.1 \
    && python -m pip install -r requirements.lock

COPY src ./src
COPY config ./config

RUN python -m pip install --no-deps . \
    && chown -R euai:euai /app

USER 10001:10001
ENV SCREENING_PORT=8080 \
    SCREENING_CONFIG_PATH=/run/config/screening.json \
    SCREENING_CREDENTIALS_PATH=/run/secrets/screening-clients.json

EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=6 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health/ready', timeout=2)"

CMD ["uvicorn", "euai_pii.api:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
