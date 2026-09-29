"""Gunicorn configuration for the production image.

Every value that depends on the host is read from the environment, so tuning a
deployment is a restart, not a rebuild. Gunicorn itself also reads
`WEB_CONCURRENCY` (worker count) and `FORWARDED_ALLOW_IPS`.
"""

import os


def _int(name: str, default: int) -> int:
    # `or` also maps an empty override (`VAR=` in .env) back to the default.
    return int(os.environ.get(name) or default)


# Inside the container; compose publishes it on loopback only.
bind = "0.0.0.0:8000"

# Sync workers give true parallelism for CPU-bound Django work. Setting
# GUNICORN_THREADS above 1 switches gunicorn to threaded (gthread) workers,
# which suit I/O-heavy views; every thread holds its own DB connection.
workers = _int("WEB_CONCURRENCY", 2)
threads = _int("GUNICORN_THREADS", 1)

# Recycle workers so a slow leak can't grow without bound. The jitter stops them
# all restarting on the same request.
max_requests = _int("GUNICORN_MAX_REQUESTS", 1000)
max_requests_jitter = _int("GUNICORN_MAX_REQUESTS_JITTER", 100)

timeout = _int("GUNICORN_TIMEOUT", 30)
graceful_timeout = _int("GUNICORN_GRACEFUL_TIMEOUT", 30)
keepalive = _int("GUNICORN_KEEPALIVE", 5)

# Import Django once in the master and share it copy-on-write with the workers:
# less memory and faster worker boot.
preload_app = True

# The worker heartbeat must live on tmpfs: on the overlay filesystem a slow disk
# can make workers miss it and get killed.
worker_tmp_dir = "/dev/shm"  # noqa: S108

# The control socket defaults to a path under /app, which is read-only in prod.
control_socket_disable = True

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
