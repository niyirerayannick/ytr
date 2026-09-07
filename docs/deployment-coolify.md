# Deploy YTR on Coolify

Use the repository's **Dockerfile** build pack with a PostgreSQL resource and
S3-compatible storage for uploads. Static assets are served by WhiteNoise from
the image. No Node.js process is needed at runtime.

## 1. Create the database and media bucket

Create a PostgreSQL resource in the same Coolify project/environment and start
it. Copy its **internal connection URL** for `DATABASE_URL`. Ensure the application
and database share a Docker network. Do not publish the database port publicly.

Create a private S3-compatible bucket (AWS S3, Cloudflare R2, or MinIO).
Give the app credentials scoped to reading, writing, listing, and deleting objects
in that bucket. Upload URLs are signed; the bucket does not need public access.
For MinIO, its HTTPS endpoint must also be reachable by visitors' browsers.
S3-compatible providers may require their specific region (for example `auto`
for R2) and API endpoint. AWS S3 usually needs no custom endpoint.

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
DATABASE_URL=postgresql://user:password@internal-database-host:5432/ytr
PORT=8000
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=60
TIME_ZONE=Africa/Kigali
AWS_STORAGE_BUCKET_NAME=ytr-media
AWS_ACCESS_KEY_ID=<bucket-access-key>
AWS_SECRET_ACCESS_KEY=<bucket-secret-key>
AWS_S3_REGION_NAME=us-east-1
```

For an S3-compatible service, also set `AWS_S3_ENDPOINT_URL` to the provider's
HTTPS API endpoint, with no bucket suffix. URL-encode special characters in
database usernames/passwords. Use plain hostnames in `ALLOWED_HOSTS`, without
schemes, paths, ports, or wildcards. The health check sends the first hostname;
`HEALTHCHECK_HOST` can override it with another allowed hostname if necessary.

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
`/health/` and requires HTTP 200 after the database query succeeds.

In Coolify's application terminal, run:

```bash
python manage.py check --deploy
python manage.py createsuperuser
```

Do not run `seed_demo_content` in production: it creates accounts with known
demo passwords. Add real content through `/admin/` or the dashboard.

Verify the homepage and `/health/` over HTTPS, log in to `/admin/`, submit a form,
and upload a cover image. Confirm the image loads, then redeploy and confirm it
still loads. Also check `/service-worker.js` and `/static/css/dist.css`.

## Persistence and updates

PostgreSQL stores accounts and content; the bucket stores uploaded files. With
this setup the application needs no persistent volume. Enable database backups
and bucket versioning/backups, and test restoring both.

Do not leave `DATABASE_URL` empty in production: the local SQLite fallback is
for development and is not supported by this non-root, stateless container.
Without `AWS_STORAGE_BUCKET_NAME`, Django falls back to local media storage;
the production app does not serve `/media/`. If deliberately using local media,
mount persistent storage at `/app/media`, make it writable by the container's
`app` user, and configure a separate media server/origin. A volume alone does
not make uploads publicly accessible.

Existing local SQLite data is not migrated automatically into PostgreSQL.
Export/import it separately if it must be retained. Copy existing media files
to the bucket using the same relative object names stored in the database.

Back up before schema changes. Startup migrations must be compatible with any
old containers still serving traffic during rolling deployment. For incompatible
schema changes, use a maintenance window and a separately coordinated migration.
Image rollback does not reverse database migrations.

The current form throttle uses per-process memory. Configure proxy/CDN request
limits for production, as noted in [security.md](security.md).

## Local image verification

With Docker running, build using:

```bash
docker build -t ytr:coolify .
```

Run it using a private environment file containing the production variables and
a database hostname reachable from Docker (not `localhost`):

```bash
docker run --rm --env-file /path/to/private-production.env -p 8000:8000 ytr:coolify
```

The image's health check supplies the trusted HTTPS header internally. A plain
HTTP browser request will redirect to HTTPS, so test browser flows behind an
HTTPS proxy. Never commit the private environment file.

References: [Coolify Dockerfile builds](https://next.coolify.io/docs/applications/builds/dockerfile),
[health checks](https://coolify.io/docs/knowledge-base/health-checks),
[S3 storage configuration](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html).
