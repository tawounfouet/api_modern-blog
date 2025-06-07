import cloudinary
from django.conf import settings


def get_cloudinary_config():
    """Retourne la configuration Cloudinary depuis les paramètres Django"""
    return {
        "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
        "api_key": settings.CLOUDINARY_PUBLIC_API_KEY,
        "api_secret": settings.CLOUDINARY_SECRET_API_KEY,
        "secure": True,
    }


def cloudinary_init():
    """Initialize Cloudinary configuration"""
    try:
        config = get_cloudinary_config()
        cloudinary.config(**config)
        return True
    except Exception as e:
        print(f"Erreur lors de l'initialisation de Cloudinary: {e}")
        return False
