from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from .models import User
from django.conf import settings
from django.contrib.auth.password_validation import validate_password


class CustomRegisterSerializer(RegisterSerializer):
    """
    Serializer personnalisé pour l'inscription avec dj-rest-auth
    """

    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data.update(
            {
                "first_name": self.validated_data.get("first_name", ""),
                "last_name": self.validated_data.get("last_name", ""),
            }
        )
        return data

    def save(self, request):
        user = super().save(request)
        user.first_name = self.validated_data.get("first_name", "")
        user.last_name = self.validated_data.get("last_name", "")
        user.save()
        return user


class UserCreateSerializer(BaseUserCreateSerializer):
    """
    Serializer pour la création d'utilisateurs, utilisant la nouvelle syntaxe de dj-rest-auth
    """

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = [
            "id",
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "avatar",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Utiliser les paramètres de ACCOUNT_SETTINGS pour déterminer les champs obligatoires
        account_settings = getattr(settings, "ACCOUNT_SETTINGS", {})
        signup_fields = account_settings.get("SIGNUP_FIELDS", {})

        for field_name, config in signup_fields.items():
            if field_name in self.fields and "required" in config:
                self.fields[field_name].required = config["required"]


class UserSerializer(BaseUserSerializer):
    # Ajout d'un champ pour obtenir le profil utilisateur
    profile = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "avatar",
            "profile",
        ]

    def get_profile(self, obj):
        from content.serializers import UserProfileSerializer

        if hasattr(obj, "profile"):
            return UserProfileSerializer(obj.profile).data
        return None


class UserDetailSerializer(UserSerializer):
    """
    Serializer pour les détails complets d'un utilisateur, incluant son profil.
    """

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields
