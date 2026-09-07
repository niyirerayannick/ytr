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
    && mkdir -p /app/media \
    && chown app:app /app/media

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "scripts/healthcheck.py"]

CMD ["sh", "-c", "python manage.py check && python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-3} --timeout ${GUNICORN_TIMEOUT:-60} --access-logfile - --error-logfile -"]
