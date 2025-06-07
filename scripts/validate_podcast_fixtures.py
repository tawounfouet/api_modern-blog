#!/usr/bin/env python3
"""
Script de validation des fixtures podcasts
Ce script vérifie que les fixtures podcasts sont valides et fonctionnelles.
"""

import os
import sys
import django
import requests
import json
from pathlib import Path

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from content.models import Podcast, Category
from django.contrib.auth import get_user_model

User = get_user_model()


def check_database_state():
    """Vérifier l'état actuel de la base de données"""
    print("🔍 Vérification de l'état de la base de données...")

    # Vérifier les utilisateurs
    users = User.objects.all()
    print(f"   Utilisateurs: {users.count()} trouvés")
    for user in users:
        print(f"     - ID {user.id}: {user.username} ({user.email})")

    # Vérifier les catégories
    categories = Category.objects.all()
    print(f"   Catégories: {categories.count()} trouvées")
    for cat in categories:
        print(f"     - ID {cat.id}: {cat.name} ({cat.slug})")

    # Vérifier les podcasts
    podcasts = Podcast.objects.all()
    print(f"   Podcasts: {podcasts.count()} trouvés")
    for podcast in podcasts:
        print(
            f"     - ID {podcast.id}: {podcast.title} (S{podcast.season}E{podcast.episode})"
        )

    return users.count() >= 3 and categories.count() >= 2


def validate_fixtures_structure():
    """Valider la structure des fixtures"""
    print("\n📋 Validation de la structure des fixtures...")

    fixtures_path = Path("content/fixtures/06_podcasts_corrected.json")
    if not fixtures_path.exists():
        print("   ❌ Fichier de fixtures introuvable")
        return False

    try:
        with open(fixtures_path, "r", encoding="utf-8") as f:
            fixtures_data = json.load(f)

        print(f"   ✅ Fixtures chargées: {len(fixtures_data)} podcasts")

        # Vérifier les champs requis
        required_fields = [
            "title",
            "slug",
            "description",
            "cloudinary_url",
            "cloudinary_public_id",
            "duration",
            "host",
            "categories",
            "is_published",
            "is_processed",
            "season",
            "episode",
        ]

        for i, fixture in enumerate(fixtures_data):
            fields = fixture.get("fields", {})
            missing_fields = [field for field in required_fields if field not in fields]

            if missing_fields:
                print(f"   ❌ Podcast {i+1}: champs manquants: {missing_fields}")
                return False
            else:
                print(f"   ✅ Podcast {i+1}: structure valide")

        return True

    except Exception as e:
        print(f"   ❌ Erreur lors de la lecture: {e}")
        return False


def test_api_endpoints():
    """Tester les endpoints API"""
    print("\n🌐 Test des endpoints API...")

    try:
        # Test de l'endpoint liste des podcasts
        response = requests.get("http://localhost:8000/api/podcasts/", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Podcasts accessible: {data.get('count', 0)} podcasts")

            # Vérifier quelques podcasts
            results = data.get("results", [])
            for podcast in results[:2]:
                title = podcast.get("title", "N/A")
                host = podcast.get("host", {}).get("username", "N/A")
                print(f"     - {title} par {host}")

            return True
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("   ⚠️  Serveur Django non accessible (normal si non démarré)")
        return True  # Ne pas considérer comme une erreur critique
    except Exception as e:
        print(f"   ❌ Erreur de test API: {e}")
        return False


def validate_podcast_relationships():
    """Valider les relations des podcasts"""
    print("\n🔗 Validation des relations des podcasts...")

    podcasts = Podcast.objects.all()

    for podcast in podcasts:
        print(f"   Podcast: {podcast.title}")

        # Vérifier l'host
        if podcast.host:
            print(f"     ✅ Host: {podcast.host.username}")
        else:
            print(f"     ❌ Aucun host défini")
            return False

        # Vérifier les catégories
        categories = podcast.categories.all()
        if categories.exists():
            cat_names = [cat.name for cat in categories]
            print(f"     ✅ Catégories: {', '.join(cat_names)}")
        else:
            print(f"     ❌ Aucune catégorie assignée")
            return False

        # Vérifier les invités
        guests = podcast.guests.all()
        if guests.exists():
            guest_names = [guest.username for guest in guests]
            print(f"     ✅ Invités: {', '.join(guest_names)}")
        else:
            print(f"     ℹ️  Aucun invité")

        # Vérifier les URLs
        if podcast.cloudinary_url:
            print(f"     ✅ URL audio: {podcast.cloudinary_url[:50]}...")
        else:
            print(f"     ❌ Aucune URL audio")
            return False

    return True


def main():
    """Fonction principale de validation"""
    print("=" * 60)
    print("🎙️  VALIDATION DES FIXTURES PODCASTS")
    print("=" * 60)

    all_checks_passed = True

    # 1. Vérifier l'état de la base de données
    if not check_database_state():
        print("\n❌ Prérequis manquants (utilisateurs ou catégories)")
        all_checks_passed = False

    # 2. Valider la structure des fixtures
    if not validate_fixtures_structure():
        print("\n❌ Structure des fixtures invalide")
        all_checks_passed = False

    # 3. Valider les relations
    if not validate_podcast_relationships():
        print("\n❌ Relations des podcasts invalides")
        all_checks_passed = False

    # 4. Tester l'API
    if not test_api_endpoints():
        print("\n⚠️  Tests API incomplets")

    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✅ TOUTES LES VALIDATIONS SONT PASSÉES")
        print("📚 Les fixtures podcasts sont prêtes à l'emploi !")
    else:
        print("❌ CERTAINES VALIDATIONS ONT ÉCHOUÉ")
        print("🔧 Veuillez corriger les problèmes identifiés")
    print("=" * 60)

    return 0 if all_checks_passed else 1


if __name__ == "__main__":
    sys.exit(main())
