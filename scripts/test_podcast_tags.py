#!/usr/bin/env python
"""
Script de test pour la fonctionnalité de tags des podcasts
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from content.models import Podcast, Category
from authentication.models import User
from django.utils import timezone


def test_podcast_tags():
    """Test de la fonctionnalité de tags des podcasts"""

    print("🎧 Test de la fonctionnalité de tags des podcasts")
    print("=" * 50)

    # Créer un utilisateur de test si nécessaire
    user, created = User.objects.get_or_create(
        username="testhost",
        defaults={
            "email": "testhost@example.com",
            "first_name": "Test",
            "last_name": "Host",
        },
    )
    if created:
        print(f"✅ Utilisateur créé: {user.username}")
    else:
        print(f"ℹ️  Utilisateur existant: {user.username}")

    # Créer une catégorie de test
    category, created = Category.objects.get_or_create(
        name="Technology", defaults={"description": "Tech podcasts"}
    )
    if created:
        print(f"✅ Catégorie créée: {category.name}")
    else:
        print(f"ℹ️  Catégorie existante: {category.name}")

    # Créer un podcast de test avec des tags
    test_tags = "python, django, web development, api, rest framework"

    podcast, created = Podcast.objects.get_or_create(
        title="Test Podcast with Tags",
        defaults={
            "description": "Un podcast de test pour tester les tags",
            "host": user,
            "tags": test_tags,
            "published_at": timezone.now(),
            "is_published": True,
        },
    )

    if created:
        podcast.categories.add(category)
        print(f"✅ Podcast créé: {podcast.title}")
    else:
        # Mettre à jour les tags si le podcast existe déjà
        podcast.tags = test_tags
        podcast.save()
        print(f"ℹ️  Podcast mis à jour: {podcast.title}")

    print(f"📝 Tags (string): {podcast.tags}")
    print(f"📋 Tags (list): {podcast.get_tags_list()}")

    # Test des méthodes helper
    print("\n🔧 Test des méthodes helper:")

    # Test get_tags_list
    tags_list = podcast.get_tags_list()
    print(f"get_tags_list(): {tags_list}")

    # Test set_tags_list
    new_tags = ["javascript", "typescript", "node.js", "express"]
    podcast.set_tags_list(new_tags)
    print(f"Après set_tags_list({new_tags}): {podcast.tags}")

    # Remettre les tags originaux
    podcast.tags = test_tags
    podcast.save()

    # Test de recherche par tags
    print("\n🔍 Test de recherche par tags:")

    # Recherche de podcasts contenant "python"
    python_podcasts = Podcast.objects.filter(tags__icontains="python")
    print(f"Podcasts contenant 'python': {python_podcasts.count()}")

    # Recherche de podcasts contenant "django"
    django_podcasts = Podcast.objects.filter(tags__icontains="django")
    print(f"Podcasts contenant 'django': {django_podcasts.count()}")

    # Test de récupération de tous les tags uniques
    print("\n📊 Récupération de tous les tags uniques:")
    all_podcasts = Podcast.objects.filter(is_published=True).exclude(tags="")
    all_tags = set()

    for p in all_podcasts:
        tags = p.get_tags_list()
        all_tags.update(tags)

    print(f"Tags uniques trouvés: {sorted(list(all_tags))}")
    print(f"Nombre total de tags uniques: {len(all_tags)}")

    print("\n✅ Test terminé avec succès!")
    print("\n📊 Résumé:")
    print(f"   - Podcasts avec tags: {Podcast.objects.exclude(tags='').count()}")
    print(f"   - Tags uniques: {len(all_tags)}")
    print(f"   - Exemple de tags: {podcast.get_tags_list()}")


if __name__ == "__main__":
    test_podcast_tags()
