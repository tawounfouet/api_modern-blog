#!/bin/bash

# 🔄 Script de Commutation d'Environnement - Modern Blog Platform
# Ce script permet de basculer entre les configurations Docker des différents environnements

set -e

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

# Afficher l'aide
show_help() {
    echo "🔄 Gestionnaire de Configuration d'Environnement"
    echo "=============================================="
    echo
    echo "Usage: $0 [ENVIRONMENT]"
    echo
    echo "Environnements disponibles:"
    echo "  dev       Configuration de développement"
    echo "  prod      Configuration de production"
    echo "  staging   Configuration de staging (si disponible)"
    echo "  current   Afficher l'environnement actuel"
    echo "  backup    Sauvegarder la configuration actuelle"
    echo "  restore   Restaurer la dernière sauvegarde"
    echo
    echo "Structure:"
    echo "  • Fichiers actifs: backend/ (utilisés par Docker)"
    echo "  • Templates: backend/deployment/ (configurations pour chaque env)"
    echo
}

# Vérifier si on est dans le bon répertoire
check_directory() {
    if [[ ! -f "manage.py" ]]; then
        print_error "Ce script doit être exécuté depuis le dossier backend/"
        exit 1
    fi
}

# Sauvegarder la configuration actuelle
backup_current() {
    print_status "Sauvegarde de la configuration actuelle..."
    
    mkdir -p deployment/backup
    
    if [[ -f "docker-compose.yml" ]]; then
        cp docker-compose.yml deployment/backup/
    fi
    
    if [[ -f "Dockerfile" ]]; then
        cp Dockerfile deployment/backup/
    fi
    
    if [[ -f "Makefile" ]]; then
        cp Makefile deployment/backup/
    fi
    
    echo "$(date)" > deployment/backup/backup_timestamp
    
    print_success "Configuration sauvegardée dans deployment/backup/"
}

# Restaurer la dernière sauvegarde
restore_backup() {
    if [[ ! -d "deployment/backup" ]]; then
        print_error "Aucune sauvegarde trouvée"
        exit 1
    fi
    
    print_status "Restauration de la dernière sauvegarde..."
    
    if [[ -f "deployment/backup/docker-compose.yml" ]]; then
        cp deployment/backup/docker-compose.yml .
    fi
    
    if [[ -f "deployment/backup/Dockerfile" ]]; then
        cp deployment/backup/Dockerfile .
    fi
    
    if [[ -f "deployment/backup/Makefile" ]]; then
        cp deployment/backup/Makefile .
    fi
    
    if [[ -f "deployment/backup/backup_timestamp" ]]; then
        backup_time=$(cat deployment/backup/backup_timestamp)
        print_success "Configuration restaurée (sauvegarde du: $backup_time)"
    else
        print_success "Configuration restaurée"
    fi
}

# Basculer vers un environnement
switch_to_env() {
    local env=$1
    
    print_status "Basculement vers l'environnement: $env"
    
    # Arrêter les services en cours
    if docker-compose ps --services >/dev/null 2>&1; then
        print_status "Arrêt des services actuels..."
        docker-compose down
    fi
    
    # Sauvegarder la configuration actuelle
    backup_current
    
    # Copier les nouveaux fichiers
    case $env in
        "dev")
            if [[ -f "deployment/docker-compose.yml" ]]; then
                cp deployment/docker-compose.yml .
                print_success "docker-compose.yml (dev) activé"
            fi
            
            if [[ -f "deployment/Dockerfile" ]]; then
                cp deployment/Dockerfile .
                print_success "Dockerfile (dev) activé"
            fi
            
            if [[ -f "deployment/Makefile" ]]; then
                cp deployment/Makefile .
                print_success "Makefile (dev) activé"
            fi
            ;;
            
        "prod")
            if [[ -f "deployment/docker-compose.prod.yml" ]]; then
                cp deployment/docker-compose.prod.yml docker-compose.yml
                print_success "docker-compose.prod.yml activé comme docker-compose.yml"
            fi
            
            if [[ -f "deployment/Dockerfile.prod" ]]; then
                cp deployment/Dockerfile.prod Dockerfile
                print_success "Dockerfile.prod activé comme Dockerfile"
            fi
            
            if [[ -f "deployment/Makefile" ]]; then
                cp deployment/Makefile .
                print_success "Makefile (prod) activé"
            fi
            ;;
            
        *)
            print_error "Environnement '$env' non reconnu"
            exit 1
            ;;
    esac
    
    print_success "Environnement '$env' activé avec succès"
    print_warning "N'oubliez pas de vérifier votre fichier .env pour cet environnement"
}

# Afficher l'environnement actuel
show_current() {
    echo "🔍 Configuration actuelle:"
    echo "========================"
    echo
    
    if [[ -f "docker-compose.yml" ]]; then
        echo "📄 docker-compose.yml:"
        if grep -q "Production Configuration" docker-compose.yml 2>/dev/null; then
            echo "   → Production"
        elif grep -q "Development Configuration" docker-compose.yml 2>/dev/null; then
            echo "   → Development"
        else
            echo "   → Custom/Unknown"
        fi
    fi
    
    if [[ -f "Dockerfile" ]]; then
        echo "📄 Dockerfile:"
        if grep -q "Production Dockerfile" Dockerfile 2>/dev/null; then
            echo "   → Production"
        elif grep -q "Development Dockerfile" Dockerfile 2>/dev/null; then
            echo "   → Development"  
        else
            echo "   → Custom/Unknown"
        fi
    fi
    
    echo
    echo "📁 Templates disponibles dans deployment/:"
    ls -1 deployment/ | grep -E "\.(yml|yaml|Dockerfile)" | sed 's/^/   • /'
    echo
}

# Fonction principale
main() {
    check_directory
    
    case "${1:-help}" in
        "dev")
            switch_to_env "dev"
            ;;
        "prod")
            switch_to_env "prod"
            ;;
        "current")
            show_current
            ;;
        "backup")
            backup_current
            ;;
        "restore")
            restore_backup
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            print_error "Option '$1' non reconnue"
            show_help
            exit 1
            ;;
    esac
}

# Exécuter le script principal
main "$@"
