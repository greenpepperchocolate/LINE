from django.urls import path

from . import views

# config/urls.py で path("api/", include("events.urls")) として取り込む想定。
# よってここでは /api/ 以降のパス (events/admin/...) を定義する。
# 静的セグメント (notifications/pending) は UUID パターンより先に定義する。
urlpatterns = [
    # 通知 (承認待ち件数) — UUID パターンより先に置く
    path("events/admin/events/notifications/pending", views.notifications_pending),
    # イベント
    path("events/admin/events", views.events_list),
    path("events/admin/events/<uuid:id>", views.event_detail),
    # スロット
    path("events/admin/events/<uuid:id>/slots", views.slots_list),
    path("events/admin/events/<uuid:id>/slots/<uuid:slot_id>", views.slot_detail),
    # 予約
    path("events/admin/events/<uuid:id>/bookings", views.bookings_list),
    path("events/admin/events/<uuid:id>/bookings/<uuid:booking_id>", views.booking_detail),
    path("events/admin/events/<uuid:id>/bookings/<uuid:booking_id>/decide", views.booking_decide),
    path("events/admin/events/<uuid:id>/bookings/<uuid:booking_id>/cancel", views.booking_cancel),
]
