from django.contrib import admin

from .models import BookingMenu, BookingRequest, BookingStaff, Shift, StaffMenu


@admin.register(BookingMenu)
class BookingMenuAdmin(admin.ModelAdmin):
    list_display = ("name", "category_label", "duration_minutes", "base_price", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name",)


class StaffMenuInline(admin.TabularInline):
    model = StaffMenu
    extra = 0


@admin.register(BookingStaff)
class BookingStaffAdmin(admin.ModelAdmin):
    list_display = ("display_name", "name", "role", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "display_name")
    inlines = [StaffMenuInline]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("staff", "work_date", "start_time", "end_time")
    list_filter = ("work_date",)


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "menu", "staff", "friend", "starts_at", "status")
    list_filter = ("status",)
