# folio

A Django project.

> **Work in progress.**

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL (optional — SQLite is used when `DATABASE_URL` is unset)

## Setup

```bash
uv sync
cp .env.example .env         # then set SECRET_KEY (see below)
uv run prek install          # pre-commit and commit-msg hooks
uv run manage.py migrate
uv run manage.py createsuperuser
uv run manage.py runserver
```

Generate a `SECRET_KEY` with:

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

The app is on <http://localhost:8000> and the admin on
<http://localhost:8000/admin/> (configurable via `ADMIN_URL`).

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
