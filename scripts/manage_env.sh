#!/bin/bash

# 🔧 Script de Gestion des Environnements
# Ce script aide à gérer les différents environnements de développement

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_help() {
    echo "🔧 Gestionnaire d'Environnements - Modern Blog Platform"
    echo "====================================================="
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  dev         Démarrer l'environnement de développement"
    echo "  prod        Démarrer l'environnement de production"
    echo "  test        Démarrer l'environnement de test"
    echo "  stop        Arrêter tous les environnements"
    echo "  clean       Nettoyer les données et conteneurs"
    echo "  status      Afficher le statut des services"
    echo "  logs        Afficher les logs (par défaut: dev)"
    echo "  shell       Ouvrir un shell Django"
    echo "  db-shell    Ouvrir un shell PostgreSQL"
    echo "  migrate     Exécuter les migrations"
    echo "  superuser   Créer un superutilisateur"
    echo "  backup      Créer une sauvegarde"
    echo "  restore     Restaurer une sauvegarde"
    echo
    echo "Options:"
    echo "  -h, --help  Afficher cette aide"
    echo "  -v          Mode verbeux"
    echo
    echo "Exemples:"
    echo "  $0 dev              # Démarrer en mode développement"
    echo "  $0 prod             # Démarrer en mode production"
    echo "  $0 logs dev         # Voir les logs de développement"
    echo "  $0 shell            # Ouvrir un shell Django"
}

# Vérifier le répertoire
check_directory() {
    if [[ ! -f "../manage.py" ]]; then
        print_error "Ce script doit être exécuté depuis le dossier scripts/"
        exit 1
    fi
}

# Démarrer l'environnement de développement
start_dev() {
    print_status "Démarrage de l'environnement de développement..."
    cd ..
    docker-compose up --build -d
    print_success "Environnement de développement démarré"
    echo "🌐 Accès: http://localhost:8000"
}

# Démarrer l'environnement de production
start_prod() {
    print_status "Démarrage de l'environnement de production..."
    cd ..
    if [[ ! -f "docker-compose.prod.yml" ]]; then
        print_error "Fichier docker-compose.prod.yml non trouvé"
        exit 1
    fi
    docker-compose -f docker-compose.prod.yml up --build -d
    print_success "Environnement de production démarré"
}

# Démarrer l'environnement de test
start_test() {
    print_status "Démarrage de l'environnement de test..."
    cd ..
    # Créer un environnement de test avec une base de données temporaire
    docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build -d
    print_success "Environnement de test démarré"
}

# Arrêter tous les environnements
stop_all() {
    print_status "Arrêt de tous les environnements..."
    cd ..
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    print_success "Tous les environnements arrêtés"
}

# Nettoyer
clean_all() {
    print_warning "⚠️  Cette action va supprimer tous les conteneurs et volumes!"
    read -p "Êtes-vous sûr ? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Nettoyage en cours..."
        cd ..
        docker-compose down -v --remove-orphans 2>/dev/null || true
        docker-compose -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
        docker system prune -f
        print_success "Nettoyage terminé"
    else
        print_status "Nettoyage annulé"
    fi
}

# Afficher le statut
show_status() {
    print_status "Statut des services:"
    cd ..
    docker-compose ps
}

# Afficher les logs
show_logs() {
    local env=${1:-dev}
    print_status "Logs de l'environnement: $env"
    cd ..
    
    case $env in
        "prod")
            docker-compose -f docker-compose.prod.yml logs -f
            ;;
        *)
            docker-compose logs -f
            ;;
    esac
}

# Ouvrir un shell Django
django_shell() {
    print_status "Ouverture du shell Django..."
    cd ..
    docker-compose exec django python manage.py shell
}

# Ouvrir un shell PostgreSQL
db_shell() {
    print_status "Ouverture du shell PostgreSQL..."
    cd ..
    docker-compose exec postgres psql -U postgres -d blog_db
}

# Exécuter les migrations
run_migrations() {
    print_status "Exécution des migrations..."
    cd ..
    docker-compose exec django python manage.py migrate
    print_success "Migrations terminées"
}

# Créer un superutilisateur
create_superuser() {
    print_status "Création d'un superutilisateur..."
    cd ..
    docker-compose exec django python manage.py createsuperuser
}

# Créer une sauvegarde
create_backup() {
    print_status "Création d'une sauvegarde..."
    local backup_dir="../backup"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="backup_${timestamp}.sql"
    
    mkdir -p "$backup_dir"
    cd ..
    
    docker-compose exec postgres pg_dump -U postgres blog_db > "backup/$backup_file"
    print_success "Sauvegarde créée: $backup_file"
}

# Restaurer une sauvegarde
restore_backup() {
    print_status "Restauration d'une sauvegarde..."
    local backup_dir="../backup"
    
    if [[ ! -d "$backup_dir" ]]; then
        print_error "Dossier de sauvegarde non trouvé: $backup_dir"
        exit 1
    fi
    
    echo "Sauvegardes disponibles:"
    ls -la "$backup_dir"/*.sql 2>/dev/null || {
        print_error "Aucune sauvegarde trouvée"
        exit 1
    }
    
    read -p "Nom du fichier de sauvegarde: " backup_file
    
    if [[ ! -f "$backup_dir/$backup_file" ]]; then
        print_error "Fichier de sauvegarde non trouvé: $backup_file"
        exit 1
    fi
    
    print_warning "⚠️  Cette action va écraser la base de données actuelle!"
    read -p "Continuer ? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd ..
        docker-compose exec -T postgres psql -U postgres -d blog_db < "backup/$backup_file"
        print_success "Sauvegarde restaurée"
    else
        print_status "Restauration annulée"
    fi
}

# Fonction principale
main() {
    check_directory
    
    case "${1:-}" in
        "dev")
            start_dev
            ;;
        "prod")
            start_prod
            ;;
        "test")
            start_test
            ;;
        "stop")
            stop_all
            ;;
        "clean")
            clean_all
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "${2:-dev}"
            ;;
        "shell")
            django_shell
            ;;
        "db-shell")
            db_shell
            ;;
        "migrate")
            run_migrations
            ;;
        "superuser")
            create_superuser
            ;;
        "backup")
            create_backup
            ;;
        "restore")
            restore_backup
            ;;
        "-h"|"--help"|"help")
            show_help
            ;;
        "")
            show_help
            ;;
        *)
            print_error "Commande inconnue: $1"
            echo "Utilisez '$0 --help' pour voir les commandes disponibles."
            exit 1
            ;;
    esac
}

# Exécuter la fonction principale
main "$@"
