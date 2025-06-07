# Modern Blog Platform - Development Dockerfile Template
FROM python:3.11-slim

# Arguments de construction
ARG USE_SQLITE=true
ARG DJANGO_SUPERUSER_USERNAME=admin
ARG DJANGO_SUPERUSER_EMAIL=admin@example.com
ARG DJANGO_SUPERUSER_PASSWORD=admin

# Définir les variables d'environnement par défaut
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    USE_SQLITE=true \
    DEBUG=true \
    DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME} \
    DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL} \
    DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD} \
    SECRET_KEY="django-insecure-test-key-for-development-only-do-not-use-in-production" \
    ALLOWED_HOSTS="localhost,127.0.0.1,0.0.0.0,*" \
    CLOUDINARY_CLOUD_NAME=${CLOUDINARY_CLOUD_NAME} \
    CLOUDINARY_API_KEY=${CLOUDINARY_API_KEY} \
    CLOUDINARY_API_SECRET=${CLOUDINARY_API_SECRET} \
    CORS_ALLOW_ALL_ORIGINS="True" \
    CORS_ALLOW_CREDENTIALS="True" \
    CORS_EXPOSED_HEADERS="Content-Type,X-CSRFToken" \
    CORS_ALLOW_HEADERS="accept,accept-encoding,authorization,content-type,dnt,origin,user-agent,x-csrftoken,x-requested-with" \
    DJANGO_SETTINGS_MODULE=core.settings

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    musl-dev \
    libffi-dev \
    libssl-dev \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root pour la sécurité
RUN useradd --create-home --shell /bin/bash django

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code source et les scripts
COPY . .
COPY scripts/entrypoint.sh /app/entrypoint.sh
COPY scripts/create_superuser.py /app/scripts/create_superuser.py

# Créer les répertoires nécessaires et configurer les permissions
RUN mkdir -p media static staticfiles logs && \
    chmod +x scripts/entrypoint.sh && \
    chmod +x /app/entrypoint.sh && \
    chown -R django:django /app

# Si vous voulez garder une base de données pré-remplie, assurez-vous qu'elle ait les bonnes permissions
RUN if [ -f db.sqlite3 ]; then chmod 664 db.sqlite3; fi

# Vérifier la structure du projet
RUN ls -la && \
    echo "Vérification du module core:" && \
    ls -la core/

# Passer à l'utilisateur non-root
USER django

# Vérifier l'accès au module core
RUN python -c "import sys; print(sys.path); import core; print('Module core trouvé!')"

# Collecter les fichiers statiques et créer le superutilisateur
RUN if [ "$USE_SQLITE" = "true" ]; then \
        echo "Configuration pour SQLite" && \
        python manage.py migrate --noinput && \
        python manage.py collectstatic --noinput && \
        python scripts/create_superuser.py; \
    else \
        echo "Configuration standard (PostgreSQL)" && \
        python manage.py collectstatic --noinput; \
    fi

# Exposer le port 8000
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]