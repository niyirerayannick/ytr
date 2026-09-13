# Deploy YTR on Coolify

Use the repository's **Dockerfile** build pack. This variant runs on **SQLite**
instead of PostgreSQL, with the database file and uploaded media stored on two
persistent volumes so they survive redeploys. Static assets are served by
WhiteNoise from the image. No Node.js process is needed at runtime.

SQLite has exactly one writer at a time. That's fine for a low/medium-traffic
site like this one as long as: the container runs a single Gunicorn worker
(concurrency comes from threads instead — already set up in the Dockerfile),
WAL mode is enabled (already set in `config/settings/base.py`), and the db
file lives on a real persistent volume, not the container's writable layer.
If traffic grows enough that "database is locked" errors start showing up in
logs, that's the signal to move to PostgreSQL — swap `DATABASE_URL` back to a
`postgresql://` URL and nothing else in the app needs to change.

## 1. Create the persistent volumes

In the application's **Storage** tab, add two persistent volumes:

| Mount path | Purpose |
| --- | --- |
| `/app/data` | Holds `db.sqlite3` (WAL sidecar files too) |
| `/app/media` | Holds uploaded images (article covers, avatars, etc.) |

Both must exist before the first deploy so the app writes into the volume
instead of the container's ephemeral layer.

## 2. Create the application

Connect the Git repository and select the branch containing these changes:

| Coolify setting | Value |
| --- | --- |
| Build pack | Dockerfile |
| Base directory | `/` |
| Dockerfile location | `/Dockerfile` |
| Ports Exposes | `8000` |
| Domain | `https://your-domain.com` |
| Start/build command overrides | Leave empty |
| Health check | Use the Dockerfile's built-in check |

Point the domain's DNS to the Coolify server and allow Coolify to provision TLS.
Use the proxy for inbound traffic; no host port mapping is needed for the app.

## 3. Set runtime environment variables

Replace all sample values below in Coolify's environment variable editor.
Keep secrets runtime-only; the image build does not require credentials.

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.prod
DEBUG=False
SECRET_KEY=<generated-random-secret>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
DATABASE_URL=sqlite:////app/data/db.sqlite3
PORT=8000
GUNICORN_WORKERS=1
GUNICORN_THREADS=4
GUNICORN_TIMEOUT=60
TIME_ZONE=Africa/Kigali
```

Leave `AWS_STORAGE_BUCKET_NAME` unset — with it unset, Django writes uploads to
local disk at `/app/media`, which the volume from step 1 persists across
redeploys. Use plain hostnames in `ALLOWED_HOSTS`, without schemes, paths,
ports, or wildcards. The health check sends the first hostname;
`HEALTHCHECK_HOST` can override it with another allowed hostname if necessary.

A ready-to-paste copy of these variables (already filled in with a generated
`SECRET_KEY`) is in `.env.coolify.local` at the repo root — it's gitignored,
so only paste its contents into Coolify's editor, never commit it.

Generate the Django secret locally and paste it into Coolify:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Keep the same secret across deployments. The forwarded-protocol setting assumes
Coolify's trusted proxy controls that header, as described in [security.md](security.md).

Configure real email delivery as well:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_HOST_USER=<smtp-user>
EMAIL_HOST_PASSWORD=<smtp-password>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=<verified-sender-address>
CONTACT_FALLBACK_EMAIL=<ministry-inbox>
```

Without SMTP configuration, mail is printed to container logs.

## 4. Deploy and initialize

Deploy. Each container startup checks Django configuration, applies migrations,
and starts Gunicorn. Failed migrations stop startup. The readiness check requests
`/health/` and requires HTTP 200 after the database query succeeds. On this
first deploy, migrations create a fresh, empty `/app/data/db.sqlite3` on the
volume — replace it with your local database next.

## 5. Bring over your local content

Your local `db.sqlite3` and `media/` folder (articles, devotions, uploaded
images, accounts, everything you created on `localhost`) are not in git — the
repo's `.gitignore` deliberately excludes them, since committing user data
(password hashes, contact-form messages, prayer requests) to source control is
a bad idea. Copy them onto the server directly instead:

```bash
# From PowerShell in this repo, create a local content bundle
.\scripts\package-production-content.ps1

# Upload the generated deploy-content/ytr-content-*.zip to the Coolify host,
# then unzip it there.
scp deploy-content/ytr-content-*.zip you@your-coolify-host:/tmp/
ssh you@your-coolify-host
cd /tmp
unzip ytr-content-*.zip

# On the Coolify host: find the running container, then copy the files in
docker ps --filter "name=<your-app-name>"           # note the container ID
./restore-production-content.sh <container-id>
```

Then restart the application in Coolify so Gunicorn picks up the copied
database cleanly (rather than a file that may have been open mid-copy).

If you'd rather not use `scp`/SSH, Coolify's per-application **Terminal** tab
gives you a shell in the running container; you can `curl`/`wget` the files
from anywhere you've temporarily hosted them, or paste small files with a
heredoc, then move them to `/app/data` and `/app/media` the same way.

Do not run `seed_demo_content` in production: it creates accounts with known
demo passwords — skip it, since your real content is now in place.

Verify the homepage and `/health/` over HTTPS, log in to `/admin/` with an
account from your local database, and confirm articles/images you created
locally are showing up. Redeploy once and confirm the same content and images
are still there (proves the volumes are actually persisting, not just the
first container's filesystem).

## Persistence and updates

The SQLite file on `/app/data` and uploaded media on `/app/media` are only as
durable as those two volumes — back them up. A simple approach: a cron job (on
the Coolify host, or a scheduled task in Coolify itself) that copies
`/app/data/db.sqlite3*` and `/app/media` out to off-host storage on a
schedule. Stop writes or use SQLite's `.backup` command (via
`sqlite3 db.sqlite3 ".backup '/backup/path.sqlite3'"`) rather than copying the
file while the app is live, so you don't capture it mid-transaction.

Back up before schema changes. Startup migrations must be compatible with any
old containers still serving traffic during rolling deployment. For incompatible
schema changes, use a maintenance window and a separately coordinated migration.
Image rollback does not reverse database migrations.

If this ever needs to move to PostgreSQL (e.g. traffic outgrows a single
SQLite writer), `python manage.py dumpdata` / `loaddata` is the standard route
— dump from SQLite locally, point `DATABASE_URL` at a Postgres resource, load
the dump, and redeploy.

The current form throttle uses per-process memory. Configure proxy/CDN request
limits for production, as noted in [security.md](security.md).

## Local image verification

With Docker running, build using:

```bash
docker build -t ytr:coolify .
```

Run it using a private environment file containing the production variables,
mounting local volumes for `/app/data` and `/app/media` so the container has
somewhere to write the SQLite file (no external database needed with SQLite):

```bash
docker run --rm --env-file /path/to/private-production.env \
  -v ytr-data:/app/data -v ytr-media:/app/media \
  -p 8000:8000 ytr:coolify
```

The image's health check supplies the trusted HTTPS header internally. A plain
HTTP browser request will redirect to HTTPS, so test browser flows behind an
HTTPS proxy. Never commit the private environment file.

References: [Coolify Dockerfile builds](https://next.coolify.io/docs/applications/builds/dockerfile),
[health checks](https://coolify.io/docs/knowledge-base/health-checks),
[Django SQLite notes (WAL mode)](https://docs.djangoproject.com/en/5.2/ref/databases/#database-is-locked-errors).
