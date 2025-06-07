# content/views.py
from rest_framework import viewsets, mixins, filters, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from authentication.models import User
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Tag, UserProfile, Post, Comment, Podcast, Video
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    CategorySerializer,
    TagSerializer,
    PostListSerializer,
    PostDetailSerializer,
    CommentSerializer,
    PodcastListSerializer,
    PodcastDetailSerializer,
    PodcastUploadSerializer,
    VideoListSerializer,
    VideoDetailSerializer,
)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "first_name", "last_name"]


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Ce viewset est maintenu pour la compatibilité avec le code existant,
    mais utilise directement le modèle User au lieu de UserProfile.
    """

    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "role"]


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.filter(is_published=True).order_by("-published_at")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = [
        "categories__slug",
        "tags__slug",
        "author__username",
        "is_featured",
    ]
    search_fields = ["title", "content", "excerpt"]
    lookup_field = "slug"

    # Ajouter cette propriété pour désactiver le formulaire de filtrage
    # filter_form_template = None

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PostDetailSerializer
        return PostListSerializer
    
    # perform_create est utilisé pour associer l'auteur du post à l'utilisateur connecté
    def perqform_create(self, serializer):
        serializer.save(author=self.request.user)


class PodcastViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = [
        "categories__slug",
        "host__username",
        "is_featured",
        "season",
        "episode",
    ]
    search_fields = ["title", "description"]
    lookup_field = "slug"
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Si l'utilisateur est authentifié et qu'il s'agit de ses podcasts, montrer aussi les non publiés
        if self.request.user.is_authenticated and self.action in ["list", "retrieve"]:
            user_podcasts = Podcast.objects.filter(host=self.request.user)
            public_podcasts = Podcast.objects.filter(is_published=True)
            return (
                (user_podcasts | public_podcasts).distinct().order_by("-published_at")
            )
        # Sinon, ne montrer que les podcasts publiés
        return Podcast.objects.filter(is_published=True).order_by("-published_at")

    def get_serializer_class(self):
        if (
            self.action == "create"
            or self.action == "update"
            or self.action == "partial_update"
        ):
            return PodcastUploadSerializer
        elif self.action == "retrieve":
            return PodcastDetailSerializer
        return PodcastListSerializer

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)


class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Video.objects.filter(is_published=True).order_by("-published_at")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["categories__slug", "presenter__username", "is_featured"]
    search_fields = ["title", "description"]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return VideoDetailSerializer
        return VideoListSerializer


class CommentViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)





# Add these imports and view to your existing views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from .tasks import test_celery_task

@api_view(['GET'])
@permission_classes([IsAdminUser])
def test_celery(request):
    """
    Test endpoint to trigger a Celery task and validate the Celery setup.
    Only accessible to admin users.
    """
    # Schedule the task to run immediately
    task = test_celery_task.delay(name=request.query_params.get('name', 'User'))
    
    return Response({
        'message': 'Celery task triggered successfully',
        'task_id': task.id,
        'status': 'The task is being processed asynchronously'
    })