# content/serializers.py
from rest_framework import serializers
from authentication.models import User
from django.utils.text import slugify
from .models import Category, Tag, UserProfile, Post, Comment, Podcast, Video


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer de base pour le modèle User.
    Utilisé pour les vues qui n'ont besoin que des informations de base de l'utilisateur.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle UserProfile qui contient les informations étendues du profil.
    Inclut les champs de base du User et les champs spécifiques au profil.
    """

    # Ces champs viennent du modèle User via la relation user
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    avatar = serializers.ImageField(source="user.avatar", read_only=True)
    date_joined = serializers.DateTimeField(source="user.date_joined", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "website",
            "location",
            "date_joined",
            "birth_date",
            "twitter",
            "github",
            "linkedin",
            "role",
            "headline",
            "interests",
            "is_public",
        ]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "author",
            "created_at",
            "updated_at",
            "is_approved",
        ]


class PostListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    featured_image = serializers.SerializerMethodField()
    featured_image_urls = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "featured_image",
            "featured_image_urls",
            "published_at",
            "author",
            "categories",
            "tags",
            "likes_count",
            "views_count",
            "reading_time",
            "is_featured",
            "meta_title",
            "meta_description",
        ]

    def get_featured_image(self, obj):
        """Retourne l'URL de l'image principale (pour compatibilité)"""
        if hasattr(obj, "cloudinary_image") and obj.cloudinary_image:
            return obj.cloudinary_image.url
        if obj.featured_image:
            return obj.featured_image.url
        return None

    def get_featured_image_urls(self, obj):
        """Retourne les URLs des différentes versions d'image"""
        # Vérifier si on a des images Cloudinary
        if hasattr(obj, "cloudinary_image") and obj.cloudinary_image:
            original_url = str(obj.cloudinary_image.url) if obj.cloudinary_image else ""
            large_url = (
                str(obj.cloudinary_image_large.url)
                if obj.cloudinary_image_large
                else original_url
            )
            thumbnail_url = (
                str(obj.cloudinary_image_thumbnail.url)
                if obj.cloudinary_image_thumbnail
                else original_url
            )

            return {
                "original": original_url,
                "large": large_url,
                "thumbnail": thumbnail_url,
            }
        elif obj.featured_image:
            # Fallback pour les images classiques
            image_url = obj.featured_image.url
            return {
                "original": image_url,
                "large": image_url,
                "thumbnail": image_url,
            }
        return {"original": "", "large": "", "thumbnail": ""}


class PostDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    featured_image = serializers.SerializerMethodField()
    featured_image_urls = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "excerpt",
            "featured_image",
            "featured_image_urls",
            "published_at",
            "updated_at",
            "author",
            "categories",
            "tags",
            "comments",
            "likes_count",
            "views_count",
            "reading_time",
            "is_featured",
            "is_published",
            "meta_title",
            "meta_description",
        ]

    def get_featured_image(self, obj):
        """Retourne l'URL de l'image principale (pour compatibilité)"""
        if hasattr(obj, "cloudinary_image") and obj.cloudinary_image:
            return obj.cloudinary_image.url
        if obj.featured_image:
            return obj.featured_image.url
        return None

    def get_featured_image_urls(self, obj):
        """Retourne les URLs des différentes versions d'image"""
        # Vérifier si on a des images Cloudinary
        if hasattr(obj, "cloudinary_image") and obj.cloudinary_image:
            original_url = str(obj.cloudinary_image.url) if obj.cloudinary_image else ""
            large_url = (
                str(obj.cloudinary_image_large.url)
                if obj.cloudinary_image_large
                else original_url
            )
            thumbnail_url = (
                str(obj.cloudinary_image_thumbnail.url)
                if obj.cloudinary_image_thumbnail
                else original_url
            )

            return {
                "original": original_url,
                "large": large_url,
                "thumbnail": thumbnail_url,
            }
        elif obj.featured_image:
            # Fallback pour les images classiques
            image_url = obj.featured_image.url
            return {
                "original": image_url,
                "large": image_url,
                "thumbnail": image_url,
            }
        return {"original": "", "large": "", "thumbnail": ""}


class PodcastListSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()
    cover_image_urls = serializers.SerializerMethodField()

    class Meta:
        model = Podcast
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "cover_image",
            "cover_image_urls",
            "duration",
            "published_at",
            "host",
            "categories",
            "plays_count",
            "is_featured",
            "season",
            "episode",
        ]

    def get_cover_image(self, obj):
        # Logique pour récupérer l'URL de l'image de couverture
        if hasattr(obj, "cloudinary_cover_image") and obj.cloudinary_cover_image:
            return obj.cloudinary_cover_image.url
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def get_cover_image_urls(self, obj):
        """Retourne les URLs des différentes versions d'image"""
        # Vérifier si on a des images Cloudinary
        if hasattr(obj, "cloudinary_cover_image") and obj.cloudinary_cover_image:
            original_url = (
                str(obj.cloudinary_cover_image.url)
                if obj.cloudinary_cover_image
                else ""
            )
            large_url = (
                str(obj.cloudinary_cover_image_large.url)
                if obj.cloudinary_cover_image_large
                else original_url
            )
            thumbnail_url = (
                str(obj.cloudinary_cover_image_thumbnail.url)
                if obj.cloudinary_cover_image_thumbnail
                else original_url
            )

            return {
                "original": original_url,
                "large": large_url,
                "thumbnail": thumbnail_url,
            }
        elif obj.cover_image:
            # Fallback pour les images classiques
            image_url = obj.cover_image.url
            return {
                "original": image_url,
                "large": image_url,
                "thumbnail": image_url,
            }
        return {"original": "", "large": "", "thumbnail": ""}


class PodcastDetailSerializer(serializers.ModelSerializer):
    host = UserProfileSerializer(source="host.profile", read_only=True)
    guests = UserProfileSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()
    cover_image_urls = serializers.SerializerMethodField()
    audio_url = serializers.SerializerMethodField()

    class Meta:
        model = Podcast
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "cover_image",
            "cover_image_urls",
            "audio_url",
            "duration",
            "published_at",
            "updated_at",
            "host",
            "guests",
            "categories",
            "plays_count",
            "is_featured",
            "season",
            "episode",
            "transcript",
        ]

    def get_cover_image(self, obj):
        # Logique pour récupérer l'URL de l'image de couverture
        if hasattr(obj, "cloudinary_cover_image") and obj.cloudinary_cover_image:
            return obj.cloudinary_cover_image.url
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def get_cover_image_urls(self, obj):
        """Retourne les URLs des différentes versions d'image"""
        # Vérifier si on a des images Cloudinary
        if hasattr(obj, "cloudinary_cover_image") and obj.cloudinary_cover_image:
            original_url = (
                str(obj.cloudinary_cover_image.url)
                if obj.cloudinary_cover_image
                else ""
            )
            large_url = (
                str(obj.cloudinary_cover_image_large.url)
                if obj.cloudinary_cover_image_large
                else original_url
            )
            thumbnail_url = (
                str(obj.cloudinary_cover_image_thumbnail.url)
                if obj.cloudinary_cover_image_thumbnail
                else original_url
            )

            return {
                "original": original_url,
                "large": large_url,
                "thumbnail": thumbnail_url,
            }
        elif obj.cover_image:
            # Fallback pour les images classiques
            image_url = obj.cover_image.url
            return {
                "original": image_url,
                "large": image_url,
                "thumbnail": image_url,
            }
        return {"original": "", "large": "", "thumbnail": ""}

    def get_audio_url(self, obj):
        if obj.cloudinary_url:
            return obj.cloudinary_url
        if obj.audio_file:
            return obj.audio_file.url
        return None


class PodcastUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Podcast
        fields = [
            "title",
            "description",
            "audio_file",
            "cover_image",
            "categories",
            "guests",
            "season",
            "episode",
            "is_published",
        ]


class VideoListSerializer(serializers.ModelSerializer):
    presenter = UserSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "video_url",
            "thumbnail",
            "duration",
            "published_at",
            "presenter",
            "categories",
            "views_count",
            "likes_count",
            "is_featured",
        ]


class VideoDetailSerializer(serializers.ModelSerializer):
    presenter = UserProfileSerializer(source="presenter.profile", read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "video_url",
            "thumbnail",
            "duration",
            "published_at",
            "updated_at",
            "presenter",
            "categories",
            "comments",
            "views_count",
            "likes_count",
            "is_featured",
            "transcript",
        ]
