from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

# プレフィックス: /api/auth/
urlpatterns = [
    path("register", views.register),
    path("login", views.login),
    path("me", views.me),
    path("refresh", TokenRefreshView.as_view()),
]
