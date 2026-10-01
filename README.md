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
uv run manage.py setup_code    # prints the code that claims the install
uv run manage.py runserver
```

Generate a `SECRET_KEY` with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

The app is on <http://localhost:8000> and the admin on
<http://localhost:8000/admin/> (configurable via `ADMIN_URL`).

A fresh install has no login. The server prints a setup code to its log at
start (`Setup code: …`, or run `manage.py setup_code`); the first visit asks
for it, then for the name, email and password of the install's only login,
then a passkey or an authenticator app, and finally shows 10 recovery codes
once. Passkeys work from the HTTPS URL in `CSRF_TRUSTED_ORIGINS` (or
`http://localhost:8000`); see `WEBAUTHN_ORIGINS` in `.env.example`.

Five wrong passwords or codes from one address pause signing in from it for an
hour; the login itself is never locked. Locked out with every passkey, the
authenticator and the recovery codes lost? On the server, run:

```bash
uv run manage.py break_glass --two-factor    # sign in by password, then set up anew
uv run manage.py break_glass --password      # prints a new password
```

Either signs out every device and lifts every pause. In Docker, run it with
`docker compose -f compose.prod.yaml exec web python manage.py break_glass …`.

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

Three long-running containers come up:

- `web` runs `runserver` against a bind mount of this directory, so code
  changes reload without a rebuild. Migrations run on every start.
- `postgres` holds the database, the same major version as prod, in the
  `pgdata` volume (`docker compose down -v` starts it afresh).
- `tailwind` watches the project and rebuilds `static/css/app.css` from
  `assets/css/app.css` whenever a template or source file changes.

`web` and `tailwind` run as your uid (`DOCKER_UID`/`DOCKER_GID`, default 1000),
so new migrations and the stylesheet stay editable on the host. If yours
differ (`id -u && id -g`), set them in `.env` and run `docker compose build`.
Dependencies are baked into the image, so rebuild after `uv add`.

```bash
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
- **Database:** the stack runs its own Postgres (pinned major version, no
  published port) with its data in the `pgdata` volume; back that up. Set
  `POSTGRES_PASSWORD` in `.env`; `DATABASE_URL` there is ignored.
- **TLS:** the container publishes on `127.0.0.1` only, for the host's reverse
  proxy to forward to. The app trusts the proxy's `X-Forwarded-Proto` and
  `X-Forwarded-For`, so the proxy must set both and strip any copy a client
  sent.
- **Headers:** HSTS for an hour (raise `SECURE_HSTS_SECONDS` to a year once
  HTTPS is verified; never preloaded), `X-Frame-Options: DENY`,
  `Referrer-Policy: same-origin`, and `X-Robots-Tag: noindex` on every
  response, with a `robots.txt` that disallows everything.
- **Files:** the app keeps nothing on disk; there is no media volume.
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
