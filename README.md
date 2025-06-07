# 📋 Modern Blog Platform - Structure du Projet

## 📁 Structure des Dossiers

```
backend/
├── 📄 Configuration principale
│   ├── .env                    # Variables d'environnement
│   ├── .env.example           # Exemple de configuration
│   ├── manage.py              # Script principal Django
│   ├── requirements.txt       # Dépendances Python
│   └── Makefile              # Commandes rapides
│
├── 🏗️ Applications Django
│   ├── authentication/       # Système d'authentification
│   ├── content/              # Gestion du contenu (posts, etc.)
│   ├── core/                # Configuration Django principale
│   ├── helpers/             # Utilitaires et helpers
│   └── utils/               # Scripts utilitaires
│
├── 📁 Dossiers de données
│   ├── media/               # Fichiers uploadés par les utilisateurs
│   ├── static/              # Fichiers statiques de développement
│   └── staticfiles/         # Fichiers statiques collectés
│
├── 🐳 Configuration Docker
│   ├── deployment/          # Configuration de déploiement
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.prod.yml
│   │   ├── docker-compose.override.yml
│   │   ├── Dockerfile
│   │   ├── Dockerfile.prod
│   │   ├── Makefile
│   │   └── README.md
│   └── docker/              # Configurations Docker spécialisées
│       ├── proxy/           # Configuration Nginx
│       │   └── nginx.conf
│       └── scripts/         # Scripts de conteneur
│           ├── entrypoint.sh
│           └── healthcheck.sh
│
├── 📚 Documentation
│   └── docs/
│       └── README_DOCKER.md # Guide Docker détaillé
│
├── 🔧 Scripts
│   ├── scripts/             # Scripts d'administration
│   │   ├── setup.sh         # Configuration automatique
│   │   ├── check_production.py
│   │   ├── test_auth_api.py
│   │   └── test_environment.py
│   └── backup/              # Scripts de sauvegarde
│
└── 📊 Données persistantes
    ├── db.sqlite3           # Base de données SQLite (développement)
    └── backup/              # Sauvegardes
```

## 🚀 Démarrage Rapide

### Option 1: Configuration Automatique (Recommandé)
```bash
cd backend
./scripts/setup.sh
```

### Option 2: Configuration Manuelle
```bash
cd backend/deployment
make setup    # ou docker-compose up --build
```

## 📝 Commandes Utiles

### Depuis le dossier `backend/`
```bash
# Configuration automatique complète
./scripts/setup.sh

# Tests et vérifications
python scripts/test_environment.py
python scripts/test_auth_api.py
```

### Depuis le dossier `backend/deployment/`
```bash
# Gestion des conteneurs
make up          # Démarrer les services
make down        # Arrêter les services
make logs        # Voir les logs
make status      # Statut des services
make restart     # Redémarrer les services

# Développement
make shell-django    # Shell Django
make shell-db       # Shell PostgreSQL
make migrate        # Exécuter les migrations
make superuser      # Créer un superutilisateur

# Maintenance
make clean          # Nettoyer les conteneurs
make rebuild        # Reconstruire complètement
```

## 🔧 Configuration

### Variables d'Environnement
- **Fichier principal**: `.env`
- **Exemple**: `.env.example`
- **Docker**: `.env.docker.example`

### Base de Données
- **Développement**: SQLite (`db.sqlite3`)
- **Production**: PostgreSQL (via Docker)

### Services
- **Django**: http://localhost:8000
- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/
- **PostgreSQL**: localhost:5434
- **Redis**: localhost:6380

## 📚 Documentation

- **Docker**: [`docs/README_DOCKER.md`](docs/README_DOCKER.md)
- **API**: Consultez `/api/` pour la documentation auto-générée
- **Déploiement**: [`deployment/README.md`](deployment/README.md)

## 🛠️ Dépannage

### Problèmes courants
1. **Ports occupés**: Modifiez les ports dans `docker-compose.yml`
2. **Permissions**: Assurez-vous que les scripts sont exécutables
3. **Variables d'environnement**: Vérifiez le fichier `.env`

### Logs et Debugging
```bash
# Logs détaillés
cd deployment && make logs

# Status des services
cd deployment && make status

# Shell pour debugging
cd deployment && make shell-django
```

## 🔐 Sécurité

- Les scripts utilisent des utilisateurs non-root dans les conteneurs
- Les mots de passe sont générés automatiquement
- Configuration SSL prête pour la production
- Headers de sécurité configurés dans Nginx

## 📦 Déploiement

### Développement
```bash
cd backend/deployment
docker-compose up --build
```

### Production
```bash
cd backend/deployment
docker-compose -f docker-compose.prod.yml up --build -d
```

## 🤝 Contribution

1. Respectez la structure des dossiers
2. Documentez les nouvelles fonctionnalités
3. Testez avec `./scripts/setup.sh`
4. Mettez à jour ce README si nécessaire


```sh
# Exécuter le conteneur en montant le volume
# docker run -d \
#   --name modern-blog \
#   -p 8000:8000 \
#   -v sqlite_data:/app \
#   tawounfouet/modern-blog-platform:sqlite-latest

docker run -d tawounfouet/modern-blog-platform

docker run -d -p 8000:8000 tawounfouet/modern-blog-platform

docker run -d tawounfouet/modern-blog-platform:sqlite-latest

docker run -d -p 8000:8000 tawounfouet/modern-blog-platform:sqlite-latest


# créer un volume pour la base de données SQLite
docker volume create sqlite_data
# Exécuter le conteneur en montant le volume
docker run -d \
  --name modern-blog \
  -p 8000:8000 \
  -v sqlite_data:/app/db.sqlite3 \
  tawounfouet/modern-blog-platform
```