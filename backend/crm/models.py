import uuid

from django.db import models

# D1 スキーマ (packages/db/schema.sql) の friends / tags / friend_tags /
# broadcasts に対応する Django モデル。ID は UUID (D1 の TEXT UUID 相当)。

MESSAGE_TYPE_CHOICES = (
    ("text", "text"),
    ("image", "image"),
    ("flex", "flex"),
)


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=20, default="#3B82F6")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tags"
        ordering = ["created_at"]

    def __str__(self):
        return self.name


class Friend(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line_user_id = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=255, blank=True, default="")
    picture_url = models.TextField(null=True, blank=True)
    status_message = models.TextField(null=True, blank=True)
    is_following = models.BooleanField(default=True)
    user_id = models.CharField(max_length=64, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ref_code = models.CharField(max_length=255, null=True, blank=True)
    score = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag, through="FriendTag", related_name="friends")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "friends"
        ordering = ["-created_at"]

    def __str__(self):
        return self.display_name or self.line_user_id


class FriendTag(models.Model):
    """友だち×タグの中間テーブル。"""

    friend = models.ForeignKey(Friend, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "friend_tags"
        unique_together = ("friend", "tag")


class Broadcast(models.Model):
    TARGET_TYPE_CHOICES = (
        ("all", "all"),
        ("tag", "tag"),
        ("segment", "segment"),
        ("multi-account-dedup", "multi-account-dedup"),
    )
    STATUS_CHOICES = (
        ("draft", "draft"),
        ("scheduled", "scheduled"),
        ("sending", "sending"),
        ("sent", "sent"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    message_content = models.TextField()
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES, default="all")
    target_tag = models.ForeignKey(
        Tag, on_delete=models.SET_NULL, null=True, blank=True, related_name="broadcasts"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    total_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "broadcasts"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# ----------------------------------------------------------------------------
# 未移植機能の追加 (templates / auto-replies / scenarios / chats / messages)
# ----------------------------------------------------------------------------

class Template(models.Model):
    """メッセージテンプレート。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, default="general")
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default="text")
    message_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "templates"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class AutoReply(models.Model):
    """キーワード自動応答ルール。"""

    MATCH_TYPE_CHOICES = (("exact", "exact"), ("contains", "contains"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    keyword = models.CharField(max_length=255)
    match_type = models.CharField(max_length=10, choices=MATCH_TYPE_CHOICES, default="contains")
    response_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default="text")
    response_content = models.TextField()
    template = models.ForeignKey(
        Template, on_delete=models.SET_NULL, null=True, blank=True, related_name="auto_replies"
    )
    line_account_id = models.CharField(max_length=64, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auto_replies"
        ordering = ["-created_at"]

    def __str__(self):
        return self.keyword


class Scenario(models.Model):
    """ステップ配信シナリオ。"""

    TRIGGER_CHOICES = (
        ("friend_add", "friend_add"),
        ("tag_added", "tag_added"),
        ("manual", "manual"),
    )
    DELIVERY_MODE_CHOICES = (
        ("relative", "relative"),
        ("elapsed", "elapsed"),
        ("absolute_time", "absolute_time"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_CHOICES)
    trigger_tag = models.ForeignKey(
        Tag, on_delete=models.SET_NULL, null=True, blank=True, related_name="trigger_scenarios"
    )
    line_account_id = models.CharField(max_length=64, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    delivery_mode = models.CharField(max_length=20, choices=DELIVERY_MODE_CHOICES, default="relative")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scenarios"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ScenarioStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name="steps")
    step_order = models.IntegerField()
    delay_minutes = models.IntegerField(default=0)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default="text")
    message_content = models.TextField()
    offset_days = models.IntegerField(null=True, blank=True)
    offset_minutes = models.IntegerField(null=True, blank=True)
    delivery_time = models.CharField(max_length=5, null=True, blank=True)  # "HH:MM"
    template = models.ForeignKey(
        Template, on_delete=models.SET_NULL, null=True, blank=True, related_name="scenario_steps"
    )
    on_reach_tag = models.ForeignKey(
        Tag, on_delete=models.SET_NULL, null=True, blank=True, related_name="reach_steps"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scenario_steps"
        ordering = ["step_order"]
        unique_together = ("scenario", "step_order")


class FriendScenario(models.Model):
    """友だちのシナリオ購読 (enrollment)。"""

    STATUS_CHOICES = (
        ("active", "active"),
        ("paused", "paused"),
        ("completed", "completed"),
        ("delivering", "delivering"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    friend = models.ForeignKey(Friend, on_delete=models.CASCADE, related_name="scenario_enrollments")
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name="enrollments")
    current_step_order = models.IntegerField(default=0)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="active")
    started_at = models.DateTimeField(auto_now_add=True)
    next_delivery_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "friend_scenarios"


class Chat(models.Model):
    """友だちとの対話スレッド (1対1サポート)。"""

    STATUS_CHOICES = (
        ("unread", "unread"),
        ("in_progress", "in_progress"),
        ("resolved", "resolved"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    friend = models.OneToOneField(Friend, on_delete=models.CASCADE, related_name="chat")
    operator_id = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="unread")
    notes = models.TextField(blank=True, default="")
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chats"
        ordering = ["-last_message_at"]


class Message(models.Model):
    """送受信メッセージログ (messages_log)。"""

    DIRECTION_CHOICES = (("incoming", "incoming"), ("outgoing", "outgoing"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    friend = models.ForeignKey(Friend, on_delete=models.CASCADE, related_name="messages")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    message_type = models.CharField(max_length=10, default="text")
    content = models.TextField()
    delivery_type = models.CharField(max_length=10, null=True, blank=True)  # push / reply / test
    line_account_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages_log"
        ordering = ["created_at"]


class LineSettings(models.Model):
    """
    LINE 連携設定 (シングルトン: id=1 の1行のみ)。
    管理画面から登録・更新する。空欄の項目は環境変数にフォールバックする。
    """

    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    line_channel_access_token = models.TextField(blank=True, default="")
    line_channel_secret = models.CharField(max_length=255, blank=True, default="")
    relay_shared_secret = models.CharField(max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "line_settings"

    def __str__(self):
        return "LINE 設定"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


class LineAccount(models.Model):
    """
    LINE 公式アカウント (マルチアカウント対応)。
    管理画面「LINEアカウント管理」から登録する。
    Webhook の署名検証・メッセージ送信はこのアカウントの資格情報を使う。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel_id = models.CharField(max_length=255, unique=True)  # Messaging API Channel ID
    name = models.CharField(max_length=255)
    channel_access_token = models.TextField(blank=True, default="")
    channel_secret = models.CharField(max_length=255, blank=True, default="")
    login_channel_id = models.CharField(max_length=255, null=True, blank=True)
    login_channel_secret = models.CharField(max_length=255, null=True, blank=True)
    liff_id = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    role = models.CharField(max_length=100, null=True, blank=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "line_accounts"
        ordering = ["display_order", "created_at"]

    def __str__(self):
        return self.name
