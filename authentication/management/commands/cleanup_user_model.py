from django.core.management.base import BaseCommand
from django.db import migrations, transaction
from authentication.models import User
from content.models import UserProfile


class Command(BaseCommand):
    help = "Nettoie les champs sociaux du modèle User après la migration des données"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche les modifications qui seraient faites sans les appliquer",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        
        with transaction.atomic():
            if dry_run:
                self.stdout.write(self.style.WARNING("Mode simulation (dry run)"))
            
            # Vérifier que tous les utilisateurs ont un profil
            users_without_profile = User.objects.filter(profile__isnull=True)
            if users_without_profile.exists():
                self.stdout.write(
                    self.style.ERROR(
                        f"{users_without_profile.count()} utilisateurs n'ont pas de profil."
                        " Exécutez d'abord la commande migrate_user_profiles."
                    )
                )
                return
            
            # Vérifier que toutes les données ont été migrées
            verification_failed = False
            for user in User.objects.all():
                profile = user.profile
                if any([
                    user.twitter != profile.twitter,
                    user.github != profile.github,
                    user.linkedin != profile.linkedin,
                    user.role != profile.role,
                ]):
                    self.stdout.write(
                        self.style.ERROR(
                            f"Les données de l'utilisateur {user.username} "
                            "ne correspondent pas à son profil"
                        )
                    )
                    verification_failed = True
            
            if verification_failed:
                self.stdout.write(
                    self.style.ERROR(
                        "La vérification a échoué. "
                        "Exécutez d'abord la commande migrate_user_profiles."
                    )
                )
                return
            
            # Si nous sommes en dry-run, arrêter ici
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        "La vérification est réussie. "
                        "Les données peuvent être supprimées en toute sécurité."
                    )
                )
                return
            
            # Supprimer les champs
            User.objects.update(
                twitter="",
                github="",
                linkedin="",
                role="reader"
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    "Les champs sociaux ont été nettoyés avec succès du modèle User"
                )
            )
