from django.contrib import admin

from .models import Event, EventBooking, EventSlot


class EventSlotInline(admin.TabularInline):
    model = EventSlot
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "venue_name", "is_published", "sort_order", "created_at")
    list_filter = ("is_published", "requires_approval", "target_type")
    search_fields = ("name", "venue_name")
    inlines = [EventSlotInline]


@admin.register(EventSlot)
class EventSlotAdmin(admin.ModelAdmin):
    list_display = ("event", "starts_at", "ends_at", "capacity", "is_active", "sort_order")
    list_filter = ("is_active",)


@admin.register(EventBooking)
class EventBookingAdmin(admin.ModelAdmin):
    list_display = ("event", "friend", "slot", "status", "requested_at")
    list_filter = ("status",)
    search_fields = ("friend__display_name", "friend__line_user_id")
