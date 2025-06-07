# content/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Category, Tag, UserProfile, Post, Comment, Podcast, Video
from helpers._cloudinary.audio_service import CloudinaryAudioService


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "website")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "bio")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "published_at",
        "is_published",
        "is_featured",
        "display_image_preview",
    )
    list_filter = ("is_published", "is_featured", "categories")
    search_fields = ("title", "content", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    filter_horizontal = ("categories", "tags")
    readonly_fields = (
        "cloudinary_public_id",
        "display_image_preview",
        "display_cloudinary_images",
    )

    def display_image_preview(self, obj):
        """Affiche une vignette de l'image dans l'admin"""
        if hasattr(obj, "image_urls") and obj.image_urls["thumbnail"]:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:100px;" />',
                obj.image_urls["thumbnail"],
            )
        elif obj.featured_image:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:100px;" />',
                obj.featured_image.url,
            )
        return "Aucune image disponible"

    display_image_preview.short_description = "Aperçu"

    def display_cloudinary_images(self, obj):
        """Affiche toutes les versions des images Cloudinary"""
        if not hasattr(obj, "image_urls"):
            return "Aucune image disponible"

        urls = obj.image_urls
        html = "<h3>Images Cloudinary</h3>"

        if urls["original"]:
            html += f"""
            <div style="margin-bottom: 15px;">
                <p><strong>Image originale:</strong></p>
                <img src="{urls['original']}" style="max-width:200px;" /><br/>
                <code>{urls['original']}</code>
            </div>
            """

        if urls["large"]:
            html += f"""
            <div style="margin-bottom: 15px;">
                <p><strong>Image large:</strong></p>
                <img src="{urls['large']}" style="max-width:200px;" /><br/>
                <code>{urls['large']}</code>
            </div>
            """

        if urls["thumbnail"]:
            html += f"""
            <div style="margin-bottom: 15px;">
                <p><strong>Image vignette:</strong></p>
                <img src="{urls['thumbnail']}" style="max-width:200px;" /><br/>
                <code>{urls['thumbnail']}</code>
            </div>
            """

        return format_html(html)

    display_cloudinary_images.short_description = "Images Cloudinary"

    def save_model(self, request, obj, form, change):
        """Sauvegarde le modèle"""
        super().save_model(request, obj, form, change)

        # Vérifier si une nouvelle image a été fournie et qu'elle n'est pas déjà sur Cloudinary
        if obj.featured_image and not obj.cloudinary_public_id:
            from helpers._cloudinary.image_service import CloudinaryImageService

            CloudinaryImageService.upload_post_image_to_cloudinary(obj)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "created_at")
    list_filter = ("created_at",)
    search_fields = ("author__username", "content")
    date_hierarchy = "created_at"


