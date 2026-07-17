# ---- Frontend build stage: produces frontend/dist, served by app.frontend() ----
FROM node:22-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# ---- Backend stage ----
FROM python:3.11-slim-bookworm


COPY --from=ghcr.io/astral-sh/uv:0.5.24 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app


RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev


COPY . .
COPY --from=frontend-builder /frontend/dist ./frontend/dist


RUN chmod +x /app/entrypoint.sh && \
    sed -i 's/\r$//' /app/entrypoint.sh


ENTRYPOINT ["/app/entrypoint.sh"]
