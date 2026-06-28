from rest_framework import serializers

from .models import BookingMenu, BookingRequest, BookingStaff, Shift

# 予約 (Booking) のシリアライザ。
# フロント (apps/web の BookingMenu / BookingStaff / BookingShift / BookingRequest 型) は
# snake_case のフィールドをそのまま受け取るため、CRM のような camelCase マッピングはしない。


class BookingMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingMenu
        fields = (
            "id", "name", "category_label", "description",
            "duration_minutes", "buffer_after_minutes", "base_price",
            "sort_order", "is_active",
        )
        read_only_fields = ("id",)


class BookingStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingStaff
        fields = (
            "id", "name", "display_name", "role", "profile_image_url",
            "bio", "sort_order", "is_designation_optional", "is_active",
        )
        read_only_fields = ("id",)


class BookingShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ("id", "work_date", "start_time", "end_time")
        read_only_fields = ("id",)


class BookingRequestSerializer(serializers.ModelSerializer):
    menu_name = serializers.SerializerMethodField()
    staff_name = serializers.SerializerMethodField()
    friend_name = serializers.SerializerMethodField()

    class Meta:
        model = BookingRequest
        fields = (
            "id", "starts_at", "ends_at", "status",
            "customer_note", "internal_note", "price_at_booking",
            "menu_name", "staff_name", "friend_name",
        )

    def get_menu_name(self, obj):
        return obj.menu.name if obj.menu else ""

    def get_staff_name(self, obj):
        return (obj.staff.display_name or obj.staff.name) if obj.staff else ""

    def get_friend_name(self, obj):
        return obj.friend.display_name if obj.friend else None
