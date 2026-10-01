# syntax=docker/dockerfile:1
#
# One multi-stage build, two targets:
#   --target dev   autoreloading runserver with dev tooling   (compose.yaml)
#   --target prod  gunicorn on a lean, read-only-friendly image (compose.prod.yaml)
#
# Layers run cheap to expensive, so the slow dependency install stays cached
# until uv.lock or package-lock.json actually change.

ARG PYTHON_VERSION=3.14
ARG NODE_VERSION=25

FROM ghcr.io/astral-sh/uv:0.12.19 AS uv

# ────────────────────────── supercronic ──────────────────────────
# The cron service's scheduler: one static binary per architecture, each pinned
# by checksum. Only the target architecture's stage is built.
FROM scratch AS supercronic-amd64
ADD --checksum=sha256:a53ae236602c7338aba3fbaff40bda6300eae3b9fedb8261eb06cfe3724430c1 --chmod=755 \
    https://github.com/aptible/supercronic/releases/download/v0.2.49/supercronic-linux-amd64 /supercronic

FROM scratch AS supercronic-arm64
ADD --checksum=sha256:02aa0cb229ba09050cba6638059dadb9eedc2276632ea43d6a57a2f8c1629dd5 --chmod=755 \
    https://github.com/aptible/supercronic/releases/download/v0.2.49/supercronic-linux-arm64 /supercronic

FROM supercronic-${TARGETARCH} AS supercronic

# ───────────────────────────── base ──────────────────────────────
# Shared by every Python stage, including prod, so it holds only what the
# runtime needs: no uv, no compilers.
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Outside /app so the dev bind mount over /app can't shadow it.
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

RUN groupadd --system --gid 1001 folio \
 && useradd --system --uid 1001 --gid folio --home-dir /app folio

COPY --from=supercronic /supercronic /usr/local/bin/supercronic

# ─────────────────────────── tailwind ────────────────────────────
# The dev watcher and nothing else. package.json arrives over compose's bind
# mount and is installed on start, so a dependency change needs no rebuild.
#
# It writes into your working tree, so it runs as your uid: a root-owned
# stylesheet can't be touched by your editor or git without sudo. compose masks
# /app/node_modules with an anonymous volume seeded from this image, ownership
# included, which is why the directory must already exist here owned by that uid.
FROM node:${NODE_VERSION}-slim AS tailwind
ARG DOCKER_UID=1000
ARG DOCKER_GID=1000
WORKDIR /app
RUN mkdir -p /app/node_modules && chown -R ${DOCKER_UID}:${DOCKER_GID} /app
CMD ["npm", "run", "watch"]

# ──────────────────────────── assets ─────────────────────────────
# Compiles the stylesheet once for prod. Node is a build dependency only; prod
# copies the output and never sees npm.
FROM node:${NODE_VERSION}-slim AS assets
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund
# The whole tree, not selected folders: Tailwind only emits the classes it finds,
# and a directory left out fails silently as unstyled pages.
COPY . .
RUN npm run build

# ───────────────────────────── deps ──────────────────────────────
# The venv from the lockfile alone, before any source is copied, so editing
# code never reinstalls dependencies. The project is run from /app, not
# installed as a package, hence --no-install-project.
FROM base AS deps
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy \
    # Precompile the venv so the first request pays no import-compile cost.
    UV_COMPILE_BYTECODE=1 \
    # The base image already is the Python to use.
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# ───────────────────────────── dev ───────────────────────────────
# compose bind-mounts the source over /app, so edits reload through Django's
# autoreloader without a rebuild; the venv in /opt/venv is untouched by that.
FROM deps AS dev
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project
COPY . .
# compose runs this as your uid, which has no passwd entry and so no home;
# `manage.py shell` wants one for its history.
ENV HOME=/tmp
USER folio
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ──────────────────────────── build ──────────────────────────────
# Bakes hashed, compressed static files into the image (WhiteNoise serves them
# from STATIC_ROOT at runtime) and precompiles the app's bytecode, since the prod
# filesystem is read-only and couldn't cache it, then drops build-only files.
# The throwaway SECRET_KEY only satisfies the settings import and is not kept in
# any layer.
FROM deps AS build
COPY . .
COPY --from=assets /app/static/css/app.css static/css/app.css
RUN SECRET_KEY=build-only python manage.py collectstatic --noinput --clear \
 && python -m compileall -q -j 0 /app \
 && rm -rf assets package.json package-lock.json Dockerfile compose*.yaml

# ───────────────────────────── prod ──────────────────────────────
# Just the runtime: base, the venv and the app. Everything stays root-owned so
# the unprivileged user can read the code but never change it; the app keeps
# nothing on disk.
FROM base AS prod
COPY --from=build /opt/venv /opt/venv
COPY --from=build /app /app

USER folio
EXPOSE 8000

# Sends Host: localhost, so ALLOWED_HOSTS must include localhost.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request as u; r = u.Request('http://127.0.0.1:8000/healthz', headers={'Host': 'localhost'}); sys.exit(u.urlopen(r, timeout=3).status != 200)"]

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--config", "gunicorn.conf.py"]
