import uuid

from django.db import models


class Form(models.Model):
    """
    LIFF 公開フォームの定義。
    fields は [{name, label, type}] の JSON 配列で回答項目を表す。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    fields = models.JSONField(default=list, blank=True)  # [{name, label, type}]
    line_account_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "forms"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class FormSubmission(models.Model):
    """フォームへの回答 (LIFF から送信)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="submissions")
    friend = models.ForeignKey(
        "crm.Friend",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="form_submissions",
    )
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "form_submissions"
        ordering = ["-created_at"]
