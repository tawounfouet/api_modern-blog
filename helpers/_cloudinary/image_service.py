import cloudinary.uploader
from django.core.files.storage import default_storage
import os
import logging
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)


class CloudinaryImageService:
    @staticmethod
    def upload_post_image_to_cloudinary(post_instance, image_field="featured_image"):
        """Upload l'image d'un post vers Cloudinary avec différentes versions"""
        if not hasattr(post_instance, image_field) or not getattr(
            post_instance, image_field
        ):
            return False

        try:
            image_file = getattr(post_instance, image_field)

            # Obtenir le chemin du fichier
            image_path = image_file.path

            # Uploader l'image originale
            upload_result = cloudinary.uploader.upload(
                image_path,
                resource_type="image",
                folder="posts/original",
                public_id=f"post_{post_instance.id}_{post_instance.slug}",
                overwrite=True,
            )

            # Sauvegarder l'ID public pour référence
            post_instance.cloudinary_public_id = upload_result["public_id"]

            # Assigner les URL Cloudinary aux différents champs
            post_instance.cloudinary_image = upload_result["public_id"]

            # Créer les transformations pour l'image large et thumbnail
            # (Cloudinary le fait automatiquement grâce aux transformations définies dans le modèle)
            post_instance.cloudinary_image_large = upload_result["public_id"]
            post_instance.cloudinary_image_thumbnail = upload_result["public_id"]

            # Sauvegarder les modifications dans la base de données
            post_instance.save()

            # Supprimer l'image locale temporaire si elle existe encore
            if default_storage.exists(image_path):
                default_storage.delete(image_path)
                logger.info(f"Fichier local supprimé : {image_path}")

            return True

        except Exception as e:
            logger.error(
                f"Erreur lors de l'upload de l'image vers Cloudinary: {str(e)}"
            )
            return False

    @staticmethod
    def delete_post_image_from_cloudinary(post_instance):
        """Supprime les images Cloudinary associées à un post"""
        if post_instance.cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(
                    post_instance.cloudinary_public_id, resource_type="image"
                )
                return True
            except Exception as e:
                logger.error(
                    f"Erreur lors de la suppression de l'image Cloudinary: {str(e)}"
                )
                return False
        return False

    @staticmethod
    def get_post_image_urls(post_instance):
        """Retourne un dictionnaire avec les URLs des différentes versions de l'image"""
        urls = {"original": "", "large": "", "thumbnail": ""}

        # URL de l'image originale
        if post_instance.cloudinary_image:
            urls["original"] = post_instance.cloudinary_image.url
        elif post_instance.featured_image:
            urls["original"] = post_instance.featured_image.url

        # URL de l'image large
        if post_instance.cloudinary_image_large:
            urls["large"] = post_instance.cloudinary_image_large.url
        elif urls["original"]:
            urls["large"] = urls["original"]

        # URL de la vignette
        if post_instance.cloudinary_image_thumbnail:
            urls["thumbnail"] = post_instance.cloudinary_image_thumbnail.url
        elif urls["original"]:
            urls["thumbnail"] = urls["original"]

        return urls

    @staticmethod
    def upload_podcast_cover_image_to_cloudinary(
        podcast_instance, image_field="cover_image"
    ):
        """Upload l'image de couverture d'un podcast vers Cloudinary avec différentes versions"""
        if not hasattr(podcast_instance, image_field) or not getattr(
            podcast_instance, image_field
        ):
            return False

        try:
            image_file = getattr(podcast_instance, image_field)

            # Obtenir le chemin du fichier
            image_path = image_file.path

            # Uploader l'image originale
            upload_result = cloudinary.uploader.upload(
                image_path,
                resource_type="image",
                folder="podcast_covers/original",
                public_id=f"podcast_cover_{podcast_instance.id}_{podcast_instance.slug}",
                overwrite=True,
            )

            # Stocker l'ID public Cloudinary
            podcast_instance.cover_image_cloudinary_public_id = upload_result[
                "public_id"
            ]

            # Enregistrer l'image originale dans le champ CloudinaryField
            podcast_instance.cloudinary_cover_image = upload_result["public_id"]

            # Créer et enregistrer la version large (pour la page de détail)
            large_result = cloudinary.uploader.upload(
                image_path,
                resource_type="image",
                folder="podcast_covers/large",
                public_id=f"podcast_cover_large_{podcast_instance.id}_{podcast_instance.slug}",
                overwrite=True,
                transformation=[
                    {"width": 800, "crop": "limit"},
                    {"quality": "auto"},
                    {"fetch_format": "auto"},
                ],
            )
            podcast_instance.cloudinary_cover_image_large = large_result["public_id"]

            # Créer et enregistrer la vignette (pour les listes/grilles)
            thumbnail_result = cloudinary.uploader.upload(
                image_path,
                resource_type="image",
                folder="podcast_covers/thumbnails",
                public_id=f"podcast_cover_thumbnail_{podcast_instance.id}_{podcast_instance.slug}",
                overwrite=True,
                transformation=[
                    {"width": 400, "height": 400, "crop": "fill"},
                    {"quality": "auto"},
                    {"fetch_format": "auto"},
                ],
            )
            podcast_instance.cloudinary_cover_image_thumbnail = thumbnail_result[
                "public_id"
            ]

            # Enregistrer les modifications
            podcast_instance.save(
                update_fields=[
                    "cover_image_cloudinary_public_id",
                    "cloudinary_cover_image",
                    "cloudinary_cover_image_large",
                    "cloudinary_cover_image_thumbnail",
                ]
            )

            return True

        except Exception as e:
            logger.error(
                f"Erreur lors de l'upload de l'image de couverture vers Cloudinary: {str(e)}"
            )
            return False
