# Stage 1: Build
FROM python:3.13-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ccache \
    clang \
    patchelf

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src src
RUN uv sync --frozen --no-editable

ENV CFLAGS="-Wno-macro-redefined"
RUN uv run python -m nuitka \
    --standalone \
    --clang \
    --python-flag=nosite,-O \
    --prefer-source-code \
    --output-dir=/app/build \
    --output-filename=dependency_cmp \
    src/dependency_cmp/main.py

# Stage 2: Runtime
FROM debian:bookworm-slim

COPY --from=k8s.gcr.io/kustomize/kustomize:v5.8.0 /app/kustomize /usr/local/bin/kustomize

COPY --from=builder /app/build/main.dist /opt/dependency_cmp
RUN ln -s /opt/dependency_cmp/dependency_cmp /usr/local/bin/dependency_cmp

USER 999
WORKDIR /app

COPY --chown=999:999 plugin.yaml /home/argocd/cmp-server/config/plugin.yaml

ENTRYPOINT ["/var/run/argocd/argocd-cmp-server"]