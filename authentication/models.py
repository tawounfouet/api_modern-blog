from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extended from Django's AbstractUser.
    Email is used as the unique identifier for authentication instead of username.

    Ce modèle gère uniquement les informations d'authentification et les données de base.
    Les informations supplémentaires du profil sont dans le modèle UserProfile.
    """

    email = models.EmailField(_("email address"), unique=True)
    username = models.CharField(_("username"), max_length=150, unique=True)
    # La photo avatar reste dans le modèle User pour un accès facile dans l'UI
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    # Email is the primary identifier for authentication
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "username"
    ]  # Username is still required, but not the primary identifier

    def __str__(self):
        return self.email
