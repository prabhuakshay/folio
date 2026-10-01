#!/usr/bin/env sh
# Production entrypoint: bring the schema up to date, then hand over to the
# server. `exec` makes gunicorn PID 1 so it receives SIGTERM directly and shuts
# down cleanly.
set -eu

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
  # Creates the table a dbcache:// CACHE_URL needs; a no-op for other backends.
  python manage.py createcachetable
fi

# Until the install is claimed, the log carries the code that claims it.
python manage.py setup_code

exec "$@"
