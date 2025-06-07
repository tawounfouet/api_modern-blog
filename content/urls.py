# content/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    TagViewSet,
    PostViewSet,
    PodcastViewSet,
    VideoViewSet,
    CommentViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"tags", TagViewSet)
router.register(r"posts", PostViewSet)
router.register(r"podcasts", PodcastViewSet, basename="podcast")
router.register(r"videos", VideoViewSet)
router.register(r"comments", CommentViewSet)


from . import views

urlpatterns = [
    path("", include(router.urls)),
    
    
    path('test-celery/', views.test_celery, name='test-celery'),

]
