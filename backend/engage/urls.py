from django.urls import path

from . import views

# プレフィックス: /api/ (config/urls.py 側で include 想定)
# 注意: 静的セグメント (rules 等) を UUID パターンより先に定義する。
urlpatterns = [
    # Reminders (+ steps)
    path("reminders", views.reminders_list),
    path("reminders/<uuid:id>", views.reminder_detail),
    path("reminders/<uuid:id>/steps", views.reminder_steps),
    path("reminders/<uuid:id>/steps/<uuid:step_id>", views.reminder_step_detail),
    # Webhooks (incoming / outgoing)
    path("webhooks/incoming", views.incoming_webhooks_list),
    path("webhooks/incoming/<uuid:id>", views.incoming_webhook_detail),
    path("webhooks/outgoing", views.outgoing_webhooks_list),
    path("webhooks/outgoing/<uuid:id>", views.outgoing_webhook_detail),
    # Notifications (+ rules)
    path("notifications", views.notifications_list),
    path("notifications/rules", views.notification_rules_list),
    path("notifications/rules/<uuid:id>", views.notification_rule_detail),
]
