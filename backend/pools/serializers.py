from rest_framework import serializers

from crm.models import LineAccount

from .models import PoolAccount, TrafficPool

# フロント (@line-crm/shared の型) は camelCase を期待するため、
# snake_case のモデルフィールドを camelCase にマップする (crm/serializers.py と同方針)。


class TrafficPoolSerializer(serializers.ModelSerializer):
    activeAccountId = serializers.PrimaryKeyRelatedField(
        source="active_account",
        queryset=LineAccount.objects.all(),
        required=False,
        allow_null=True,
    )
    accountName = serializers.SerializerMethodField()
    liffId = serializers.SerializerMethodField()
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = TrafficPool
        fields = (
            "id", "slug", "name", "activeAccountId", "accountName", "liffId",
            "isActive", "createdAt", "updatedAt",
        )

    def get_accountName(self, obj):
        return obj.active_account.name if obj.active_account else None

    def get_liffId(self, obj):
        return obj.active_account.liff_id if obj.active_account else None


class PoolAccountSerializer(serializers.ModelSerializer):
    poolId = serializers.PrimaryKeyRelatedField(source="pool", read_only=True)
    lineAccountId = serializers.PrimaryKeyRelatedField(
        source="line_account", queryset=LineAccount.objects.all()
    )
    accountName = serializers.SerializerMethodField()
    liffId = serializers.SerializerMethodField()
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = PoolAccount
        fields = (
            "id", "poolId", "lineAccountId", "accountName", "liffId",
            "isActive", "createdAt",
        )

    def get_accountName(self, obj):
        return obj.line_account.name if obj.line_account else None

    def get_liffId(self, obj):
        return obj.line_account.liff_id if obj.line_account else None
