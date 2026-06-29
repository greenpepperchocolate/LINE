from rest_framework import serializers

from .models import (
    AutoReply,
    Broadcast,
    Chat,
    Friend,
    LineAccount,
    LineSettings,
    Message,
    Scenario,
    ScenarioStep,
    Tag,
    Template,
)

# フロント (@line-crm/shared の型) は camelCase を期待するため、
# 各シリアライザで snake_case のモデルフィールドを camelCase にマップする。


class TagSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "createdAt")


class FriendSerializer(serializers.ModelSerializer):
    lineUserId = serializers.CharField(source="line_user_id", read_only=True)
    displayName = serializers.CharField(source="display_name", read_only=True)
    pictureUrl = serializers.CharField(source="picture_url", read_only=True, allow_null=True)
    statusMessage = serializers.CharField(source="status_message", read_only=True, allow_null=True)
    isFollowing = serializers.BooleanField(source="is_following", read_only=True)
    refCode = serializers.CharField(source="ref_code", read_only=True, allow_null=True)
    userId = serializers.CharField(source="user_id", read_only=True, allow_null=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Friend
        fields = (
            "id", "lineUserId", "displayName", "pictureUrl", "statusMessage",
            "isFollowing", "metadata", "refCode", "userId",
            "createdAt", "updatedAt", "tags",
        )


class BroadcastSerializer(serializers.ModelSerializer):
    messageType = serializers.CharField(source="message_type")
    messageContent = serializers.CharField(source="message_content")
    targetType = serializers.CharField(source="target_type", required=False)
    targetTagId = serializers.PrimaryKeyRelatedField(
        source="target_tag", queryset=Tag.objects.all(),
        required=False, allow_null=True,
    )
    scheduledAt = serializers.DateTimeField(source="scheduled_at", required=False, allow_null=True)
    sentAt = serializers.DateTimeField(source="sent_at", read_only=True, allow_null=True)
    totalCount = serializers.IntegerField(source="total_count", read_only=True)
    successCount = serializers.IntegerField(source="success_count", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    # マルチアカウント系は MVP では未対応のため常に null を返す (フロント型互換)。
    accountIds = serializers.SerializerMethodField()
    dedupPriority = serializers.SerializerMethodField()
    failedAccountIds = serializers.SerializerMethodField()

    class Meta:
        model = Broadcast
        fields = (
            "id", "title", "messageType", "messageContent", "targetType",
            "targetTagId", "status", "scheduledAt", "sentAt",
            "totalCount", "successCount", "createdAt",
            "accountIds", "dedupPriority", "failedAccountIds",
        )

    def get_accountIds(self, obj):
        return None

    def get_dedupPriority(self, obj):
        return None

    def get_failedAccountIds(self, obj):
        return None


# ----------------------------------------------------------------------------
# Templates
# ----------------------------------------------------------------------------
class TemplateSerializer(serializers.ModelSerializer):
    messageType = serializers.CharField(source="message_type")
    messageContent = serializers.CharField(source="message_content")
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    usageCount = serializers.SerializerMethodField()

    class Meta:
        model = Template
        fields = (
            "id", "name", "category", "messageType", "messageContent",
            "usageCount", "createdAt", "updatedAt",
        )

    def get_usageCount(self, obj):
        return obj.auto_replies.count() + obj.scenario_steps.count()


# ----------------------------------------------------------------------------
# Auto-replies
# ----------------------------------------------------------------------------
class AutoReplySerializer(serializers.ModelSerializer):
    matchType = serializers.CharField(source="match_type", required=False)
    responseType = serializers.CharField(source="response_type", required=False)
    responseContent = serializers.CharField(source="response_content")
    templateId = serializers.PrimaryKeyRelatedField(
        source="template", queryset=Template.objects.all(), required=False, allow_null=True
    )
    lineAccountId = serializers.CharField(source="line_account_id", required=False, allow_null=True)
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = AutoReply
        fields = (
            "id", "keyword", "matchType", "responseType", "responseContent",
            "templateId", "lineAccountId", "isActive", "createdAt",
        )


# ----------------------------------------------------------------------------
# Scenarios (+ steps)
# ----------------------------------------------------------------------------
class ScenarioStepSerializer(serializers.ModelSerializer):
    scenarioId = serializers.PrimaryKeyRelatedField(source="scenario", read_only=True)
    stepOrder = serializers.IntegerField(source="step_order")
    messageType = serializers.CharField(source="message_type")
    messageContent = serializers.CharField(source="message_content")
    delayMinutes = serializers.IntegerField(source="delay_minutes", required=False)
    offsetDays = serializers.IntegerField(source="offset_days", required=False, allow_null=True)
    offsetMinutes = serializers.IntegerField(source="offset_minutes", required=False, allow_null=True)
    deliveryTime = serializers.CharField(source="delivery_time", required=False, allow_null=True)
    templateId = serializers.PrimaryKeyRelatedField(
        source="template", queryset=Template.objects.all(), required=False, allow_null=True
    )
    onReachTagId = serializers.PrimaryKeyRelatedField(
        source="on_reach_tag", queryset=Tag.objects.all(), required=False, allow_null=True
    )
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = ScenarioStep
        fields = (
            "id", "scenarioId", "stepOrder", "messageType", "messageContent",
            "delayMinutes", "offsetDays", "offsetMinutes", "deliveryTime",
            "templateId", "onReachTagId", "createdAt",
        )


class ScenarioSerializer(serializers.ModelSerializer):
    triggerType = serializers.CharField(source="trigger_type")
    triggerTagId = serializers.PrimaryKeyRelatedField(
        source="trigger_tag", queryset=Tag.objects.all(), required=False, allow_null=True
    )
    lineAccountId = serializers.CharField(source="line_account_id", required=False, allow_null=True)
    isActive = serializers.BooleanField(source="is_active", required=False)
    deliveryMode = serializers.CharField(source="delivery_mode", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    stepCount = serializers.SerializerMethodField()

    class Meta:
        model = Scenario
        fields = (
            "id", "name", "description", "triggerType", "triggerTagId",
            "lineAccountId", "isActive", "deliveryMode",
            "createdAt", "updatedAt", "stepCount",
        )

    def get_stepCount(self, obj):
        return obj.steps.count()


class ScenarioDetailSerializer(ScenarioSerializer):
    steps = ScenarioStepSerializer(many=True, read_only=True)

    class Meta(ScenarioSerializer.Meta):
        fields = ScenarioSerializer.Meta.fields + ("steps",)


# ----------------------------------------------------------------------------
# Chats (+ messages)
# ----------------------------------------------------------------------------
class MessageSerializer(serializers.ModelSerializer):
    senderType = serializers.SerializerMethodField()
    messageType = serializers.CharField(source="message_type")
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Message
        # direction は吹き出しの左右判定 (outgoing=右 / incoming=左) に使う
        fields = ("id", "content", "messageType", "direction", "senderType", "createdAt")

    def get_senderType(self, obj):
        # incoming = 友だち, outgoing = オペレーター
        return "friend" if obj.direction == "incoming" else "operator"


class ChatSerializer(serializers.ModelSerializer):
    # フロントはチャット識別子に friend_id を使う (id === friendId)。
    id = serializers.SerializerMethodField()
    friendId = serializers.PrimaryKeyRelatedField(source="friend", read_only=True)
    friendName = serializers.SerializerMethodField()
    friendPictureUrl = serializers.SerializerMethodField()
    operatorId = serializers.CharField(source="operator_id", required=False, allow_null=True)
    sendMode = serializers.SerializerMethodField()
    lastMessageAt = serializers.DateTimeField(source="last_message_at", read_only=True, allow_null=True)
    lastMessageContent = serializers.SerializerMethodField()
    lastMessageDirection = serializers.SerializerMethodField()
    lastMessageType = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Chat
        fields = (
            "id", "friendId", "friendName", "friendPictureUrl", "operatorId",
            "status", "notes", "sendMode", "lastMessageAt", "lastMessageContent",
            "lastMessageDirection", "lastMessageType", "createdAt", "updatedAt",
        )

    def get_id(self, obj):
        return str(obj.friend_id)

    def _last_message(self, obj):
        if not hasattr(obj, "_cached_last"):
            obj._cached_last = obj.friend.messages.order_by("-created_at").first()
        return obj._cached_last

    def get_friendName(self, obj):
        return obj.friend.display_name or obj.friend.line_user_id or "LINE友だち"

    def get_friendPictureUrl(self, obj):
        return obj.friend.picture_url

    def get_sendMode(self, obj):
        return "push"

    def get_lastMessageContent(self, obj):
        m = self._last_message(obj)
        return m.content if m else None

    def get_lastMessageDirection(self, obj):
        m = self._last_message(obj)
        return m.direction if m else None

    def get_lastMessageType(self, obj):
        m = self._last_message(obj)
        return m.message_type if m else None


class ChatDetailSerializer(ChatSerializer):
    messages = serializers.SerializerMethodField()

    class Meta(ChatSerializer.Meta):
        fields = ChatSerializer.Meta.fields + ("messages",)

    def get_messages(self, obj):
        qs = obj.friend.messages.all().order_by("created_at")
        return MessageSerializer(qs, many=True).data


# ----------------------------------------------------------------------------
# LINE Settings (管理画面から登録)
# ----------------------------------------------------------------------------
class LineSettingsSerializer(serializers.ModelSerializer):
    lineChannelAccessToken = serializers.CharField(
        source="line_channel_access_token", required=False, allow_blank=True
    )
    lineChannelSecret = serializers.CharField(
        source="line_channel_secret", required=False, allow_blank=True
    )
    relaySharedSecret = serializers.CharField(
        source="relay_shared_secret", required=False, allow_blank=True
    )
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = LineSettings
        fields = (
            "lineChannelAccessToken",
            "lineChannelSecret",
            "relaySharedSecret",
            "updatedAt",
        )


# ----------------------------------------------------------------------------
# LINE Accounts (マルチアカウント / 「LINEアカウント管理」画面)
# ----------------------------------------------------------------------------
class LineAccountSerializer(serializers.ModelSerializer):
    """詳細/作成/更新用 (シークレット含む)。"""

    channelId = serializers.CharField(source="channel_id")
    channelAccessToken = serializers.CharField(source="channel_access_token", required=False, allow_blank=True)
    channelSecret = serializers.CharField(source="channel_secret", required=False, allow_blank=True)
    loginChannelId = serializers.CharField(source="login_channel_id", required=False, allow_null=True, allow_blank=True)
    loginChannelSecret = serializers.CharField(source="login_channel_secret", required=False, allow_null=True, allow_blank=True)
    liffId = serializers.CharField(source="liff_id", required=False, allow_null=True, allow_blank=True)
    isActive = serializers.BooleanField(source="is_active", required=False)
    country = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    role = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    displayOrder = serializers.IntegerField(source="display_order", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = LineAccount
        fields = (
            "id", "channelId", "name", "channelAccessToken", "channelSecret",
            "loginChannelId", "loginChannelSecret", "liffId", "isActive",
            "country", "role", "displayOrder", "createdAt", "updatedAt",
        )


class LineAccountListSerializer(serializers.ModelSerializer):
    """一覧用 (シークレット類は省略)。"""

    channelId = serializers.CharField(source="channel_id")
    displayName = serializers.SerializerMethodField()
    pictureUrl = serializers.SerializerMethodField()
    basicId = serializers.SerializerMethodField()
    loginChannelId = serializers.CharField(source="login_channel_id", allow_null=True)
    liffId = serializers.CharField(source="liff_id", allow_null=True)
    isActive = serializers.BooleanField(source="is_active")
    displayOrder = serializers.IntegerField(source="display_order")
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = LineAccount
        fields = (
            "id", "channelId", "name", "displayName", "pictureUrl", "basicId",
            "loginChannelId", "liffId", "isActive", "country", "role",
            "displayOrder", "createdAt", "updatedAt", "stats",
        )

    def get_displayName(self, obj):
        return obj.name

    def get_pictureUrl(self, obj):
        return None

    def get_basicId(self, obj):
        return None

    def get_stats(self, obj):
        # 友だち等はアカウント横断管理のため当面グローバル集計。
        from django.utils import timezone
        start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return {
            "friendCount": Friend.objects.count(),
            "activeScenarios": Scenario.objects.filter(is_active=True).count(),
            "messagesThisMonth": Message.objects.filter(created_at__gte=start).count(),
        }
