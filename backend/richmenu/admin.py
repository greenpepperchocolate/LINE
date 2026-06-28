from django.contrib import admin

from .models import (
    MessageTemplate,
    RichMenuArea,
    RichMenuGroup,
    RichMenuPage,
    TestRecipient,
)


class RichMenuAreaInline(admin.TabularInline):
    model = RichMenuArea
    extra = 0


@admin.register(RichMenuPage)
class RichMenuPageAdmin(admin.ModelAdmin):
    list_display = ("group", "order_index", "name", "line_richmenu_id", "created_at")
    inlines = [RichMenuAreaInline]


class RichMenuPageInline(admin.TabularInline):
    model = RichMenuPage
    extra = 0


@admin.register(RichMenuGroup)
class RichMenuGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "account", "size", "status", "is_default_for_all", "created_at")
    list_filter = ("status", "size", "is_default_for_all")
    search_fields = ("name",)
    inlines = [RichMenuPageInline]


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "message_type", "created_at")
    search_fields = ("name",)


@admin.register(TestRecipient)
class TestRecipientAdmin(admin.ModelAdmin):
    list_display = ("account", "friend", "created_at")
