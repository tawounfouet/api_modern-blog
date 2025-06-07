from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from content.models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crée automatiquement un profil utilisateur lorsqu'un nouvel utilisateur est créé
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """
    S'assure que le profil est sauvegardé quand l'utilisateur est sauvegardé
    """
    # Vérifier si l'utilisateur a déjà un profil
    if hasattr(instance, "profile"):
        instance.profile.save()
    else:
        # Si le profil n'existe pas pour une raison quelconque, le créer
        UserProfile.objects.create(user=instance)
