from django.contrib import admin

from .models import (
    IncomingWebhook,
    Notification,
    NotificationRule,
    OutgoingWebhook,
    Reminder,
    ReminderStep,
)


class ReminderStepInline(admin.TabularInline):
    model = ReminderStep
    extra = 0


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    inlines = [ReminderStepInline]


@admin.register(ReminderStep)
class ReminderStepAdmin(admin.ModelAdmin):
    list_display = ("reminder", "offset_minutes", "message_type", "created_at")
    list_filter = ("message_type",)


@admin.register(IncomingWebhook)
class IncomingWebhookAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "is_active", "created_at")
    list_filter = ("source_type", "is_active")
    search_fields = ("name",)


@admin.register(OutgoingWebhook)
class OutgoingWebhookAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "url")


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "event_type", "is_active", "created_at")
    list_filter = ("event_type", "is_active")
    search_fields = ("name", "event_type")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "event_type", "channel", "status", "created_at")
    list_filter = ("status", "channel", "event_type")
    search_fields = ("title", "body")
