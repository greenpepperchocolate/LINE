from rest_framework import serializers

from .models import (
    IncomingWebhook,
    Notification,
    NotificationRule,
    OutgoingWebhook,
    Reminder,
    ReminderStep,
)

# フロント (@line-crm/shared の型) は camelCase を期待するため、
# 各シリアライザで snake_case のモデルフィールドを camelCase にマップする。


# ----------------------------------------------------------------------------
# Reminders (+ steps)
# ----------------------------------------------------------------------------
class ReminderStepSerializer(serializers.ModelSerializer):
    reminderId = serializers.PrimaryKeyRelatedField(source="reminder", read_only=True)
    offsetMinutes = serializers.IntegerField(source="offset_minutes")
    messageType = serializers.CharField(source="message_type")
    messageContent = serializers.CharField(source="message_content")
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = ReminderStep
        fields = (
            "id", "reminderId", "offsetMinutes", "messageType",
            "messageContent", "createdAt",
        )


class ReminderSerializer(serializers.ModelSerializer):
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Reminder
        fields = ("id", "name", "description", "isActive", "createdAt", "updatedAt")


class ReminderDetailSerializer(ReminderSerializer):
    steps = ReminderStepSerializer(many=True, read_only=True)

    class Meta(ReminderSerializer.Meta):
        fields = ReminderSerializer.Meta.fields + ("steps",)


# ----------------------------------------------------------------------------
# Webhooks — Incoming
# ----------------------------------------------------------------------------
class IncomingWebhookSerializer(serializers.ModelSerializer):
    """一覧 / 取得 / 更新用。raw secret は返さず hasSecret のみ公開する。"""

    sourceType = serializers.CharField(source="source_type", required=False)
    hasSecret = serializers.SerializerMethodField()
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = IncomingWebhook
        fields = (
            "id", "name", "sourceType", "hasSecret",
            "isActive", "createdAt", "updatedAt",
        )

    def get_hasSecret(self, obj):
        return bool(obj.secret)


class IncomingWebhookCreatedSerializer(serializers.ModelSerializer):
    """POST 直後のみ secret を含めて返す (operator がコピーするため)。"""

    sourceType = serializers.CharField(source="source_type")
    isActive = serializers.BooleanField(source="is_active")
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = IncomingWebhook
        fields = ("id", "name", "sourceType", "isActive", "createdAt", "secret")


# ----------------------------------------------------------------------------
# Webhooks — Outgoing
# ----------------------------------------------------------------------------
class OutgoingWebhookSerializer(serializers.ModelSerializer):
    """一覧 / 取得 / 更新用。raw secret は返さず hasSecret のみ公開する。"""

    eventTypes = serializers.JSONField(source="event_types", required=False)
    hasSecret = serializers.SerializerMethodField()
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = OutgoingWebhook
        fields = (
            "id", "name", "url", "eventTypes", "hasSecret",
            "isActive", "createdAt", "updatedAt",
        )

    def get_hasSecret(self, obj):
        return bool(obj.secret)


class OutgoingWebhookCreatedSerializer(serializers.ModelSerializer):
    """POST 直後のみ secret を含めて返す。"""

    eventTypes = serializers.JSONField(source="event_types")
    isActive = serializers.BooleanField(source="is_active")
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = OutgoingWebhook
        fields = ("id", "name", "url", "eventTypes", "isActive", "createdAt", "secret")


# ----------------------------------------------------------------------------
# Notifications (+ rules)
# ----------------------------------------------------------------------------
class NotificationRuleSerializer(serializers.ModelSerializer):
    eventType = serializers.CharField(source="event_type")
    conditions = serializers.JSONField(required=False)
    channels = serializers.JSONField(required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = NotificationRule
        fields = (
            "id", "name", "eventType", "conditions", "channels",
            "isActive", "createdAt", "updatedAt",
        )


class NotificationSerializer(serializers.ModelSerializer):
    ruleId = serializers.PrimaryKeyRelatedField(source="rule", read_only=True)
    eventType = serializers.CharField(source="event_type", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id", "ruleId", "eventType", "title", "body",
            "channel", "status", "metadata", "createdAt",
        )
