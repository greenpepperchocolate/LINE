import uuid

from django.db import models

# 管理画面「イベント予約 (events)」の Django モデル。
# 旧 Cloudflare Workers + D1 (SQLite) スキーマに対応。
# フロント (apps/web の EventListItem / EventDetail / EventSlot /
# EventBookingItem 型) は snake_case フィールドと 0/1 整数フラグを使うため、
# モデルも snake_case + IntegerField (フラグ) で揃える。


class Event(models.Model):
    """予約可能なイベント。"""

    TARGET_TYPE_CHOICES = (
        ("single", "single"),
        ("multi-account-dedup", "multi-account-dedup"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    venue_name = models.CharField(max_length=255, null=True, blank=True)
    venue_url = models.TextField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    description_centered = models.IntegerField(default=0)
    max_bookings_per_friend = models.IntegerField(null=True, blank=True)
    requires_approval = models.IntegerField(default=0)
    cancel_deadline_hours_before = models.IntegerField(null=True, blank=True)
    reminder_day_before_enabled = models.IntegerField(default=0)
    reminder_hours_before = models.IntegerField(null=True, blank=True)
    is_published = models.IntegerField(default=0)
    sort_order = models.IntegerField(default=0)
    # マルチアカウント (broadcasts と同パターン)。JSON 配列を保持する。
    target_type = models.CharField(max_length=32, choices=TARGET_TYPE_CHOICES, default="single")
    account_ids = models.JSONField(null=True, blank=True)
    dedup_priority = models.JSONField(null=True, blank=True)
    line_account_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "events"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.name


class EventSlot(models.Model):
    """イベントの開催枠 (日時 + 定員)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="slots")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.IntegerField(null=True, blank=True)
    is_active = models.IntegerField(default=1)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "event_slots"
        ordering = ["sort_order", "starts_at"]

    def __str__(self):
        return f"{self.event_id} @ {self.starts_at}"


class EventBooking(models.Model):
    """イベント予約 (友だちからの申し込み)。"""

    STATUS_CHOICES = (
        ("pending", "pending"),
        ("confirmed", "confirmed"),
        ("rejected", "rejected"),
        ("cancelled", "cancelled"),
        ("attended", "attended"),
        ("no_show", "no_show"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bookings")
    slot = models.ForeignKey(EventSlot, on_delete=models.CASCADE, related_name="bookings")
    # 友だち参照は crm の Friend を使う。
    friend = models.ForeignKey("crm.Friend", on_delete=models.CASCADE, related_name="event_bookings")
    line_account_id = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    customer_note = models.TextField(null=True, blank=True)
    internal_note = models.TextField(null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        db_table = "event_bookings"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.event_id} / {self.friend_id} / {self.status}"
