from django.contrib import admin

from .models import (
    Affiliate,
    AffiliateClick,
    Automation,
    AutomationLog,
    ConversionEvent,
    ConversionPoint,
    EntryRoute,
    ScoringRule,
)


@admin.register(ConversionPoint)
class ConversionPointAdmin(admin.ModelAdmin):
    list_display = ("name", "event_type", "value", "created_at")
    search_fields = ("name", "event_type")


@admin.register(ConversionEvent)
class ConversionEventAdmin(admin.ModelAdmin):
    list_display = ("conversion_point", "friend", "affiliate_code", "created_at")
    list_filter = ("conversion_point",)


@admin.register(Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "commission_rate", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(AffiliateClick)
class AffiliateClickAdmin(admin.ModelAdmin):
    list_display = ("affiliate", "ip_address", "created_at")


@admin.register(ScoringRule)
class ScoringRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "event_type", "score_value", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(EntryRoute)
class EntryRouteAdmin(admin.ModelAdmin):
    list_display = ("name", "ref_code", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "ref_code")


class AutomationLogInline(admin.TabularInline):
    model = AutomationLog
    extra = 0


@admin.register(Automation)
class AutomationAdmin(admin.ModelAdmin):
    list_display = ("name", "event_type", "is_active", "priority", "created_at")
    list_filter = ("event_type", "is_active")
    search_fields = ("name",)
    inlines = [AutomationLogInline]


@admin.register(AutomationLog)
class AutomationLogAdmin(admin.ModelAdmin):
    list_display = ("automation", "friend", "status", "created_at")
    list_filter = ("status",)
