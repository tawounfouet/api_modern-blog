"""
Module contenant les classes d'email personnalisées pour l'authentification.
"""

from djoser import email


class ActivationEmail(email.ActivationEmail):
    template_name = "authentication/email/activation.html"


class ConfirmationEmail(email.ConfirmationEmail):
    template_name = "authentication/email/confirmation.html"


class PasswordResetEmail(email.PasswordResetEmail):
    template_name = "authentication/email/password_reset.html"


class PasswordChangedConfirmationEmail(email.PasswordChangedConfirmationEmail):
    template_name = "authentication/email/password_changed_confirmation.html"


class UsernameChangedConfirmationEmail(email.UsernameChangedConfirmationEmail):
    template_name = "authentication/email/username_changed_confirmation.html"


class UsernameResetEmail(email.UsernameResetEmail):
    template_name = "authentication/email/username_reset.html"
