#!/bin/bash

set -e

# Définir explicitement le module de paramètres Django
export DJANGO_SETTINGS_MODULE=core.settings

# S'assurer que ALLOWED_HOSTS est correctement configuré
if [ -z "$ALLOWED_HOSTS" ]; then
  export ALLOWED_HOSTS="localhost,127.0.0.1,0.0.0.0,*"
fi

# Configuration selon le type de base de données
if [ "$USE_SQLITE" = "true" ]; then
    echo "Utilisation de SQLite"
    
    # Exécuter les migrations si nécessaire
    python manage.py migrate --noinput
    
    # Vérifie et crée le superutilisateur si nécessaire
    python scripts/create_superuser.py
else
    echo "Utilisation de PostgreSQL"
    
    # Attendre que la base de données soit prête
    echo "En attente de la disponibilité de la base de données PostgreSQL..."
    
    # Exécuter les migrations
    python manage.py migrate --noinput
    
    # Vérifie et crée le superutilisateur si nécessaire
    python scripts/create_superuser.py
fi

# Démarrer le serveur Django en écoutant sur toutes les interfaces
echo "Démarrage du serveur Django..."
python manage.py runserver 0.0.0.0:8000