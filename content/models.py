# content/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from cloudinary.models import CloudinaryField
import cloudinary
import logging

logger = logging.getLogger(__name__)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """
    Modèle de profil utilisateur qui contient les informations supplémentaires
    spécifiques au profil public et qui ne sont pas directement liées à l'authentification.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    # L'avatar est déjà dans le modèle User
    bio = models.TextField(max_length=500, blank=True)
    website = models.URLField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    twitter = models.URLField(blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    role = models.CharField(max_length=50, default="reader")

    # Champs supplémentaires pour le profil public
    headline = models.CharField(
        max_length=255, blank=True, help_text="Courte description professionnelle"
    )
    interests = models.TextField(
        blank=True, help_text="Centres d'intérêt et compétences"
    )
    is_public = models.BooleanField(
        default=True, help_text="Si le profil est visible publiquement"
    )

    def __str__(self):
        return f"{self.user.username}'s profile"

    def save(self, *args, **kwargs):
        """
        Lors de la sauvegarde, synchroniser certains champs avec le modèle User
        pour assurer la cohérence pendant la période de transition
        """
        # Si le profil est nouveau (pas encore sauvegardé)
        if not self.pk:
            # Copier les valeurs du modèle User si elles existent et que les champs du profil sont vides
            if hasattr(self.user, "twitter") and not self.twitter and self.user.twitter:
                self.twitter = self.user.twitter

            if hasattr(self.user, "github") and not self.github and self.user.github:
                self.github = self.user.github

            if (
                hasattr(self.user, "linkedin")
                and not self.linkedin
                and self.user.linkedin
            ):
                self.linkedin = self.user.linkedin

            if hasattr(self.user, "role") and not self.role and self.user.role:
                self.role = self.user.role

        super().save(*args, **kwargs)


class Post(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)

    # Champ pour l'ancienne méthode d'upload (conservé pour compatibilité)
    featured_image = models.ImageField(upload_to="posts/", blank=True, null=True)

    # Cloudinary public_id pour référence et suppression
    cloudinary_public_id = models.CharField(max_length=255, blank=True, default="")

    # Version originale de l'image
    cloudinary_image = CloudinaryField(
        "post_featured_image",
        resource_type="image",
        folder="posts/original",
        null=True,
        blank=True,
    )

    # Version pour affichage principal (page de détail)
    cloudinary_image_large = CloudinaryField(
        "post_featured_image_large",
        resource_type="image",
        folder="posts/large",
        null=True,
        blank=True,
        transformation=[
            {"width": 1200, "crop": "limit"},
            {"quality": "auto"},
            {"fetch_format": "auto"},
        ],
    )

    # Version pour les listes/grilles de posts
    cloudinary_image_thumbnail = CloudinaryField(
        "post_featured_image_thumbnail",
        resource_type="image",
        folder="posts/thumbnails",
        null=True,
        blank=True,
        transformation=[
            {"width": 400, "height": 300, "crop": "fill"},
            {"quality": "auto"},
            {"fetch_format": "auto"},
        ],
    )

    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    categories = models.ManyToManyField(Category, related_name="posts")
    tags = models.ManyToManyField(Tag, related_name="posts")
    likes_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)  # Nombre de vues
    reading_time = models.PositiveIntegerField(default=0)  # en minutes
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)

    # Champs SEO
    meta_title = models.CharField(
        max_length=60,
        blank=True,
        help_text="Titre SEO (60 caractères max pour un bon référencement)",
    )
    meta_description = models.TextField(
        max_length=160,
        blank=True,
        help_text="Description SEO (160 caractères max pour un bon référencement)",
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Génération automatique des champs SEO s'ils sont vides
        if not self.meta_title:
            self.meta_title = self.title[:60]  # Limiter à 60 caractères

        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]  # Limiter à 160 caractères

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Supprimer les images Cloudinary lors de la suppression du post"""
        if self.cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(
                    self.cloudinary_public_id, resource_type="image"
                )
            except Exception as e:
                logger.error(
                    f"Erreur lors de la suppression de l'image Cloudinary: {str(e)}"
                )
        super().delete(*args, **kwargs)

    @property
    def image_urls(self):
        """Retourne un dictionnaire avec les URL des différentes versions de l'image"""
        urls = {"original": "", "large": "", "thumbnail": ""}

        # URL de l'image originale
        if hasattr(self, "cloudinary_image") and self.cloudinary_image:
            urls["original"] = self.cloudinary_image.url
        elif self.featured_image:
            urls["original"] = self.featured_image.url

        # URL de l'image large
        if hasattr(self, "cloudinary_image_large") and self.cloudinary_image_large:
            urls["large"] = self.cloudinary_image_large.url
        elif urls["original"]:
            urls["large"] = urls["original"]

        # URL de la vignette
        if (
            hasattr(self, "cloudinary_image_thumbnail")
            and self.cloudinary_image_thumbnail
        ):
            urls["thumbnail"] = self.cloudinary_image_thumbnail.url
        elif urls["original"]:
            urls["thumbnail"] = urls["original"]

        return urls

    def increment_views(self):
        """Incrémente le nombre de vues du post"""
        self.views_count += 1
        self.save(update_fields=["views_count"])


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"


