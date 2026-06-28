from django.urls import path

from . import views

# プレフィックスなし (ルート直下)。config 側で path("", include("publicapi.urls")) で登録する。
urlpatterns = [
    path("auth/line", views.auth_line),
    path("auth/callback", views.auth_callback),
    path("r/<str:ref_code>", views.tracking_redirect),
]
