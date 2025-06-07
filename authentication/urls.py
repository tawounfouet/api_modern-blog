from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, user_profile, update_profile

router = DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    # Router URLs
    path("", include(router.urls)),
    # Djoser and JWT auth endpoints
    path("", include("djoser.urls")),
    path("", include("djoser.urls.jwt")),
    # Social auth endpoints
    path("", include("dj_rest_auth.urls")),
    path("registration/", include("dj_rest_auth.registration.urls")),
    # Legacy endpoints (à conserver pour la compatibilité)
    path("profile/", user_profile, name="user-profile"),
    path("profile/update/", update_profile, name="update-profile"),
]
