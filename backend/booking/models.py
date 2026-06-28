import uuid

from django.db import models

# 予約管理 (Booking) のモデル群。
# フロント (apps/web の bookingApi / BookingMenu 等の型) は snake_case のフィールド名と
# 0/1 の整数フラグ (is_active 等) を期待するため、CRM とは異なり camelCase 変換はしない。
# 0/1 フラグは IntegerField で保持し、そのまま number として返す。
# 友だち参照は crm.Friend を FK。アカウントスコープは line_account_id (?account_id=) で行う。


class BookingMenu(models.Model):
    """予約メニュー (施術・サービス)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line_account_id = models.CharField(max_length=64, null=True, blank=True)
    name = models.CharField(max_length=255)
    category_label = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=30)
    buffer_after_minutes = models.IntegerField(default=0)
    base_price = models.IntegerField(default=0)
    sort_order = models.IntegerField(default=0)
    is_active = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booking_menus"
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return self.name


class BookingStaff(models.Model):
    """予約を受けるスタッフ。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line_account_id = models.CharField(max_length=64, null=True, blank=True)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, default="")
    role = models.CharField(max_length=255, null=True, blank=True)
    profile_image_url = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    is_designation_optional = models.IntegerField(default=0)
    is_active = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booking_staff"
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return self.display_name or self.name


class StaffMenu(models.Model):
    """スタッフ×メニューの提供可否マトリクス (任意で所要時間/料金を上書き)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(
        BookingStaff, on_delete=models.CASCADE, related_name="staff_menus"
    )
    menu = models.ForeignKey(
        BookingMenu, on_delete=models.CASCADE, related_name="staff_menus"
    )
    is_offered = models.IntegerField(default=1)
    override_duration_minutes = models.IntegerField(null=True, blank=True)
    override_price = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booking_staff_menus"
        unique_together = ("staff", "menu")


class Shift(models.Model):
    """スタッフのシフト (勤務枠)。start_time / end_time は "HH:MM" 文字列。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(
        BookingStaff, on_delete=models.CASCADE, related_name="shifts"
    )
    work_date = models.DateField()
    start_time = models.CharField(max_length=5)  # "HH:MM"
    end_time = models.CharField(max_length=5)  # "HH:MM"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booking_shifts"
        ordering = ["work_date", "start_time"]
        unique_together = ("staff", "work_date", "start_time")


class BookingRequest(models.Model):
    """予約リクエスト (承認/却下フロー)。"""

    STATUS_CHOICES = (
        ("requested", "requested"),
        ("confirmed", "confirmed"),
        ("rejected", "rejected"),
        ("cancelled", "cancelled"),
        ("completed", "completed"),
        ("no_show", "no_show"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line_account_id = models.CharField(max_length=64, null=True, blank=True)
    menu = models.ForeignKey(
        BookingMenu, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="requests",
    )
    staff = models.ForeignKey(
        BookingStaff, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="requests",
    )
    friend = models.ForeignKey(
        "crm.Friend", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="booking_requests",
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="requested")
    customer_note = models.TextField(null=True, blank=True)
    internal_note = models.TextField(null=True, blank=True)
    price_at_booking = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booking_requests"
        ordering = ["starts_at"]
