#!/bin/bash

# 🚀 Script de Configuration Rapide pour Modern Blog Platform
# Ce script configure automatiquement l'environnement de développement
#
# Structure Docker:
# - Fichiers actifs: backend/ (docker-compose.yml, Dockerfile, Makefile)
# - Templates: backend/deployment/ (configurations pour dev, staging, prod)

set -e

echo "🚀 Configuration de Modern Blog Platform"
echo "========================================"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher des messages colorés
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si Docker est installé
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé. Veuillez l'installer d'abord."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé. Veuillez l'installer d'abord."
        exit 1
    fi
    
    print_success "Docker et Docker Compose sont installés"
}

# Vérifier si on est dans le bon répertoire
check_directory() {
    if [[ ! -f "manage.py" ]]; then
        print_error "Ce script doit être exécuté depuis le dossier backend/"
        exit 1
    fi
    print_success "Répertoire correct détecté"
}

# Créer le fichier .env s'il n'existe pas
setup_env() {
    if [[ ! -f ".env" ]]; then
        print_status "Création du fichier .env..."
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            print_success "Fichier .env créé à partir de .env.example"
        else
            print_warning "Aucun fichier .env.example trouvé"
        fi
    else
        print_success "Fichier .env existe déjà"
    fi
}

# Construire et démarrer les conteneurs
start_services() {
    print_status "Construction et démarrage des services..."
    cd ..
    
    # Arrêter les services existants s'ils tournent
    docker-compose down 2>/dev/null || true
    
    # Construire et démarrer
    docker-compose up --build -d
    
    print_success "Services démarrés avec succès"
}

# Attendre que les services soient prêts
wait_for_services() {
    print_status "Attente que les services soient prêts..."
    
    # Attendre PostgreSQL
    timeout=60
    counter=0
    while ! docker-compose exec postgres pg_isready -U postgres >/dev/null 2>&1; do
        if [ $counter -ge $timeout ]; then
            print_error "Timeout: PostgreSQL n'est pas prêt après ${timeout}s"
            exit 1
        fi
        sleep 1
        counter=$((counter + 1))
    done
    
    print_success "PostgreSQL est prêt"
    
    # Attendre Django
    timeout=120
    counter=0
    while ! curl -f http://localhost:8000/api/ >/dev/null 2>&1; do
        if [ $counter -ge $timeout ]; then
            print_error "Timeout: Django n'est pas prêt après ${timeout}s"
            exit 1
        fi
        sleep 2
        counter=$((counter + 2))
    done
    
    print_success "Django est prêt"
}

# Exécuter les migrations
run_migrations() {
    print_status "Exécution des migrations..."
    docker-compose exec django python manage.py migrate
    print_success "Migrations terminées"
}

# Collecter les fichiers statiques
collect_static() {
    print_status "Collecte des fichiers statiques..."
    docker-compose exec django python manage.py collectstatic --noinput
    print_success "Fichiers statiques collectés"
}

# Créer un superutilisateur
create_superuser() {
    read -p "Voulez-vous créer un superutilisateur ? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Création du superutilisateur..."
        docker-compose exec django python manage.py createsuperuser
    fi
}

# Afficher les informations finales
show_info() {
    echo
    echo "🎉 Configuration terminée avec succès !"
    echo "======================================"
    echo
    echo "🌐 URLs disponibles :"
    echo "   • API Django: http://localhost:8000/api/"
    echo "   • Admin Django: http://localhost:8000/admin/"
    echo "   • PostgreSQL: localhost:5434"
    echo "   • Redis: localhost:6380"
    echo
    echo "📋 Commandes utiles :"
    echo "   • Voir les logs: make logs"
    echo "   • Arrêter: make down"
    echo "   • Shell Django: make shell-django"
    echo "   • Status: make status"
    echo
    echo "📁 Fichiers importants :"
    echo "   • Configuration: .env"
    echo "   • Docker actuel: docker-compose.yml et Dockerfile (racine)"
    echo "   • Templates Docker: deployment/ (dev, staging, prod)"
    echo "   • Docs: docs/"
    echo
}

# Fonction principale
main() {
    print_status "Début de la configuration..."
    
    check_docker
    check_directory
    setup_env
    start_services
    wait_for_services
    run_migrations
    collect_static
    create_superuser
    show_info
    
    print_success "🚀 Modern Blog Platform est prêt à l'emploi !"
}

# Gestion des erreurs
trap 'print_error "Script interrompu. Nettoyage..."; cd .. 2>/dev/null && docker-compose down 2>/dev/null || true; exit 1' INT TERM

# Exécuter le script principal
main "$@"
