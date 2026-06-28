from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view

from common.responses import err, ok

from .models import (
    IncomingWebhook,
    Notification,
    NotificationRule,
    OutgoingWebhook,
    Reminder,
    ReminderStep,
)
from .serializers import (
    IncomingWebhookCreatedSerializer,
    IncomingWebhookSerializer,
    NotificationRuleSerializer,
    NotificationSerializer,
    OutgoingWebhookCreatedSerializer,
    OutgoingWebhookSerializer,
    ReminderDetailSerializer,
    ReminderSerializer,
    ReminderStepSerializer,
)

# 認証はグローバル設定 (IsAuthenticated) により全て JWT 必須。


# ----------------------------------------------------------------------------
# Reminders (+ steps)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def reminders_list(request):
    if request.method == "GET":
        qs = Reminder.objects.all()
        return ok(ReminderSerializer(qs, many=True).data)

    serializer = ReminderSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    reminder = serializer.save()
    return ok(ReminderSerializer(reminder).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def reminder_detail(request, id):
    reminder = get_object_or_404(Reminder, id=id)

    if request.method == "GET":
        return ok(ReminderDetailSerializer(reminder).data)

    if request.method == "DELETE":
        reminder.delete()
        return ok(None)

    serializer = ReminderSerializer(reminder, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(ReminderSerializer(reminder).data)


@api_view(["POST"])
def reminder_steps(request, id):
    reminder = get_object_or_404(Reminder, id=id)
    serializer = ReminderStepSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    step = serializer.save(reminder=reminder)
    return ok(ReminderStepSerializer(step).data, status=201)


@api_view(["PUT", "DELETE"])
def reminder_step_detail(request, id, step_id):
    step = get_object_or_404(ReminderStep, id=step_id, reminder_id=id)
    if request.method == "DELETE":
        step.delete()
        return ok(None)

    serializer = ReminderStepSerializer(step, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(ReminderStepSerializer(step).data)


# ----------------------------------------------------------------------------
# Webhooks — Incoming
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def incoming_webhooks_list(request):
    if request.method == "GET":
        qs = IncomingWebhook.objects.all()
        return ok(IncomingWebhookSerializer(qs, many=True).data)

    serializer = IncomingWebhookSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    webhook = serializer.save(secret=request.data.get("secret", "") or "")
    return ok(IncomingWebhookCreatedSerializer(webhook).data, status=201)


@api_view(["PUT", "DELETE"])
def incoming_webhook_detail(request, id):
    webhook = get_object_or_404(IncomingWebhook, id=id)

    if request.method == "DELETE":
        webhook.delete()
        return ok(None)

    serializer = IncomingWebhookSerializer(webhook, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    # secret はシリアライザ外で明示更新 (空文字での消去は避ける)
    secret = request.data.get("secret")
    if secret:
        webhook.secret = secret
        webhook.save(update_fields=["secret", "updated_at"])
    return ok(IncomingWebhookSerializer(webhook).data)


# ----------------------------------------------------------------------------
# Webhooks — Outgoing
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def outgoing_webhooks_list(request):
    if request.method == "GET":
        qs = OutgoingWebhook.objects.all()
        return ok(OutgoingWebhookSerializer(qs, many=True).data)

    serializer = OutgoingWebhookSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    webhook = serializer.save(secret=request.data.get("secret", "") or "")
    return ok(OutgoingWebhookCreatedSerializer(webhook).data, status=201)


@api_view(["PUT", "DELETE"])
def outgoing_webhook_detail(request, id):
    webhook = get_object_or_404(OutgoingWebhook, id=id)

    if request.method == "DELETE":
        webhook.delete()
        return ok(None)

    serializer = OutgoingWebhookSerializer(webhook, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    secret = request.data.get("secret")
    if secret:
        webhook.secret = secret
        webhook.save(update_fields=["secret", "updated_at"])
    return ok(OutgoingWebhookSerializer(webhook).data)


# ----------------------------------------------------------------------------
# Notifications (+ rules)
# ----------------------------------------------------------------------------
@api_view(["GET"])
def notifications_list(request):
    qs = Notification.objects.all()

    status = request.query_params.get("status")
    if status:
        qs = qs.filter(status=status)

    event_type = request.query_params.get("eventType")
    if event_type:
        qs = qs.filter(event_type=event_type)

    limit = request.query_params.get("limit")
    if limit:
        try:
            qs = qs[: int(limit)]
        except (TypeError, ValueError):
            pass

    return ok(NotificationSerializer(qs, many=True).data)


@api_view(["GET", "POST"])
def notification_rules_list(request):
    if request.method == "GET":
        qs = NotificationRule.objects.all()
        return ok(NotificationRuleSerializer(qs, many=True).data)

    serializer = NotificationRuleSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    rule = serializer.save()
    # TODO: 実送信 (ルール発火時の通知配信) は別途実装する。
    return ok(NotificationRuleSerializer(rule).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def notification_rule_detail(request, id):
    rule = get_object_or_404(NotificationRule, id=id)

    if request.method == "GET":
        return ok(NotificationRuleSerializer(rule).data)

    if request.method == "DELETE":
        rule.delete()
        return ok(None)

    serializer = NotificationRuleSerializer(rule, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(NotificationRuleSerializer(rule).data)