class Podcast(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    # Utiliser FileField pour l'upload temporaire
    audio_file = models.FileField(
        upload_to="temp_podcasts/",
        help_text="Formats acceptés : MP3, WAV, M4A, OGG, WEBM",
        null=True,
        blank=True,
    )

    # URLs et identifiants Cloudinary
    cloudinary_url = models.URLField(max_length=500, blank=True, default="")
    cloudinary_public_id = models.CharField(max_length=255, blank=True, default="")

    duration = models.PositiveIntegerField(null=True, blank=True)  # en secondes

    # Champ pour l'ancienne méthode d'upload (conservé pour compatibilité)
    cover_image = models.ImageField(upload_to="podcast_covers/", blank=True, null=True)

    # Cloudinary public_id pour l'image de couverture
    cover_image_cloudinary_public_id = models.CharField(
        max_length=255, blank=True, default=""
    )

    # Version originale de l'image de couverture
    cloudinary_cover_image = CloudinaryField(
        "podcast_cover_image",
        resource_type="image",
        folder="podcast_covers/original",
        null=True,
        blank=True,
    )

    # Version pour affichage principal (page de détail)
    cloudinary_cover_image_large = CloudinaryField(
        "podcast_cover_image_large",
        resource_type="image",
        folder="podcast_covers/large",
        null=True,
        blank=True,
        transformation=[
            {"width": 800, "crop": "limit"},
            {"quality": "auto"},
            {"fetch_format": "auto"},
        ],
    )

    # Version pour les listes/grilles de podcasts
    cloudinary_cover_image_thumbnail = CloudinaryField(
        "podcast_cover_image_thumbnail",
        resource_type="image",
        folder="podcast_covers/thumbnails",
        null=True,
        blank=True,
        transformation=[
            {"width": 400, "height": 400, "crop": "fill"},
            {"quality": "auto"},
            {"fetch_format": "auto"},
        ],
    )
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hosted_podcasts",
    )
    guests = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="podcast_appearances", blank=True
    )
    categories = models.ManyToManyField(Category, related_name="podcasts")
    plays_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    season = models.PositiveIntegerField(default=1)
    episode = models.PositiveIntegerField(default=1)
    is_processed = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    transcript = models.TextField(blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Supprimer le fichier audio et les images Cloudinary lors de la suppression du podcast"""
        if self.cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(
                    self.cloudinary_public_id, resource_type="video"
                )
            except Exception as e:
                logger.error(
                    f"Erreur lors de la suppression du fichier audio Cloudinary: {str(e)}"
                )

        # Supprimer également l'image de couverture si elle existe
        if self.cover_image_cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(
                    self.cover_image_cloudinary_public_id, resource_type="image"
                )
            except Exception as e:
                logger.error(
                    f"Erreur lors de la suppression de l'image de couverture Cloudinary: {str(e)}"
                )

        super().delete(*args, **kwargs)

    @property
    def cover_image_urls(self):
        """Retourne un dictionnaire avec les URLs des différentes versions de l'image de couverture"""
        # Si nous avons des images Cloudinary, les utiliser en priorité
        if self.cloudinary_cover_image and self.cloudinary_cover_image.url:
            return {
                "original": str(self.cloudinary_cover_image.url),
                "large": str(
                    self.cloudinary_cover_image_large.url
                    if self.cloudinary_cover_image_large
                    else self.cloudinary_cover_image.url
                ),
                "thumbnail": str(
                    self.cloudinary_cover_image_thumbnail.url
                    if self.cloudinary_cover_image_thumbnail
                    else self.cloudinary_cover_image.url
                ),
            }
        # Sinon, utiliser l'image classique si disponible
        elif self.cover_image:
            return {
                "original": self.cover_image.url,
                "large": self.cover_image.url,
                "thumbnail": self.cover_image.url,
            }
        # Si aucune image n'est disponible
        return {"original": "", "large": "", "thumbnail": ""}

    @property
    def audio_url(self):
        """Retourne l'URL du fichier audio"""
        return self.cloudinary_url or (self.audio_file.url if self.audio_file else "")


class Video(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    video_url = models.URLField()
    thumbnail = models.ImageField(upload_to="video_thumbnails/", blank=True, null=True)
    duration = models.PositiveIntegerField(
        help_text="Durée en secondes", null=True, blank=True
    )
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    presenter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="videos"
    )
    categories = models.ManyToManyField(Category, related_name="videos")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
