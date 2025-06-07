from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "authentication"

    def ready(self):
        """
        Import les signaux lors du chargement de l'application
        pour s'assurer que les handlers de signaux sont enregistrés.
        """
        import authentication.signals
