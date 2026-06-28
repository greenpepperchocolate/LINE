from rest_framework import serializers

from .models import (
    Affiliate,
    Automation,
    AutomationLog,
    ConversionEvent,
    ConversionPoint,
    EntryRoute,
    ScoringRule,
)

# フロント (@line-crm/shared の型) は camelCase を期待するため、
# 各シリアライザで snake_case のモデルフィールドを camelCase にマップする。
# (既存 crm/serializers.py と同じ規約)


# ----------------------------------------------------------------------------
# Conversions
# ----------------------------------------------------------------------------
class ConversionPointSerializer(serializers.ModelSerializer):
    eventType = serializers.CharField(source="event_type")
    value = serializers.FloatField(required=False, allow_null=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = ConversionPoint
        fields = ("id", "name", "eventType", "value", "createdAt")


class ConversionEventSerializer(serializers.ModelSerializer):
    conversionPointId = serializers.PrimaryKeyRelatedField(
        source="conversion_point", read_only=True
    )
    friendId = serializers.PrimaryKeyRelatedField(source="friend", read_only=True)
    userId = serializers.CharField(source="user_id", read_only=True, allow_null=True)
    affiliateCode = serializers.CharField(
        source="affiliate_code", read_only=True, allow_null=True
    )
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = ConversionEvent
        fields = (
            "id", "conversionPointId", "friendId", "userId",
            "affiliateCode", "metadata", "createdAt",
        )


# ----------------------------------------------------------------------------
# Affiliates
# ----------------------------------------------------------------------------
class AffiliateSerializer(serializers.ModelSerializer):
    commissionRate = serializers.FloatField(source="commission_rate", required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Affiliate
        fields = ("id", "name", "code", "commissionRate", "isActive", "createdAt")


# ----------------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------------
class ScoringRuleSerializer(serializers.ModelSerializer):
    eventType = serializers.CharField(source="event_type")
    scoreValue = serializers.IntegerField(source="score_value")
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = ScoringRule
        fields = (
            "id", "name", "eventType", "scoreValue", "isActive",
            "createdAt", "updatedAt",
        )


# ----------------------------------------------------------------------------
# Entry routes
# ----------------------------------------------------------------------------
class EntryRouteSerializer(serializers.ModelSerializer):
    refCode = serializers.CharField(source="ref_code")
    tagId = serializers.UUIDField(source="tag_id", required=False, allow_null=True)
    scenarioId = serializers.UUIDField(source="scenario_id", required=False, allow_null=True)
    redirectUrl = serializers.CharField(
        source="redirect_url", required=False, allow_null=True, allow_blank=True
    )
    poolId = serializers.UUIDField(source="pool_id", required=False, allow_null=True)
    introTemplateId = serializers.UUIDField(
        source="intro_template_id", required=False, allow_null=True
    )
    runAccountFriendAddScenarios = serializers.BooleanField(
        source="run_account_friend_add_scenarios", required=False
    )
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = EntryRoute
        fields = (
            "id", "refCode", "name", "tagId", "scenarioId", "redirectUrl",
            "poolId", "introTemplateId", "runAccountFriendAddScenarios",
            "isActive", "createdAt", "updatedAt",
        )


# ----------------------------------------------------------------------------
# Automations
# ----------------------------------------------------------------------------
class AutomationLogSerializer(serializers.ModelSerializer):
    automationId = serializers.PrimaryKeyRelatedField(
        source="automation", read_only=True
    )
    friendId = serializers.PrimaryKeyRelatedField(
        source="friend", read_only=True, allow_null=True
    )
    eventData = serializers.CharField(source="event_data", read_only=True, allow_null=True)
    actionsResult = serializers.CharField(
        source="actions_result", read_only=True, allow_null=True
    )
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = AutomationLog
        fields = (
            "id", "automationId", "friendId", "eventData",
            "actionsResult", "status", "createdAt",
        )


class AutomationSerializer(serializers.ModelSerializer):
    eventType = serializers.CharField(source="event_type")
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Automation
        fields = (
            "id", "name", "description", "eventType", "conditions",
            "actions", "isActive", "priority", "createdAt", "updatedAt",
        )


class AutomationDetailSerializer(AutomationSerializer):
    logs = AutomationLogSerializer(many=True, read_only=True)

    class Meta(AutomationSerializer.Meta):
        fields = AutomationSerializer.Meta.fields + ("logs",)