@admin.register(Podcast)
class PodcastAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "host",
        "season",
        "episode",
        "published_at",
        "is_featured",
        "is_processed",
        "display_audio_player",
        "display_cover_image",
    )
    list_filter = (
        "is_featured",
        "is_processed",
        "season",
        "categories",
    )
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    filter_horizontal = ("guests", "categories")
    readonly_fields = (
        "cloudinary_url",
        "cloudinary_public_id",
        "cover_image_cloudinary_public_id",
        "display_audio_player",
        "display_cloudinary_cover_images",
    )

    def display_audio_player(self, obj):
        """Affiche un lecteur audio dans l'admin"""
        if obj.audio_url:
            return format_html(
                '<audio controls style="width:300px"><source src="{}" type="audio/mpeg">Votre navigateur ne supporte pas l\'audio HTML5.</audio>',
                obj.audio_url,
            )
        return "Aucun fichier audio disponible"

    display_audio_player.short_description = "Lecteur audio"

    def display_cover_image(self, obj):
        """Affiche l'image de couverture du podcast dans la liste d'admin"""
        if hasattr(obj, "cover_image_urls") and obj.cover_image_urls["thumbnail"]:
            return format_html(
                '<img src="{}" width="50" height="50" />',
                obj.cover_image_urls["thumbnail"],
            )
        elif obj.cover_image:
            return format_html(
                '<img src="{}" width="50" height="50" />', obj.cover_image.url
            )
        return "Aucune image"

    display_cover_image.short_description = "Couverture"

    def display_cloudinary_cover_images(self, obj):
        """Affiche toutes les versions des images de couverture Cloudinary dans l'admin"""
        urls = obj.cover_image_urls
        html = ""

        if urls["original"]:
            html += f"""
            <div style="margin-bottom: 15px;">
                <p><strong>Image originale:</strong></p>
                <img src="{urls['original']}" style="max-width:300px;" /><br/>
                <code>{urls['original']}</code>
            </div>
            """

        if urls["large"]:
            html += f"""
            <div style="margin-bottom: 15px;">
                <p><strong>Image large:</strong></p>
                <img src="{urls['large']}" style="max-width:250px;" /><br/>
                <code>{urls['large']}</code>
            </div>
            """

        if urls["thumbnail"]:
            html += f"""
            <div style="margin-bottom: 15px;">
                <p><strong>Image vignette:</strong></p>
                <img src="{urls['thumbnail']}" style="max-width:200px;" /><br/>
                <code>{urls['thumbnail']}</code>
            </div>
            """

        return format_html(html)

    display_cloudinary_cover_images.short_description = (
        "Images de couverture Cloudinary"
    )

    def save_model(self, request, obj, form, change):
        """Sauvegarde le modèle et déclenche l'upload vers Cloudinary si un nouveau fichier est détecté"""
        # Sauvegarder d'abord pour obtenir un ID
        super().save_model(request, obj, form, change)

        # Vérifier si un nouveau fichier audio a été fourni et qu'il n'est pas déjà sur Cloudinary
        if obj.audio_file and not obj.cloudinary_url:
            CloudinaryAudioService.upload_podcast_to_cloudinary(obj)

        # Vérifier si une nouvelle image de couverture a été fournie et qu'elle n'est pas déjà sur Cloudinary
        if obj.cover_image and not obj.cover_image_cloudinary_public_id:
            from helpers._cloudinary.image_service import CloudinaryImageService

            CloudinaryImageService.upload_podcast_cover_image_to_cloudinary(obj)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "presenter", "published_at", "is_published", "is_featured")
    list_filter = ("is_published", "is_featured", "categories")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}


# Signal pour déclencher l'upload Cloudinary lors de la sauvegarde d'un podcast (en dehors de l'admin)
@receiver(post_save, sender=Podcast)
def upload_podcast_to_cloudinary(sender, instance, created, **kwargs):
    """Déclenche l'upload du fichier audio vers Cloudinary après la sauvegarde du podcast"""
    # Vérifier si un fichier audio est présent et qu'il n'a pas encore été traité
    if instance.audio_file and not instance.cloudinary_url:
        CloudinaryAudioService.upload_podcast_to_cloudinary(instance)

    # Vérifier si une image de couverture est présente et qu'elle n'a pas encore été traitée
    if instance.cover_image and not instance.cover_image_cloudinary_public_id:
        from helpers._cloudinary.image_service import CloudinaryImageService

        CloudinaryImageService.upload_podcast_cover_image_to_cloudinary(instance)


# Signal pour déclencher l'upload des images des posts vers Cloudinary
@receiver(post_save, sender=Post)
def upload_post_image_to_cloudinary(sender, instance, created, **kwargs):
    """Déclenche l'upload de l'image vers Cloudinary après la sauvegarde du post"""
    # Vérifier si une image est présente et qu'elle n'a pas encore été traitée
    if instance.featured_image and not instance.cloudinary_public_id:
        from helpers._cloudinary.image_service import CloudinaryImageService

        if CloudinaryImageService.upload_post_image_to_cloudinary(instance):
            # Si l'upload a réussi, on supprime le fichier local
            instance.featured_image.delete(
                save=False
            )  # Ne pas déclencher un autre save
