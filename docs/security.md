# YTR Security and Staging Guide

## Required production environment

Run production with `config.settings.prod` and set, at minimum:

```text
SECRET_KEY=<generated random value of at least 50 characters>
ALLOWED_HOSTS=your-domain.example,www.your-domain.example
DATABASE_URL=postgres://...
EMAIL_BACKEND=...
EMAIL_HOST=...
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=...
CONTACT_FALLBACK_EMAIL=...
```

`SECRET_KEY` is required in production. Empty values, values shorter than 50 characters, and obvious development placeholders are rejected at startup. Never commit `.env`, credentials, databases, media, or cloud keys. Generate a secret with `python -c "import secrets; print(secrets.token_urlsafe(64))"` and store it in the deployment platform's secret manager.

If TLS terminates at a trusted reverse proxy, set `SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https` only after confirming the proxy strips incoming client-supplied forwarding headers. HTTPS redirect, HSTS, secure session/CSRF cookies, no-sniff protection and a same-origin referrer policy are enabled in production settings.

## Public forms

Registration and contact forms are limited to five attempts per IP per hour; newsletter attempts are limited to ten. All three include a honeypot field. The limits use Django's cache: the default is suitable for a single staging process but production should use a shared cache and reverse-proxy/CDN limits so multiple processes share the same policy.

Do not add CAPTCHA unless abuse persists. Do not disclose whether an account or subscriber email already exists. Contact notification failures are logged for operators, while visitors receive a neutral confirmation after their message is persisted.

## Safe redirects

Bookmark and RSVP forms accept `next` only when it is a same-host URL validated by Django. Never add a direct `redirect(request.POST["next"])` or equivalent user-controlled redirect.

## Media policy

YouTube is the initial video delivery path. Video URLs must be HTTPS URLs on YouTube/youtu.be domains. Author video forms intentionally do not offer local video upload; the legacy admin field remains validated for existing records and limited to MP4/WebM up to 100 MB.

Podcast uploads accept MP3, M4A or WAV up to 25 MB, with extension, claimed request MIME type and size checks. These checks are not antivirus scanning. In production, store user media in object storage or a dedicated media host outside the executable application directory, serve it through a non-executable origin/CDN, and add malware scanning if untrusted uploads expand.

## Logging and operations

Production emits INFO/WARNING/ERROR logs to standard output, suitable for Coolify/container log capture. Do not log passwords, tokens, full prayer requests, or message bodies. Configure log retention and alerts in the hosting platform. `/health/` runs a lightweight `SELECT 1` database check and returns only `{"status": "ok"}` or a generic 503 response.

## Staging checklist

1. Use PostgreSQL and run `python manage.py migrate` during release.
2. Run `python manage.py collectstatic --noinput` before serving application traffic.
3. Configure backups for database and object storage; test a restore.
4. Configure a reverse proxy/CDN request limit in addition to app limits.
5. Confirm `/health/` is healthy, HTTPS is active, and error pages do not reveal diagnostics.
6. Run `python manage.py check --deploy --settings=config.settings.prod` with production-equivalent non-secret values before deployment.
