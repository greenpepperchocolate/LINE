import secrets
import uuid

from django.db import models


def generate_api_key():
    """旧 StaffMember 用 (削除済み)。過去マイグレーション 0001 が参照するため残置。"""
    return secrets.token_urlsafe(32)

# 管理画面の「ユーザー / スタッフ管理 / アカウントヘルス・移行」用モデル。
# ID は他アプリ (crm / accounts) と同様 UUID。
# crm.Friend.user_id は CharField なので、User.id (UUID) を文字列で紐づける。


class User(models.Model):
    """
    cross-account の内部ユーザー。
    crm.Friend を user_id (= この User.id の文字列) でまとめる概念。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    external_id = models.CharField(max_length=255, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.display_name or self.email or str(self.id)


class AccountHealthLog(models.Model):
    """LINE アカウントの健全性チェックログ。"""

    RISK_CHOICES = (
        ("normal", "normal"),
        ("warning", "warning"),
        ("danger", "danger"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line_account_id = models.CharField(max_length=64)
    error_code = models.IntegerField(null=True, blank=True)
    error_count = models.IntegerField(default=0)
    check_period = models.CharField(max_length=50, default="")
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, default="normal")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "account_health_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.line_account_id} ({self.risk_level})"


class AccountMigration(models.Model):
    """アカウント間の友だち移行ジョブ。"""

    STATUS_CHOICES = (
        ("pending", "pending"),
        ("in_progress", "in_progress"),
        ("completed", "completed"),
        ("failed", "failed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_account_id = models.CharField(max_length=64)
    to_account_id = models.CharField(max_length=64)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    migrated_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "account_migrations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.from_account_id} -> {self.to_account_id}"
