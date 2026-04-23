# syntax=docker/dockerfile:1.7

FROM python:3.12-slim-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_PREFERENCE=only-system \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --extra aws --locked --no-dev --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --extra aws --locked --no-dev


FROM python:3.12-slim-bookworm AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}" \
    PLAYWRIGHT_BROWSERS_PATH=/usr/bin \
    CHROME_PATH=/usr/bin/chromium \
    CHROMIUM_PATH=/usr/bin/chromium

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        chromium \
        curl \
        fonts-dejavu-core \
        fonts-freefont-ttf \
        fonts-liberation \
        fonts-noto-core \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system utw \
    && useradd --system --create-home --gid utw utw \
    && mkdir -p /app /tmp/utw \
    && chown -R utw:utw /app /tmp/utw

COPY --from=builder /app /app

USER utw

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
