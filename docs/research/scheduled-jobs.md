# Scheduled jobs for Django 6 in Docker

Research for [#6](https://github.com/prabhuakshay/folio/issues/6) (map: [#1](https://github.com/prabhuakshay/folio/issues/1)). Researched 2026-09-30 against Django 6.1.1 (the version in `uv.lock`).

**Question:** what is the simplest robust way to run scheduled background work (daily price fetches, recurring-payment posting, reminders) in Folio's existing Docker compose stack?

This note gathers facts and trade-offs. It does not make the decision.

## TL;DR

- **`django.tasks` does not schedule anything, and it does not run anything in production.** Django ships a task *API* only. Its two built-in backends are for development and testing. It has no periodic or cron support. `run_after` only sets a one-off earliest start time. Django 6.1 added nothing on these fronts.
- To run `django.tasks` work in production you need a third-party backend with a worker, for example `django-tasks-db` (`manage.py db_worker`). To make it periodic you need yet another package, for example `django-crontask`, which runs an APScheduler process that enqueues tasks.
- **A supercronic sidecar calling management commands** is the lightest option that schedules. It adds no Python dependencies, no new tables and no broker. It needs one static binary in the image and one extra compose service. It has no retries and no catch-up.
- **django-q2 with the ORM broker** gives you a scheduler, a worker, retries, catch-up and an admin view of failures in one process, with no broker. It uses its own API rather than `django.tasks`, and it pickles task payloads.
- **Celery** needs a broker (Redis or RabbitMQ) plus separate worker and beat processes. That is too heavy for a single-user VPS.
- **None of these runners catches up after downtime in a way you can rely on, except django-q2.** Whatever runner is chosen, jobs should be **date-driven and idempotent**. A job should work out from the database what is due since its last success, rather than assuming it runs exactly once per tick.
- **The facts favour a supercronic sidecar running idempotent management commands** for the three named workloads. `django.tasks` plus `django-tasks-db` is worth adding later, and only if Folio needs background work *triggered by requests* (for example parsing a large CAS import off the request path).

## Constraints from this repo

| Constraint | Source | Consequence for a job runner |
|---|---|---|
| Prod root filesystem is read-only; only `/tmp` (tmpfs) and `/app/media` (volume) are writable | `compose.prod.yaml` (`read_only: true`, `tmpfs: [/tmp]`, `volumes: media`) | Anything that writes a state file (Celery beat's `celerybeat-schedule`, pid files) must point at `/tmp`, which does not survive a restart. Scheduler state should live in Postgres. |
| Runs as unprivileged `folio` (uid 1001), `cap_drop: ALL`, `no-new-privileges` | `Dockerfile` (`USER folio`), `compose.prod.yaml` | Classic Debian `cron` expects to run as root and `setuid` to users, so it is out. supercronic, `db_worker`, `qcluster` and `crontask` all run as an ordinary user. |
| Image `HEALTHCHECK` probes `http://127.0.0.1:8000/healthz` | `Dockerfile` | A sidecar built from the same image inherits this probe. It serves nothing on :8000, so Docker would mark it `unhealthy`. The sidecar needs `healthcheck: {disable: true}` or its own test. |
| `ENTRYPOINT` runs `migrate` and `createcachetable` unless `RUN_MIGRATIONS=0` | `docker/entrypoint.sh` | A second service from the same image would race the web container on migrations. It should set `RUN_MIGRATIONS=0`. `.env.example` already documents this knob for replicas. |
| `ENTRYPOINT` `exec`s the command | `docker/entrypoint.sh` | The runner becomes PID 1 and receives SIGTERM directly. supercronic reaps zombie processes only when it is PID 1 (`-no-reap` flag help text), and here it would be. |
| Web container memory cap 768M; the notes put each gunicorn worker at about 100 MB | `compose.prod.yaml`, `.env.example` | Every extra long-running Django process (worker or scheduler) costs roughly one more worker's memory. A cron-invoked command pays a cold Django import on each run instead of holding memory between runs. |
| Default `CACHE_URL` is `locmemcache://` (per process) | `config/settings.py`, `.env.example` | django-q2's monitoring (`qinfo` / `qmonitor`) needs a shared cache. The ORM broker docs say it "Needs Django's Cache framework configured for monitoring". `dbcache://` would work, and the entrypoint already runs `createcachetable`. |
| Prod uses Postgres; dev defaults to SQLite | `compose.prod.yaml`, `.env.example` | A Postgres-only runner (Procrastinate) would not work in the default dev stack. `django-tasks-db` and django-q2's ORM broker work on both. |
| Base image is Debian 13 (trixie) `python:3.14-slim` and includes `/usr/share/zoneinfo` | verified with `docker run python:3.14-slim` | supercronic's `TZ` / `CRON_TZ` and APScheduler/Django timezones can use `Asia/Kolkata` without adding tzdata. `TIME_ZONE` currently defaults to `UTC`. |

## Option 1: Django's built-in tasks framework (`django.tasks`)

**What Django provides** ([Tasks topic, 6.1](https://docs.djangoproject.com/en/6.1/topics/tasks/)):

- "It does not provide a worker mechanism to run Tasks. The actual execution must be handled by infrastructure outside Django, such as a separate process or service."
- "Django comes with built-in backends, but these are for development and testing only." / "Production systems should rely on backends that supply a worker process and a durable queue implementation."
- The only built-in backends are `ImmediateBackend` (runs in the calling thread) and `DummyBackend` (stores the task and never runs it). Source: `django/tasks/backends/{immediate,dummy}.py` in 6.1.1.

**Scheduling:** none. The `Task` dataclass has `run_after: datetime | None  # The earliest this Task will run.` The `@task` decorator refuses it statically: `"run_after cannot be defined statically with the @task decorator. Use .using(run_after=...) to set it dynamically."` (`django/tasks/base.py`, 6.1.1). That is a one-shot deferral. There is no cron, interval or recurrence concept anywhere in `django/tasks/`. A backend opts into deferral with `supports_defer`, which `ImmediateBackend` does not set.

**Retries:** none in the API. `TaskResult.attempts` is `len(self.worker_ids)`. There is no retry policy field on `Task`.

**6.1 changes** ([release notes](https://docs.djangoproject.com/en/6.1/releases/6.1/)): `@task` now forwards `**kwargs` to the backend's `task_class`, and `Task`/`TaskResult` can be pickled. Nothing on scheduling, retries or new backends.

**Other things to know:** enqueue from inside a transaction with `transaction.on_commit(partial(task.enqueue, ...))`, otherwise the task may run before its data is committed (topic docs). Signals `task_enqueued`, `task_started` and `task_finished` exist (`django/tasks/signals.py`).

### 1a. `django-tasks-db`: database backend and worker

[django-tasks-db](https://github.com/RealOrangeOne/django-tasks-db) is listed on Django's [community ecosystem page](https://www.djangoproject.com/community/ecosystem/). Since django-tasks 0.12.0 the DB and RQ backends ship as separate packages ([django-tasks README](https://github.com/RealOrangeOne/django-tasks)). Facts below come from the 0.13.0 sdist (released 2026-08-28):

- Setup: `"django_tasks_db"` in `INSTALLED_APPS`, `BACKEND: "django_tasks_db.DatabaseBackend"`. It adds its own migrations (one results table).
- Backend flags: `supports_defer`, `supports_priority`, `supports_get_result` and `supports_async_task` are all `True` (`backend.py`).
- Worker: `manage.py db_worker` with `--queue-name`, `--exclude-queues`, `--interval` (default **1 s** poll when idle), `--batch` ("Process all outstanding tasks, then exit"), `--max-tasks`, `--reload` (defaults to `DEBUG`; "Not recommended for production"), `--no-startup-delay` and `--worker-id` (`management/commands/db_worker.py`).
- Locking: `select_for_update(skip_locked=True)` on Postgres. On SQLite it uses an `EXCLUSIVE` transaction (`models.py`, `utils.py`).
- Shutdown: on SIGTERM/SIGINT/SIGQUIT it finishes the current task and then exits. A second signal kills the task with `sys.exit(1)`.
- **Retries: none.** The `retry` decorator in `utils.py` only retries the worker's own DB calls on `OperationalError`. A task that raises is marked `FAILED` and stays that way.
- **Stuck tasks:** the worker only picks up `status=READY` rows (`DBTaskResultQuerySet.ready()`). If a worker is killed mid-task (SIGKILL, OOM, `stop_grace_period` expiring), that row stays `RUNNING` forever, and no code path resets it.
- Visibility: an admin (`DBTaskResultAdmin`) with add, change and delete disabled, stored tracebacks per result, and a `prune_db_task_results` command (`--min-age-days`, `--failed-min-age-days`, `--dry-run`).
- Compatibility: requires `django>=5.2`. Trove classifiers list Django 5.2 and 6.0 and Python up to 3.14. **6.1 is not declared**, although nothing pins it out.

### 1b. `django-crontask`: periodic scheduling on top of `django.tasks`

[django-crontask](https://github.com/codingjoe/django-crontask) 2.0.0 (2026-05-27) requires `django>=6.0` and `apscheduler` (unpinned):

- Usage: `@cron("0 6 * * *")` stacked on `@task`. The decorator calls `scheduler.add_job(func=task.enqueue, trigger=...)`, so the scheduler only *enqueues* and a separate worker (1a) runs the task. Run it with `manage.py crontask`, a third process. `__init__.py` and `management/commands/crontask.py` hold this.
- Day-of-week has to be a literal (`Mon`…`Sun`). Numeric weekdays raise `ValueError`.
- It uses an in-memory APScheduler `BlockingScheduler`. In APScheduler 3.11.3 the job defaults are `misfire_grace_time=1`, `coalesce=True` and `max_instances=1` (`apscheduler/schedulers/base.py`). With the memory job store, **a run that falls due while the scheduler is restarting or down is simply missed**.
- `apscheduler` is unpinned, and PyPI already carries `4.0.0a*` pre-releases with a different API. That is a future breakage risk.
- An optional Redis lock prevents two schedulers. Without Redis the lock is a no-op (`FakeLock`), which is fine for a single instance.
- It offers optional Sentry cron monitors. Otherwise failure visibility comes from whatever the backend offers (the 1a admin).
- Classifiers declare Django 6.0 only.

**Operational weight of 1a + 1b:** two extra long-running Django processes (worker and scheduler), plus three new dependencies (`django-tasks-db`, `django-crontask`, `apscheduler`) and new tables. It is the most "Django-native" route because task code uses the standard `django.tasks` API and the backend can be swapped later.

## Option 2: supercronic sidecar calling management commands

[supercronic](https://github.com/aptible/supercronic) is a single static Go binary that reads a crontab (latest release v0.2.49, 2026-08-14). Quotes are from its README and `main.go`:

- It was built for containers, where classic cron does badly: "They purge their environment before starting jobs", capture output instead of logging to stdout, and "don't respond gracefully to `SIGINT` / `SIGTERM`". With supercronic, "Your environment variables are available in jobs", "Job output is logged to `stdout` / `stderr`", "`SIGTERM` triggers a graceful shutdown", and "Job return codes and schedules are logged".
- It runs as any user, and nothing in its model needs root or capabilities. That suits `read_only`, `cap_drop: ALL` and uid 1001. No state file is written, and the crontab is read from the image.
- No overlap: "Supercronic will wait for a given job to finish before that job is scheduled again", and warns when a job falls behind. `-overlapping` turns this off.
- Flags: `-json`, `-split-logs`, `-passthrough-logs`, `-test` (validate the crontab), `-inotify`, `-overlapping` and `-no-reap`. `SIGUSR2` reloads the crontab. There is optional `-sentry-dsn`, plus `-prometheus-listen-address` exposing `*_executions`, `*_successful_executions`, `*_failed_executions`, `*_deadline_exceeded`, `*_currently_running` and an execution-time histogram (`prometheus_metrics/prommetrics.go`).
- Timezone comes from `TZ` or `CRON_TZ` in the crontab. The prod base image has zoneinfo (see the constraints table).
- **No catch-up:** the scheduler computes `nextRun` forward from `time.Now()` at start-up (`cron/cron.go`). A 06:00 run missed during a deploy or reboot is not replayed.
- **No retries:** a non-zero exit is logged (and sent to Sentry or Prometheus if configured), and nothing more happens.

**Shape in this repo:**

- Add the binary to the `prod` stage (checksum-verified download; the releases page ships example Dockerfile stanzas) and a `crontab` file.
- Add a second compose service from the same image with `command: supercronic /app/crontab`, `RUN_MIGRATIONS=0`, `healthcheck: {disable: true}` (or `supercronic -test`), and the same `read_only`, `cap_drop` and `tmpfs` hardening.
- Each line runs `python manage.py <job>`.

**Operational weight:** one extra container. Its idle memory is just supercronic, and Django only loads while a job runs. It adds one binary to the prod image and no Python dependencies, tables or broker. Failures show up as a non-zero exit in `docker compose logs`, not in the app's UI, unless the command records its own run history.

## Option 3: django-q2 with the ORM broker

[django-q2](https://github.com/GDay/django-q2) 1.11.1 (2026-08-26) requires `django>=5.2` and declares Python 3.14. Its classifiers list no specific Django versions. Facts come from the sdist and its [docs](https://django-q2.readthedocs.io/):

- One process (`manage.py qcluster`) runs both the scheduler and a pool of workers. "Schedules run within the cluster process itself", so there is no separate beat ([schedules](https://django-q2.readthedocs.io/en/master/schedules.html)).
- Schedule types are Once, Minutes, Hourly, Daily, Weekly, Biweekly, Monthly, Bimonthly, Quarterly, Yearly and Cron. Cron needs the `croniter` extra (`models.py`). You manage them in the admin or with `schedule()`.
- **Catch-up:** `catch_up` defaults to `True`. After downtime "the scheduler executes tasks in the past to catch up", and it can pass the intended run time as a kwarg (`intended_date_kwarg`).
- **Retries:** with a delivery-guaranteeing broker (the ORM broker is one), an unacknowledged task is redelivered after `retry` seconds (default 60). `max_attempts` defaults to `0` (infinite). `ack_failures` defaults to `False`, which means *failed tasks are redelivered*. `conf.py` warns if `timeout` is unset or larger than `retry` ("will cause the tasks to be retriggered before completion"). These defaults need deliberate tuning.
- ORM broker: "for a medium message rate and scheduled tasks", "Delivery receipts", "Queue editable in Django Admin", and "Needs Django's Cache framework configured for monitoring" ([brokers](https://django-q2.readthedocs.io/en/master/brokers.html)). The broker polls every 0.2 s by default (`conf.py` `poll`).
- Visibility: admin pages for Successful and Failed tasks and for Schedules, with `last_run()` and `success()` on each schedule.
- Payloads are pickled and signed with `SECRET_KEY` (`signing.py`). Tasks queued before a `SECRET_KEY` rotation would likely fail their signature check afterwards. (This is an inference from the signing code and not tested.)
- It uses `multiprocessing` for its worker pool. Its queues need `/dev/shm`, which stays writable under `read_only: true`, and gunicorn already relies on it (`worker_tmp_dir`).
- It does **not** use the `django.tasks` API, so task code is tied to django-q2.

**Operational weight:** one extra container running a multi-process cluster (`workers` defaults to the CPU count, so it should be capped to 1–2), one dependency plus `django-picklefield` and optionally `croniter`, several tables, and a shared cache for monitoring.

## Option 4: Celery (and beat)

- It needs a broker. For Django that realistically means Redis or RabbitMQ, which is a new service to run, secure and back up.
- Beat is a separate process. "Beat needs to store the last run times of the tasks in a local database file (named *celerybeat-schedule* by default)". On the read-only filesystem that file would have to go to `/tmp` (`-s`), which is lost on restart, or you add `django-celery-beat` for a DB scheduler. "You have to ensure only a single scheduler is running", and embedding beat in a worker with `-B` "isn't recommended for production use" ([periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)).
- **Operational weight:** broker, worker and beat (three services) plus two or three dependencies, all for a handful of daily jobs for one user. It is the heaviest option by a wide margin.

## Also seen (not asked for)

- **Procrastinate** ([cron howto](https://procrastinate.readthedocs.io/en/stable/howto/advanced/cron.html)): a Postgres-based queue where "Each worker is responsible for ensuring that each periodic task is deferred", with DB-level dedupe, and at start-up it defers missed periodic tasks up to 10 minutes late (configurable). It has retries. It is Postgres-only (`psycopg[pool]`), so it does not fit the default SQLite dev stack.
- **Host crontab running `docker compose run --rm web python manage.py …`**: no image change, but the schedule lives outside the repo on the VPS, each run spins up a new container (which also runs the entrypoint's migrate unless `RUN_MIGRATIONS=0`), and output goes to the host's cron mail or syslog.

## Comparison

| | `django.tasks` + tasks-db + crontask | supercronic + commands | django-q2 (ORM) | Celery + beat |
|---|---|---|---|---|
| Extra containers | 2 (worker, scheduler) | 1 | 1 | 3 (broker, worker, beat) |
| New Python deps | 3 (+ tables) | 0 | 1–3 (+ tables) | 2–3 (+ tables if DB beat) |
| Idle memory | 2 × Django process | ~0 (Django only while a job runs) | Django × (1 + workers) | 2 × Django + broker |
| Periodic scheduling | via crontask (APScheduler) | cron syntax | built in (admin-editable) | beat |
| Catch-up after downtime | no (1 s misfire grace) | no | yes (`catch_up=True`) | depends on scheduler |
| Automatic retries | no | no | yes (needs tuning) | yes |
| Failure visibility | admin: results + tracebacks | container logs (+ optional Sentry or Prometheus) | admin: failed tasks, schedule `success()` | Flower or DB results backend |
| Request-triggered background work | yes | no | yes | yes |
| Read-only / unprivileged fit | fine | fine (add binary to image) | fine (cap workers; shared cache) | beat state file needs `/tmp` or DB scheduler |
| Standard API | `django.tasks` | plain management commands | django-q2 specific | Celery specific |
| Declares Django 6.1 | no (6.0 max) | n/a | unspecified | n/a |

## What the facts favour

For **daily price fetches, recurring-payment posting and reminders**, the facts favour **a supercronic sidecar running idempotent, date-driven management commands**:

- It is the lowest operational weight. It uses the existing image and hardening and adds no broker, no new tables and no long-running Django process.
- None of the `django.tasks` routes give retries or catch-up either, so they buy two more processes and three dependencies for nothing these jobs need.
- The missing catch-up and retries are handled better *in the job* than in the runner. For example, "post every recurring payment with a due date ≤ today that has no posting yet" is correct after any gap and safe to re-run. A job written that way is correct under every runner.
- Failure visibility is the weak spot. A cheap fix is for each command to write a small run-log row (job, started, finished, ok, error) that the dashboard can surface. That also fits Folio's "opinionated, tells you" doctrine.

django-q2 is the strongest alternative if built-in retries, catch-up and an admin view of failures matter more than the extra dependency and a non-standard API. `django.tasks` plus `django-tasks-db` becomes worth adding when Folio needs **request-triggered** background work, such as a CAS import or a price back-fill that shouldn't block a request. `db_worker --batch` could even run from the same supercronic crontab, so a separate always-on worker container isn't needed.

## Open questions this raises

- **Job idempotency and run-log model**: whether each scheduled job records its runs (for visibility and catch-up), and where that shows in the UI. This touches the price-feed pipeline and recurring-payment tickets.
- **Timezone**: `TIME_ZONE` defaults to `UTC`, but "daily" for an Indian user means IST. Should the app default to `Asia/Kolkata`, or should only the scheduler use `CRON_TZ`?
- **Alerting channel for failures**: container logs alone won't be noticed on a single-user VPS. This links to the undecided reminders and notifications channel on the map.
- **Is there any request-triggered background work in v1** (CAS import size, back-fills)? That decides whether `django.tasks` plus `django-tasks-db` is needed at all.
