from django.urls import path

from . import views
from . import webhook

# プレフィックス: /api/
# 注意: 静的セグメント (count 等) を UUID パターンより先に定義する。
urlpatterns = [
    # Friends
    path("friends", views.friends_list),
    path("friends/count", views.friends_count),
    path("friends/<uuid:friend_id>", views.friend_detail),
    path("friends/<uuid:friend_id>/tags", views.friend_add_tag),
    path("friends/<uuid:friend_id>/tags/<uuid:tag_id>", views.friend_remove_tag),
    path("friends/<uuid:friend_id>/rich-menu", views.friend_rich_menu),
    path("friends/<uuid:friend_id>/score", views.friend_score),
    path("friends/<uuid:friend_id>/messages", views.friend_messages),
    # Tags
    path("tags", views.tags_list),
    path("tags/<uuid:tag_id>", views.tag_detail),
    # Broadcasts
    path("broadcasts", views.broadcasts_list),
    path("broadcasts/dedup-preview", views.broadcast_dedup_preview),
    path("broadcasts/<uuid:broadcast_id>", views.broadcast_detail),
    path("broadcasts/<uuid:broadcast_id>/send", views.broadcast_send),
    path("broadcasts/<uuid:broadcast_id>/send-segment", views.broadcast_send_segment),
    path("broadcasts/<uuid:broadcast_id>/insight", views.broadcast_insight),
    path("broadcasts/<uuid:broadcast_id>/fetch-insight", views.broadcast_fetch_insight),
    path("broadcasts/<uuid:broadcast_id>/test-send", views.broadcast_test_send),
    path("broadcasts/<uuid:broadcast_id>/progress", views.broadcast_progress),
    path("broadcasts/<uuid:broadcast_id>/preview-count", views.broadcast_preview_count),
    path("broadcasts/<uuid:broadcast_id>/per-account-stats", views.broadcast_per_account_stats),
    # Templates
    path("templates", views.templates_list),
    path("templates/<uuid:template_id>/usages", views.template_usages),
    path("templates/<uuid:template_id>", views.template_detail),
    # Auto-replies
    path("auto-replies", views.auto_replies_list),
    path("auto-replies/<uuid:auto_reply_id>", views.auto_reply_detail),
    # Scenarios (+ steps)
    path("scenarios", views.scenarios_list),
    path("scenarios/<uuid:scenario_id>", views.scenario_detail),
    path("scenarios/<uuid:scenario_id>/steps", views.scenario_steps),
    path("scenarios/<uuid:scenario_id>/steps/reorder", views.scenario_steps_reorder),
    path("scenarios/<uuid:scenario_id>/steps/<uuid:step_id>", views.scenario_step_detail),
    path("scenarios/<uuid:scenario_id>/preview", views.scenario_preview),
    path("scenarios/<uuid:scenario_id>/stats", views.scenario_stats),
    # Chats
    path("chats", views.chats_list),
    path("chats/<uuid:chat_id>", views.chat_detail),
    path("chats/<uuid:chat_id>/send", views.chat_send),
    path("chats/<uuid:chat_id>/loading", views.chat_loading),
    # LINE アカウント (マルチアカウント / 「LINEアカウント管理」画面)
    path("line-accounts", views.line_accounts_list),
    path("line-accounts/order", views.line_accounts_order),
    path("line-accounts/<uuid:account_id>", views.line_account_detail),
    # LINE 設定 (中継共有シークレット等 / owner・admin のみ)
    path("settings/line", views.line_settings),
    # LINE webhook 取り込み (中継 Worker から / 共有シークレット認証)
    path("line/webhook", webhook.line_webhook),
]
