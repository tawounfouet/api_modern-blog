#!/bin/bash
# filepath: /Users/awf/Projects/software-development/dev/django/api_modern-blog-plateforme/docker-publish.sh

set -e

# Vérifier que le Dockerfile existe
if [ ! -f "Dockerfile" ]; then
  echo "Erreur: Dockerfile introuvable dans le répertoire actuel."
  echo "Assurez-vous d'exécuter ce script depuis le répertoire racine du projet."
  exit 1
fi

# Charger les variables d'environnement
if [ -f .env ]; then
  source .env
else
  echo "Erreur: Fichier .env introuvable."
  exit 1
fi

# Vérifier les variables requises
if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ] || [ -z "$DOCKER_IMAGE_NAME" ] || [ -z "$DOCKER_IMAGE_TAG" ]; then
  echo "Erreur: Variables d'environnement manquantes. Vérifiez votre fichier .env"
  exit 1
fi

# Se connecter à DockerHub
echo "Connexion à Docker Hub..."
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

# Construire l'image Docker avec SQLite
echo "Construction de l'image Docker..."
docker build \
  --build-arg USE_SQLITE=true \
  -t "$DOCKER_USERNAME/$DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG" \
  -t "$DOCKER_USERNAME/$DOCKER_IMAGE_NAME:latest" \
  .

# Pousser l'image vers DockerHub
echo "Publication de l'image sur DockerHub..."
docker push "$DOCKER_USERNAME/$DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG"
docker push "$DOCKER_USERNAME/$DOCKER_IMAGE_NAME:latest"

echo "Publication terminée avec succès!"