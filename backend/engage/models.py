import uuid

from django.db import models

# D1 スキーマ (packages/db/schema.sql) の reminders / reminder_steps /
# incoming_webhooks / outgoing_webhooks / notification_rules / notifications
# に対応する Django モデル。ID は UUID (D1 の TEXT UUID 相当)。

MESSAGE_TYPE_CHOICES = (
    ("text", "text"),
    ("image", "image"),
    ("flex", "flex"),
)


# ----------------------------------------------------------------------------
# Reminders (+ steps)
# ----------------------------------------------------------------------------
class Reminder(models.Model):
    """リマインダ定義 (ステップ群を持つ)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reminders"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ReminderStep(models.Model):
    """リマインダの 1 ステップ (基準日時からの相対オフセットで配信)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reminder = models.ForeignKey(
        Reminder, on_delete=models.CASCADE, related_name="steps"
    )
    offset_minutes = models.IntegerField()
    message_type = models.CharField(
        max_length=10, choices=MESSAGE_TYPE_CHOICES, default="text"
    )
    message_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reminder_steps"
        ordering = ["offset_minutes"]


# ----------------------------------------------------------------------------
# Webhooks (incoming / outgoing)
# ----------------------------------------------------------------------------
class IncomingWebhook(models.Model):
    """外部システムからの受信 Webhook エンドポイント設定。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, default="custom")
    secret = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "incoming_webhooks"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class OutgoingWebhook(models.Model):
    """イベント発火時に外部 URL へ POST する送信 Webhook 設定。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    url = models.TextField()
    event_types = models.JSONField(default=list, blank=True)
    secret = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "outgoing_webhooks"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------------
# Notifications (+ rules)
# ----------------------------------------------------------------------------
class NotificationRule(models.Model):
    """通知ルール (イベント種別 + 条件 + 配信チャネル)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100)
    conditions = models.JSONField(default=dict, blank=True)
    channels = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_rules"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Notification(models.Model):
    """発火済み通知レコード (履歴 / 配信ステータス)。"""

    STATUS_CHOICES = (
        ("pending", "pending"),
        ("sent", "sent"),
        ("failed", "failed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(
        NotificationRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    event_type = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    body = models.TextField()
    channel = models.CharField(max_length=50)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    metadata = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
