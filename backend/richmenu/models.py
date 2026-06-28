import uuid

from django.db import models

# 管理画面「リッチメニュー / メッセージテンプレート / アカウント設定」用モデル。
# ID は crm と同じく UUID。LINE アカウントは crm.LineAccount を参照する。


class RichMenuGroup(models.Model):
    """リッチメニュー(グループ)。複数ページを束ねる単位。"""

    SIZE_CHOICES = (("large", "large"), ("compact", "compact"))
    STATUS_CHOICES = (("draft", "draft"), ("published", "published"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        "crm.LineAccount", on_delete=models.CASCADE, related_name="rich_menu_groups"
    )
    name = models.CharField(max_length=255)
    chat_bar_text = models.CharField(max_length=14, default="メニュー")
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default="large")
    # 既定で表示するページ (RichMenuPage の id)。FK 循環を避けるため UUID 直持ち。
    default_page_id = models.UUIDField(null=True, blank=True)
    is_default_for_all = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    publishing_at = models.DateTimeField(null=True, blank=True)
    thumbnail_r2_key = models.CharField(max_length=512, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rich_menu_groups"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class RichMenuPage(models.Model):
    """グループ内の 1 ページ (= LINE 上の 1 つの rich menu)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        RichMenuGroup, on_delete=models.CASCADE, related_name="pages"
    )
    order_index = models.IntegerField(default=0)
    name = models.CharField(max_length=255, blank=True, default="")
    alias_id = models.CharField(max_length=255, blank=True, default="")
    line_richmenu_id = models.CharField(max_length=255, null=True, blank=True)
    image_r2_key = models.CharField(max_length=512, null=True, blank=True)
    image_content_type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rich_menu_pages"
        ordering = ["order_index"]

    def __str__(self):
        return f"{self.group_id}:{self.order_index}"


class RichMenuArea(models.Model):
    """ページ内のタップ領域 (アクション)。"""

    ACTION_TYPE_CHOICES = (
        ("uri", "uri"),
        ("message", "message"),
        ("postback", "postback"),
        ("richmenuswitch", "richmenuswitch"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(
        RichMenuPage, on_delete=models.CASCADE, related_name="areas"
    )
    bounds_x = models.IntegerField(default=0)
    bounds_y = models.IntegerField(default=0)
    bounds_width = models.IntegerField(default=0)
    bounds_height = models.IntegerField(default=0)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES, default="uri")
    action_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rich_menu_areas"
        ordering = ["created_at"]


class MessageTemplate(models.Model):
    """メッセージテンプレート (リッチメニュー等から参照する送信用テンプレート)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    message_type = models.CharField(max_length=20, default="text")
    message_content = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rich_menu_message_templates"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class TestRecipient(models.Model):
    """アカウント設定: テスト配信先 (アカウント × 友だち)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        "crm.LineAccount", on_delete=models.CASCADE, related_name="test_recipients"
    )
    friend = models.ForeignKey(
        "crm.Friend", on_delete=models.CASCADE, related_name="test_recipient_of"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rich_menu_test_recipients"
        unique_together = ("account", "friend")
        ordering = ["created_at"]
