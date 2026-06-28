import uuid

from django.db import models

from crm.models import Friend

# packages/db/schema.sql の以下のテーブルに対応する Django モデル。
#   conversion_points / conversion_events / affiliates / affiliate_clicks
#   scoring_rules / entry_routes / automations / automation_logs
# ID は UUID (D1 の TEXT UUID 相当)。crm モデルと同じ規約に従う。


# ----------------------------------------------------------------------------
# Conversions (CV 計測)
# ----------------------------------------------------------------------------
class ConversionPoint(models.Model):
    """コンバージョンポイント (CV 定義)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100)
    value = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "conversion_points"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ConversionEvent(models.Model):
    """コンバージョンイベント (CV 記録)。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversion_point = models.ForeignKey(
        ConversionPoint, on_delete=models.CASCADE, related_name="events"
    )
    friend = models.ForeignKey(
        Friend, on_delete=models.CASCADE, related_name="conversion_events",
        null=True, blank=True,
    )
    user_id = models.CharField(max_length=64, null=True, blank=True)
    affiliate_code = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "conversion_events"
        ordering = ["-created_at"]


# ----------------------------------------------------------------------------
# Affiliates (アフィリエイト)
# ----------------------------------------------------------------------------
class Affiliate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    commission_rate = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "affiliates"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class AffiliateClick(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    affiliate = models.ForeignKey(
        Affiliate, on_delete=models.CASCADE, related_name="clicks"
    )
    url = models.TextField(null=True, blank=True)
    ip_address = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "affiliate_clicks"
        ordering = ["-created_at"]


# ----------------------------------------------------------------------------
# Scoring (リードスコアリング)
# ----------------------------------------------------------------------------
class ScoringRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100)
    score_value = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scoring_rules"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------------
# Entry routes (流入経路 / リファラルリンク)
# ----------------------------------------------------------------------------
class EntryRoute(models.Model):
    """流入経路。tag_id / scenario_id / pool_id / intro_template_id は
    他アプリ・他テーブル (一部は Django 非モデル) への参照のため UUID 値で保持する。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ref_code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    tag_id = models.UUIDField(null=True, blank=True)
    scenario_id = models.UUIDField(null=True, blank=True)
    redirect_url = models.TextField(null=True, blank=True)
    pool_id = models.UUIDField(null=True, blank=True)
    intro_template_id = models.UUIDField(null=True, blank=True)
    run_account_friend_add_scenarios = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entry_routes"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------------
# Automations (オートメーション)
# ----------------------------------------------------------------------------
class Automation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    event_type = models.CharField(max_length=100)
    conditions = models.JSONField(default=dict, blank=True)
    actions = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "automations"
        ordering = ["-priority", "-created_at"]

    def __str__(self):
        return self.name


class AutomationLog(models.Model):
    STATUS_CHOICES = (
        ("success", "success"),
        ("partial", "partial"),
        ("failed", "failed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(
        Automation, on_delete=models.CASCADE, related_name="logs"
    )
    friend = models.ForeignKey(
        Friend, on_delete=models.SET_NULL, related_name="automation_logs",
        null=True, blank=True,
    )
    event_data = models.TextField(null=True, blank=True)
    actions_result = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="success")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "automation_logs"
        ordering = ["-created_at"]
