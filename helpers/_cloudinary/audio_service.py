import cloudinary.uploader
from django.core.files.storage import default_storage
import os
import logging

logger = logging.getLogger(__name__)


class CloudinaryAudioService:
    @staticmethod
    def upload_podcast_to_cloudinary(podcast_instance):
        """Upload le fichier audio d'un podcast vers Cloudinary"""
        if not podcast_instance.audio_file:
            return False

        try:
            # Upload vers Cloudinary
            upload_result = cloudinary.uploader.upload(
                podcast_instance.audio_file.path,
                resource_type="video",  # Utiliser 'video' pour les fichiers audio
                folder="podcasts/",
                public_id=f"podcast_{podcast_instance.id}_{podcast_instance.slug}",
                overwrite=True,
            )

            # Sauvegarder les informations Cloudinary
            podcast_instance.cloudinary_url = upload_result["secure_url"]
            podcast_instance.cloudinary_public_id = upload_result["public_id"]
            podcast_instance.is_processed = True

            # Si duration n'est pas définie, utiliser celle de Cloudinary
            if not podcast_instance.duration and "duration" in upload_result:
                podcast_instance.duration = int(upload_result["duration"])

            podcast_instance.save()

            # Supprimer le fichier local temporaire
            if default_storage.exists(podcast_instance.audio_file.name):
                default_storage.delete(podcast_instance.audio_file.name)
                podcast_instance.audio_file = None
                podcast_instance.save()

            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'upload vers Cloudinary: {str(e)}")
            return False

    @staticmethod
    def get_cloudinary_audio(
        podcast_instance, as_html=False, controls=True, autoplay=False
    ):
        """
        Retourne l'URL ou le HTML d'un lecteur audio Cloudinary
        """
        if not podcast_instance.cloudinary_url:
            return (
                podcast_instance.audio_file.url if podcast_instance.audio_file else ""
            )

        if not as_html:
            return podcast_instance.cloudinary_url

        # Créer un lecteur HTML5 avec l'URL Cloudinary
        html = f"""
        <audio {' controls' if controls else ''} {' autoplay' if autoplay else ''} preload="metadata" class="podcast-player">
            <source src="{podcast_instance.cloudinary_url}" type="audio/mpeg">
            Votre navigateur ne supporte pas la lecture audio.
        </audio>
        """
        return html
