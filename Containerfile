FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=k8s.gcr.io/kustomize/kustomize:v5.8.0 /app/kustomize /usr/local/bin/kustomize

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    PYTHONUNBUFFERED=1

USER 999
WORKDIR /app

COPY --chown=999:999 pyproject.toml uv.lock ./
COPY --chown=999:999 src src
COPY --chown=999:999 plugin.yaml /home/argocd/cmp-server/config/plugin.yaml

RUN uv sync --frozen --no-dev --no-editable

ENTRYPOINT ["/usr/local/bin/argocd-cmp-server"]