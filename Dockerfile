ARG PYTHON_VERSION=3.13
ARG POETRY_VERSION=2.4.1

# Общая основа:
FROM python:${PYTHON_VERSION}-slim AS base
RUN groupadd -r -g 999 app && \
     useradd -r -u 999 -g app -s /usr/sbin/nologin app
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


# Сборщик для прода:
FROM python:${PYTHON_VERSION} AS prod-builder
ARG POETRY_VERSION
WORKDIR /app
# Переключаемся на Яндекс из-за блокировок
# (Этот RUN можно убрать, если проблем с сетью нет):
RUN sed -i 's/deb.debian.org/mirror.yandex.ru/g' /etc/apt/sources.list.d/debian.sources || \
    sed -i 's/deb.debian.org/mirror.yandex.ru/g' /etc/apt/sources.list
# Может понадобиться для asyncpg:
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_NO_INTERACTION=true
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root
COPY ./src ./src
# Нужно, чтобы в pyproject.toml [tool.poetry] работал packages:
RUN poetry install --only main


# Сборщик для тестов:
FROM python:${PYTHON_VERSION} AS test-builder
ARG POETRY_VERSION
WORKDIR /app
RUN sed -i 's/deb.debian.org/mirror.yandex.ru/g' /etc/apt/sources.list.d/debian.sources || \
    sed -i 's/deb.debian.org/mirror.yandex.ru/g' /etc/apt/sources.list
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}
ENV POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_NO_INTERACTION=1

COPY pyproject.toml poetry.lock ./
RUN poetry install --with test --no-root
COPY ./tests ./tests
COPY ./src ./src
RUN poetry install --with test


# Прод:
FROM base AS prod
COPY --from=prod-builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app ./alembic.ini ./
COPY --chown=app:app ./alembic ./alembic
COPY --chown=app:app ./scripts/runtime ./scripts/runtime
COPY --chown=app:app ./src ./src
COPY --chown=app:app ./pyproject.toml ./
RUN chmod +x ./scripts/runtime/*
USER app
ENTRYPOINT ["./scripts/runtime/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c "import socket; s = socket.socket(); s.connect(('127.0.0.1', 8000))" || exit 1


# Тест:
FROM base AS test
COPY --from=test-builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app ./alembic.ini ./
COPY --chown=app:app ./alembic ./alembic
COPY --chown=app:app ./scripts/runtime ./scripts/runtime
COPY --chown=app:app ./tests ./tests
COPY --chown=app:app ./src ./src
COPY --chown=app:app ./pyproject.toml ./
RUN chmod +x ./scripts/runtime/*
USER app
CMD ["pytest"]
