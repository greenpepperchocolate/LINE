from django.urls import path

from . import views

# プレフィックス: /api/  (config.urls の include("...") 配下にマウントされる想定)
# すべて /api/booking/admin/... 配下。アカウントは ?account_id= でスコープする。
# 注意: 静的セグメント (generate / pending-count 等) を UUID パターンより先に定義する。
urlpatterns = [
    # メニュー
    path("booking/admin/menus", views.menus),
    path("booking/admin/menus/<uuid:id>", views.menu_detail),
    # スタッフ
    path("booking/admin/staff", views.staff),
    path("booking/admin/staff/<uuid:id>/menus", views.staff_menus),
    path("booking/admin/staff/<uuid:id>/shifts/generate", views.staff_shifts_generate),
    path("booking/admin/staff/<uuid:id>/shifts", views.staff_shifts),
    path("booking/admin/staff/<uuid:id>/shifts/<uuid:shift_id>", views.staff_shift_detail),
    path("booking/admin/staff/<uuid:id>", views.staff_detail),
    # 予約リクエスト
    path("booking/admin/requests", views.requests_list),
    path("booking/admin/requests/<uuid:id>", views.request_detail),
    # 承認待ち件数
    path("booking/admin/pending-count", views.pending_count),
]
