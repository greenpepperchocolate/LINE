import uuid

from django.db import models

# crm の LineAccount を参照する (マルチアカウント分散先の振り分け)。
from crm.models import LineAccount

# D1 スキーマの traffic_pools / pool_accounts に対応する Django モデル。
# ID は UUID (D1 の TEXT UUID 相当)。
# フロント型: packages/shared/src/types.ts の TrafficPool / PoolAccount。


class TrafficPool(models.Model):
    """
    トラフィックプール — 1 つの slug (入口) に対して複数の LINE アカウントを
    束ね、現在アクティブな振り分け先 (active_account) を切り替える単位。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    active_account = models.ForeignKey(
        LineAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_pools",
        db_column="active_account_id",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "traffic_pools"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class PoolAccount(models.Model):
    """
    プールに所属する LINE アカウント 1 件 (中間テーブル)。
    is_active で個別に振り分け対象 ON/OFF を切り替えられる。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pool = models.ForeignKey(
        TrafficPool, on_delete=models.CASCADE, related_name="accounts"
    )
    line_account = models.ForeignKey(
        LineAccount,
        on_delete=models.CASCADE,
        related_name="pool_memberships",
        db_column="line_account_id",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pool_accounts"
        ordering = ["created_at"]
        unique_together = ("pool", "line_account")

    def __str__(self):
        return f"{self.pool_id}:{self.line_account_id}"
