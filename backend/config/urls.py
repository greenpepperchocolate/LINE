"""ルート URL 設定。"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from common.responses import ok
from publicapi import views as public_views


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """ヘルスチェック (認証不要)。"""
    return ok({"status": "ok"})


urlpatterns = [
    # 自己アップデートのスタブ (Django 非対応)。Django admin より先に定義して
    # /admin/ include に飲み込まれないようにする。
    path("admin/version", public_views.admin_version),
    path("admin/update/history", public_views.admin_update_history),
    path("admin/update/start", public_views.admin_update_start),
    path("admin/update/status/<str:update_id>", public_views.admin_update_status),
    path("admin/", admin.site.urls),
    path("health", health),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("crm.urls")),
    # 未移管機能 (ドメイン別アプリ)
    path("api/", include("engage.urls")),
    path("api/", include("marketing.urls")),
    path("api/", include("richmenu.urls")),
    path("api/", include("booking.urls")),
    path("api/", include("events.urls")),
    path("api/", include("people.urls")),
    path("api/", include("pools.urls")),
    path("api/", include("forms.urls")),
    # 公開ルート (LINE Login OAuth / トラッキングリンク) — ルート直下
    path("", include("publicapi.urls")),
]
