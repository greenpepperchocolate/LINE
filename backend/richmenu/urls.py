from django.urls import path

from . import views

# プレフィックス: /api/
# 注意: 静的セグメント (external / import 等) を <uuid:id> より先に定義する。
urlpatterns = [
    # Rich menu groups: external (LINE 上のメニュー) — UUID パターンより先に
    path("rich-menu-groups/external", views.rich_menu_groups_external),
    path("rich-menu-groups/external/<external_id>", views.rich_menu_groups_external_detail),
    path("rich-menu-groups/import", views.rich_menu_groups_import),
    # Rich menu groups: CRUD
    path("rich-menu-groups", views.rich_menu_groups_list),
    path("rich-menu-groups/<uuid:id>", views.rich_menu_group_detail),
    path("rich-menu-groups/<uuid:id>/publish", views.rich_menu_group_publish),
    path("rich-menu-groups/<uuid:id>/unpublish", views.rich_menu_group_unpublish),
    path("rich-menu-groups/<uuid:id>/apply-to-tag", views.rich_menu_group_apply_to_tag),
    # Message templates
    path("message-templates", views.message_templates_list),
    # Account settings: test recipients
    path("account-settings/test-recipients", views.test_recipients),
    # ページ画像アップロード / external 画像
    path("rich-menu-groups/<uuid:id>/pages/<uuid:page_id>/image", views.rich_menu_page_image),
    path("rich-menu-groups/external/<str:id>/image", views.rich_menu_external_image),
    # リッチメニュー画像配信 (公開 / img src から直接アクセス)
    path("rich-menu-images/<path:key>", views.rich_menu_image),
]
