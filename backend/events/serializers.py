from rest_framework import serializers

from .models import Event, EventBooking, EventSlot

# フロント (apps/web の EventListItem / EventDetail / EventSlot /
# EventBookingItem) は snake_case フィールドを使うため、ここでも snake_case の
# まま出力する (crm の camelCase マッピングとは異なる点に注意)。
# キャンセルされていない予約 (= 枠を消費する状態) の判定に使う。
ACTIVE_BOOKING_STATUSES = ("pending", "confirmed", "attended", "no_show")


class EventSerializer(serializers.ModelSerializer):
    """イベント詳細 / 作成・更新用 (EventDetail)。"""

    class Meta:
        model = Event
        fields = (
            "id", "name", "venue_name", "venue_url", "image_url",
            "description", "description_centered", "max_bookings_per_friend",
            "requires_approval", "cancel_deadline_hours_before",
            "reminder_day_before_enabled", "reminder_hours_before",
            "is_published", "sort_order", "target_type", "account_ids",
            "dedup_priority", "line_account_id", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class EventListSerializer(EventSerializer):
    """一覧用 (EventListItem) — 集計フィールドを付与。"""

    next_slot_starts_at = serializers.SerializerMethodField()
    total_capacity = serializers.SerializerMethodField()
    total_active = serializers.SerializerMethodField()
    pending_count = serializers.SerializerMethodField()

    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + (
            "next_slot_starts_at", "total_capacity", "total_active", "pending_count",
        )

    def get_next_slot_starts_at(self, obj):
        slot = obj.slots.filter(is_active=1).order_by("starts_at").first()
        return slot.starts_at if slot else None

    def get_total_capacity(self, obj):
        caps = [s.capacity for s in obj.slots.all() if s.capacity is not None]
        return sum(caps) if caps else None

    def get_total_active(self, obj):
        return obj.bookings.filter(status__in=ACTIVE_BOOKING_STATUSES).count()

    def get_pending_count(self, obj):
        return obj.bookings.filter(status="pending").count()


class EventSlotSerializer(serializers.ModelSerializer):
    """開催枠 (EventSlot)。"""

    event_id = serializers.PrimaryKeyRelatedField(source="event", read_only=True)
    active_count = serializers.SerializerMethodField()

    class Meta:
        model = EventSlot
        fields = (
            "id", "event_id", "starts_at", "ends_at",
            "capacity", "is_active", "sort_order", "active_count",
        )
        read_only_fields = ("id", "event_id")

    def get_active_count(self, obj):
        return obj.bookings.filter(status__in=ACTIVE_BOOKING_STATUSES).count()


class EventBookingSerializer(serializers.ModelSerializer):
    """予約 (EventBookingItem)。"""

    event_id = serializers.PrimaryKeyRelatedField(source="event", read_only=True)
    slot_id = serializers.PrimaryKeyRelatedField(source="slot", read_only=True)
    friend_id = serializers.PrimaryKeyRelatedField(source="friend", read_only=True)
    slot_starts_at = serializers.DateTimeField(source="slot.starts_at", read_only=True)
    slot_ends_at = serializers.DateTimeField(source="slot.ends_at", read_only=True)
    friend_display_name = serializers.CharField(source="friend.display_name", read_only=True)
    friend_line_user_id = serializers.CharField(source="friend.line_user_id", read_only=True)

    class Meta:
        model = EventBooking
        fields = (
            "id", "event_id", "slot_id", "friend_id", "line_account_id",
            "status", "customer_note", "internal_note",
            "requested_at", "decided_at", "cancelled_at", "cancelled_by",
            "slot_starts_at", "slot_ends_at",
            "friend_display_name", "friend_line_user_id",
        )
        read_only_fields = (
            "id", "event_id", "slot_id", "friend_id", "requested_at",
            "decided_at", "cancelled_at", "cancelled_by",
            "slot_starts_at", "slot_ends_at",
            "friend_display_name", "friend_line_user_id",
        )
