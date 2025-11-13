"""
URL configuration for API app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

app_name = "api"

router = DefaultRouter()

# TODO: рауты

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
