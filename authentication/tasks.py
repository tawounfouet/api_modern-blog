"""
Tâches asynchrones pour l'authentification

Ce module contient les tâches Celery pour l'authentification,
comme l'envoi d'emails de confirmation, de réinitialisation de mot de passe, etc.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id, verification_token):
    """
    Envoie un email de vérification de compte

    Args:
        user_id (int): ID de l'utilisateur
        verification_token (str): Token de vérification

    Returns:
        dict: Résultat de l'envoi
    """
    try:
        user = User.objects.get(id=user_id)

        # Préparer le contexte pour le template
        context = {
            "user": user,
            "verification_token": verification_token,
            "site_name": "Modern Blog Platform",
            "domain": (
                settings.ALLOWED_HOSTS[0]
                if settings.ALLOWED_HOSTS
                else "localhost:8000"
            ),
        }

        # Générer le contenu HTML et texte
        html_message = render_to_string(
            "authentication/emails/verification_email.html", context
        )
        plain_message = strip_tags(html_message)

        # Envoyer l'email
        send_mail(
            subject="Vérifiez votre compte - Modern Blog Platform",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Email de vérification envoyé avec succès à {user.email}")
        return {
            "status": "success",
            "message": f"Email de vérification envoyé à {user.email}",
            "user_id": user_id,
        }

    except User.DoesNotExist:
        logger.error(f"Utilisateur avec l'ID {user_id} n'existe pas")
        return {
            "status": "error",
            "message": f"Utilisateur avec l'ID {user_id} n'existe pas",
        }

    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi de l'email de vérification: {exc}")
        # Retry avec backoff exponentiel
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2**self.request.retries), exc=exc)

        return {
            "status": "error",
            "message": f"Échec de l'envoi après {self.max_retries} tentatives: {str(exc)}",
        }


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id, reset_token):
    """
    Envoie un email de réinitialisation de mot de passe

    Args:
        user_id (int): ID de l'utilisateur
        reset_token (str): Token de réinitialisation

    Returns:
        dict: Résultat de l'envoi
    """
    try:
        user = User.objects.get(id=user_id)

        context = {
            "user": user,
            "reset_token": reset_token,
            "site_name": "Modern Blog Platform",
            "domain": (
                settings.ALLOWED_HOSTS[0]
                if settings.ALLOWED_HOSTS
                else "localhost:8000"
            ),
        }

        html_message = render_to_string(
            "authentication/emails/password_reset_email.html", context
        )
        plain_message = strip_tags(html_message)

        send_mail(
            subject="Réinitialisation de mot de passe - Modern Blog Platform",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Email de réinitialisation envoyé avec succès à {user.email}")
        return {
            "status": "success",
            "message": f"Email de réinitialisation envoyé à {user.email}",
            "user_id": user_id,
        }

    except User.DoesNotExist:
        logger.error(f"Utilisateur avec l'ID {user_id} n'existe pas")
        return {
            "status": "error",
            "message": f"Utilisateur avec l'ID {user_id} n'existe pas",
        }

    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2**self.request.retries), exc=exc)

        return {
            "status": "error",
            "message": f"Échec de l'envoi après {self.max_retries} tentatives: {str(exc)}",
        }


@shared_task(bind=True)
def send_welcome_email(self, user_id):
    """
    Envoie un email de bienvenue après inscription

    Args:
        user_id (int): ID de l'utilisateur

    Returns:
        dict: Résultat de l'envoi
    """
    try:
        user = User.objects.get(id=user_id)

        context = {
            "user": user,
            "site_name": "Modern Blog Platform",
            "login_url": f"{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'}/login",
        }

        html_message = render_to_string(
            "authentication/emails/welcome_email.html", context
        )
        plain_message = strip_tags(html_message)

        send_mail(
            subject="Bienvenue sur Modern Blog Platform!",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Email de bienvenue envoyé avec succès à {user.email}")
        return {
            "status": "success",
            "message": f"Email de bienvenue envoyé à {user.email}",
            "user_id": user_id,
        }

    except User.DoesNotExist:
        logger.error(f"Utilisateur avec l'ID {user_id} n'existe pas")
        return {
            "status": "error",
            "message": f"Utilisateur avec l'ID {user_id} n'existe pas",
        }

    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {exc}")
        return {"status": "error", "message": f"Erreur lors de l'envoi: {str(exc)}"}


@shared_task
def cleanup_expired_tokens():
    """
    Nettoie les tokens expirés (tâche périodique)

    Returns:
        dict: Résultat du nettoyage
    """
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        from django.utils import timezone
        from datetime import timedelta

        # Supprimer les tokens expirés depuis plus de 7 jours
        cutoff_date = timezone.now() - timedelta(days=7)
        expired_tokens = OutstandingToken.objects.filter(created_at__lt=cutoff_date)
        count = expired_tokens.count()
        expired_tokens.delete()

        logger.info(f"Nettoyage effectué: {count} tokens expirés supprimés")
        return {
            "status": "success",
            "message": f"{count} tokens expirés supprimés",
            "cleaned_count": count,
        }

    except Exception as exc:
        logger.error(f"Erreur lors du nettoyage des tokens: {exc}")
        return {"status": "error", "message": f"Erreur lors du nettoyage: {str(exc)}"}


@shared_task
def generate_user_activity_report():
    """
    Génère un rapport d'activité des utilisateurs (tâche périodique)

    Returns:
        dict: Résultat de la génération du rapport
    """
    try:
        from django.utils import timezone
        from datetime import timedelta

        # Statistiques des 30 derniers jours
        thirty_days_ago = timezone.now() - timedelta(days=30)

        total_users = User.objects.count()
        active_users = User.objects.filter(last_login__gte=thirty_days_ago).count()
        new_users = User.objects.filter(date_joined__gte=thirty_days_ago).count()

        report = {
            "total_users": total_users,
            "active_users_30d": active_users,
            "new_users_30d": new_users,
            "activity_rate": (
                (active_users / total_users * 100) if total_users > 0 else 0
            ),
            "generated_at": timezone.now().isoformat(),
        }

        logger.info(f"Rapport d'activité généré: {report}")
        return {
            "status": "success",
            "message": "Rapport d'activité généré avec succès",
            "report": report,
        }

    except Exception as exc:
        logger.error(f"Erreur lors de la génération du rapport: {exc}")
        return {
            "status": "error",
            "message": f"Erreur lors de la génération: {str(exc)}",
        }
