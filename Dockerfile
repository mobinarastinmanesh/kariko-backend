# Use Iranian mirror to bypass Docker Hub restrictions
FROM registry.docker.ir/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
# Inlined to avoid -r chaining issues; no .env needed at this stage
RUN pip install \
    Django==5.0.6 \
    djangorestframework==3.15.2 \
    djangorestframework-simplejwt==5.3.1 \
    django-cors-headers==4.4.0 \
    django-filter==24.2 \
    psycopg2-binary==2.9.9 \
    python-decouple==3.8 \
    Pillow==10.4.0 \
    phonenumbers==8.13.44 \
    django-phonenumber-field==7.3.0 \
    pyotp==2.9.0 \
    redis==5.0.8 \
    django-redis==5.4.0 \
    celery==5.4.0 \
    gunicorn==22.0.0 \
    whitenoise==6.7.0 \
    drf-nested-routers==0.94.1 \
    sentry-sdk==2.13.0

# Copy source code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Non-root user for security
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && mkdir -p staticfiles media \
    && chown -R appuser:appgroup staticfiles media

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/auth/otp/request/')" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
