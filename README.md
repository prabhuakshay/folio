# folio

A Django project.

> **Work in progress.**

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL (optional — SQLite is used when `DATABASE_URL` is unset)
- Node.js, for building the Tailwind stylesheet (or use Docker)

## Setup (without Docker)

```bash
uv sync
cp .env.example .env         # then set SECRET_KEY (see below)
uv run prek install          # pre-commit and commit-msg hooks
npm install && npm run build   # or `npm run watch` while working
uv run manage.py migrate
uv run manage.py createsuperuser
uv run manage.py runserver
```

Generate a `SECRET_KEY` with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

The app is on <http://localhost:8000> and the admin on
<http://localhost:8000/admin/> (configurable via `ADMIN_URL`).

## Tests

```bash
uv run pytest
```

Tests need no `.env`: pytest supplies its own `SECRET_KEY`.

## Docker

### Development

```bash
cp .env.example .env         # then set SECRET_KEY and DEBUG=True
docker compose up --build
```

Two long-running containers come up:

- `web` runs `runserver` against a bind mount of this directory, so code
  changes reload without a rebuild. Migrations run on every start.
- `tailwind` watches the project and rebuilds `static/css/app.css` from
  `assets/css/app.css` whenever a template or source file changes.

Both run as your uid (`DOCKER_UID`/`DOCKER_GID`, default 1000), so the SQLite
file, new migrations and the stylesheet stay editable on the host. If yours
differ (`id -u && id -g`), set them in `.env` and run `docker compose build`.
Dependencies are baked into the image, so rebuild after `uv add`.

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py makemigrations
docker compose logs -f tailwind
```

### Production

```bash
docker compose -f compose.prod.yaml up -d --build
```

The prod image carries the virtualenv, the source and the collected static
files, and nothing else: no uv, no Node, no dev dependencies. It runs gunicorn
as an unprivileged user on a read-only filesystem with every capability
dropped. Migrations run on start (`RUN_MIGRATIONS`), then gunicorn takes over.

- **Static files** are compiled, hashed and Brotli/gzip-compressed at build
  time and served by WhiteNoise with far-future cache headers.
- **Database:** there is no database container, and SQLite can't work on the
  read-only filesystem. Point `DATABASE_URL` at Postgres; a server on the host
  is `host.docker.internal`.
- **TLS:** the container publishes on `127.0.0.1` only, for a reverse proxy on
  the host to forward to. Set `USE_X_FORWARDED_PROTO=True` if the proxy sets
  `X-Forwarded-Proto` (and strips any copy a client sent).
- **Health:** `/healthz` checks the database and backs the container
  healthcheck, which sends `Host: localhost`, so keep `localhost` in
  `ALLOWED_HOSTS`.
- **Tuning** (`WEB_CONCURRENCY`, `GUNICORN_*`, resource limits) is all in
  `.env`; changing it is a restart, not a rebuild.

## Configuration

All deployment-specific settings are read from environment variables, or from
a `.env` file at the project root. Every variable, its default and how to set
it is documented in [`.env.example`](.env.example). Only `SECRET_KEY` is
required; the defaults are production-safe, so set `DEBUG=True` for local
development.

Before deploying, audit the configuration with:

```bash
DEBUG=False uv run manage.py check --deploy
```

## Model history

[django-simple-history](https://django-simple-history.readthedocs.io/) is
installed, and its middleware records which user made each change. To track a
model, add a `HistoricalRecords` field and create a migration:

```python
from simple_history.models import HistoricalRecords


class Invoice(models.Model):
    history = HistoricalRecords()
```

## Linting and formatting

```bash
uv run ruff check .
uv run ruff format .
```

Ruff runs with `select = ["ALL"]` and Google-style docstrings; see
`[tool.ruff]` in [`pyproject.toml`](pyproject.toml) for the exceptions made
for Django.

## Git hooks

Hooks are managed by [prek](https://github.com/j178/prek) and configured in
[`.pre-commit-config.yaml`](.pre-commit-config.yaml). Run them over the whole
repo with `uv run prek run --all-files`. They enforce:

- Ruff linting and formatting
- `uv.lock` staying in sync with `pyproject.toml` — change dependencies with
  `uv add` / `uv remove`
- [Conventional Commits](https://www.conventionalcommits.org/) messages,
  e.g. `feat: add invoice model`
- No direct commits to `main` — work on a branch and merge via pull request
- Secret scanning (gitleaks), django-upgrade, djLint for templates, and
  general file hygiene checks

## License

[MIT](LICENSE)
