FROM node:22-alpine AS styles
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY tailwind.config.js ./
COPY templates ./templates
COPY apps ./apps
COPY static ./static
RUN npm run build:css

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=styles /build/static/css/dist.css ./static/css/dist.css

RUN python manage.py collectstatic --noinput --settings=config.settings.build \
    && useradd --create-home app \
    && mkdir -p /app/media /app/data \
    && chown app:app /app/media /app/data

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "scripts/healthcheck.py"]

# SQLite has one writer at a time: keep --workers at 1 (mount /app/data as a
# persistent volume so the db file survives redeploys) and use threads for
# request concurrency instead of extra processes.
CMD ["sh", "-c", "python manage.py check && python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-1} --threads ${GUNICORN_THREADS:-4} --worker-class gthread --timeout ${GUNICORN_TIMEOUT:-60} --access-logfile - --error-logfile -"]
