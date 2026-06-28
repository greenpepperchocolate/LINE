from django.contrib import admin

from .models import AccountHealthLog, AccountMigration, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("display_name", "email", "phone", "external_id", "created_at")
    search_fields = ("display_name", "email", "phone", "external_id")


@admin.register(AccountHealthLog)
class AccountHealthLogAdmin(admin.ModelAdmin):
    list_display = ("line_account_id", "risk_level", "error_code", "error_count", "created_at")
    list_filter = ("risk_level",)
    search_fields = ("line_account_id",)


@admin.register(AccountMigration)
class AccountMigrationAdmin(admin.ModelAdmin):
    list_display = ("from_account_id", "to_account_id", "status", "migrated_count", "total_count", "created_at")
    list_filter = ("status",)
