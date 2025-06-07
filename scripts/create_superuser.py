import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()

DJANGO_SUPERUSER_USERNAME = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
DJANGO_SUPERUSER_EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
DJANGO_SUPERUSER_PASSWORD = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin')

try:
    if not User.objects.filter(username=DJANGO_SUPERUSER_USERNAME).exists():
        print(f"Création du superutilisateur {DJANGO_SUPERUSER_USERNAME}...")
        User.objects.create_superuser(
            username=DJANGO_SUPERUSER_USERNAME,
            email=DJANGO_SUPERUSER_EMAIL,
            password=DJANGO_SUPERUSER_PASSWORD
        )
        print("Superutilisateur créé avec succès.")
    else:
        print(f"Le superutilisateur {DJANGO_SUPERUSER_USERNAME} existe déjà.")
except IntegrityError as e:
    print(f"Erreur lors de la création du superutilisateur: {e}")
except Exception as e:
    print(f"Une erreur inattendue s'est produite: {e}")