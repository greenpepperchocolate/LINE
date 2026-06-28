from django.urls import path

from . import views

# プレフィックス: /api/
# 注意: 静的セグメント (me / count / migrations 等) を UUID パターンより先に定義する。
urlpatterns = [
    # Users (cross-account の内部ユーザー)
    path("users", views.users_list),
    path("users-grouped", views.users_grouped),
    path("users/<uuid:user_id>", views.user_detail),
    path("users/<uuid:user_id>/link", views.user_link),
    path("users/<uuid:user_id>/accounts", views.user_accounts),
    # Staff
    path("staff", views.staff_list),
    path("staff/me", views.staff_me),
    path("staff/<uuid:id>", views.staff_detail),
    # Inbox (未返信)
    path("inbox/unanswered/count", views.inbox_unanswered_count),
    path("inbox/unanswered", views.inbox_unanswered),
    # Health / Accounts 移行
    path("accounts/migrations", views.account_migrations),
    path("accounts/migrations/<uuid:id>", views.account_migration_detail),
    path("accounts/<uuid:id>/health", views.account_health),
    path("accounts/<uuid:id>/migrate", views.account_migrate),
]
