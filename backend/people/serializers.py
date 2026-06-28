from rest_framework import serializers

from .models import AccountHealthLog, AccountMigration, StaffMember, User

# フロント (@line-crm/shared の型) は camelCase を期待するため、
# snake_case のモデルフィールドを camelCase にマップする。


class UserSerializer(serializers.ModelSerializer):
    externalId = serializers.CharField(source="external_id", required=False, allow_null=True, allow_blank=True)
    displayName = serializers.CharField(source="display_name", required=False, allow_null=True, allow_blank=True)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "phone", "externalId", "displayName", "createdAt", "updatedAt")


class StaffMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    apiKey = serializers.CharField(source="api_key", read_only=True)
    isActive = serializers.BooleanField(source="is_active", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = StaffMember
        fields = ("id", "name", "email", "role", "apiKey", "isActive", "createdAt", "updatedAt")


class AccountHealthLogSerializer(serializers.ModelSerializer):
    lineAccountId = serializers.CharField(source="line_account_id", read_only=True)
    errorCode = serializers.IntegerField(source="error_code", read_only=True, allow_null=True)
    errorCount = serializers.IntegerField(source="error_count", read_only=True)
    checkPeriod = serializers.CharField(source="check_period", read_only=True)
    riskLevel = serializers.CharField(source="risk_level", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = AccountHealthLog
        fields = ("id", "lineAccountId", "errorCode", "errorCount", "checkPeriod", "riskLevel", "createdAt")


class AccountMigrationSerializer(serializers.ModelSerializer):
    fromAccountId = serializers.CharField(source="from_account_id", read_only=True)
    toAccountId = serializers.CharField(source="to_account_id", read_only=True)
    migratedCount = serializers.IntegerField(source="migrated_count", read_only=True)
    totalCount = serializers.IntegerField(source="total_count", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    completedAt = serializers.DateTimeField(source="completed_at", read_only=True, allow_null=True)

    class Meta:
        model = AccountMigration
        fields = (
            "id", "fromAccountId", "toAccountId", "status",
            "migratedCount", "totalCount", "createdAt", "completedAt",
        )
