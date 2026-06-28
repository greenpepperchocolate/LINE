from django.contrib import admin

from .models import (
    AutoReply,
    Broadcast,
    Chat,
    Friend,
    FriendTag,
    LineAccount,
    LineSettings,
    Message,
    Scenario,
    ScenarioStep,
    Tag,
    Template,
)


@admin.register(LineSettings)
class LineSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "updated_at")


@admin.register(LineAccount)
class LineAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "channel_id", "is_active", "display_order", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "channel_id")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "created_at")
    search_fields = ("name",)


class FriendTagInline(admin.TabularInline):
    model = FriendTag
    extra = 0


@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ("display_name", "line_user_id", "is_following", "created_at")
    search_fields = ("display_name", "line_user_id")
    inlines = [FriendTagInline]


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ("title", "message_type", "target_type", "status", "created_at")
    list_filter = ("status", "target_type", "message_type")


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "message_type", "created_at")
    search_fields = ("name",)


@admin.register(AutoReply)
class AutoReplyAdmin(admin.ModelAdmin):
    list_display = ("keyword", "match_type", "is_active", "created_at")
    list_filter = ("match_type", "is_active")


class ScenarioStepInline(admin.TabularInline):
    model = ScenarioStep
    extra = 0


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ("name", "trigger_type", "is_active", "delivery_mode", "created_at")
    list_filter = ("trigger_type", "is_active")
    inlines = [ScenarioStepInline]


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("friend", "status", "last_message_at")
    list_filter = ("status",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("friend", "direction", "message_type", "created_at")
    list_filter = ("direction",)
