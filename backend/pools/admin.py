from django.contrib import admin

from .models import PoolAccount, TrafficPool


class PoolAccountInline(admin.TabularInline):
    model = PoolAccount
    extra = 0


@admin.register(TrafficPool)
class TrafficPoolAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "active_account", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    inlines = [PoolAccountInline]


@admin.register(PoolAccount)
class PoolAccountAdmin(admin.ModelAdmin):
    list_display = ("pool", "line_account", "is_active", "created_at")
    list_filter = ("is_active",)
