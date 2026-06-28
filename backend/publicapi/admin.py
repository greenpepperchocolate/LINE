from django.contrib import admin

from .models import LinkClick


@admin.register(LinkClick)
class LinkClickAdmin(admin.ModelAdmin):
    list_display = ("ref_code", "ip_address", "created_at")
    list_filter = ("ref_code",)
    search_fields = ("ref_code", "ip_address", "user_agent")
    readonly_fields = ("id", "ref_code", "user_agent", "ip_address", "referer", "created_at")
    ordering = ("-created_at",)
