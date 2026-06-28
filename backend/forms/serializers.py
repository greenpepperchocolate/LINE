from rest_framework import serializers

from .models import Form, FormSubmission

# フロント (form-submissions 画面) は camelCase を期待するため、
# snake_case のモデルフィールドを camelCase にマップする。


class FormSerializer(serializers.ModelSerializer):
    """
    一覧用 Form。submitCount / lastSubmittedAt / usedByAccounts を付与する。
    submitCount・lastSubmittedAt は views 側で annotate した値を参照する。
    """

    description = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    submitCount = serializers.SerializerMethodField()
    lastSubmittedAt = serializers.SerializerMethodField()
    usedByAccounts = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = (
            "id", "name", "description",
            "submitCount", "lastSubmittedAt", "usedByAccounts",
        )

    def get_submitCount(self, obj):
        count = getattr(obj, "submit_count", None)
        return count if count is not None else obj.submissions.count()

    def get_lastSubmittedAt(self, obj):
        last = getattr(obj, "last_submitted_at", "__missing__")
        if last == "__missing__":
            last_obj = obj.submissions.order_by("-created_at").first()
            last = last_obj.created_at if last_obj else None
        if last is None:
            return None
        return serializers.DateTimeField().to_representation(last)

    def get_usedByAccounts(self, obj):
        # マルチアカウント別の集計は MVP では未対応 (空配列)。
        return []


class FormDetailSerializer(FormSerializer):
    """詳細用 Form。回答項目 (fields) を含む。"""

    class Meta(FormSerializer.Meta):
        fields = FormSerializer.Meta.fields + ("fields",)


class FormWriteSerializer(serializers.ModelSerializer):
    """フォーム作成・更新用。"""

    description = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    fields = serializers.JSONField(required=False)
    lineAccountId = serializers.CharField(
        source="line_account_id", required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = Form
        fields = ("id", "name", "description", "fields", "lineAccountId")


class SubmissionSerializer(serializers.ModelSerializer):
    """回答の表示用。"""

    formId = serializers.PrimaryKeyRelatedField(source="form", read_only=True)
    friendId = serializers.PrimaryKeyRelatedField(source="friend", read_only=True, allow_null=True)
    friendName = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = FormSubmission
        fields = ("id", "formId", "friendId", "friendName", "data", "createdAt")

    def get_friendName(self, obj):
        return obj.friend.display_name if obj.friend else None
