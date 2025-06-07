from django.core.management.base import BaseCommand
from django.db import transaction
from authentication.models import User
from content.models import UserProfile


class Command(BaseCommand):
    help = "Migre les données des utilisateurs depuis User vers UserProfile"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING("Début de la migration des données utilisateur")
        )

        # Compter les utilisateurs et les profils
        user_count = User.objects.count()
        profile_count = UserProfile.objects.count()

        self.stdout.write(f"Nombre d'utilisateurs: {user_count}")
        self.stdout.write(f"Nombre de profils existants: {profile_count}")

        migrated = 0
        created = 0

        with transaction.atomic():
            for user in User.objects.all():
                # Vérifier si l'utilisateur a déjà un profil
                try:
                    profile = user.profile
                    # Si le profil existe, mettre à jour les champs
                    profile.twitter = user.twitter
                    profile.github = user.github
                    profile.linkedin = user.linkedin
                    profile.role = user.role
                    profile.save()
                    migrated += 1
                except UserProfile.DoesNotExist:
                    # Si le profil n'existe pas, le créer
                    UserProfile.objects.create(
                        user=user,
                        twitter=user.twitter,
                        github=user.github,
                        linkedin=user.linkedin,
                        role=user.role,
                    )
                    created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Migration terminée! {migrated} profils mis à jour, {created} profils créés"
            )
        )
