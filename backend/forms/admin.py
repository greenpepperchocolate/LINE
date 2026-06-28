from django.contrib import admin

from .models import Form, FormSubmission


class FormSubmissionInline(admin.TabularInline):
    model = FormSubmission
    extra = 0
    readonly_fields = ("friend", "data", "created_at")


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ("name", "line_account_id", "created_at", "updated_at")
    search_fields = ("name",)
    inlines = [FormSubmissionInline]


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ("form", "friend", "created_at")
    list_filter = ("form",)
