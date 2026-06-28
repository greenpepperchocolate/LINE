from rest_framework import serializers

from .models import (
    MessageTemplate,
    RichMenuArea,
    RichMenuGroup,
    RichMenuPage,
)

# フロント (apps/web/src/lib/api.ts) は camelCase を期待するため、
# snake_case のモデルフィールドを camelCase にマップする。


class RichMenuAreaSerializer(serializers.ModelSerializer):
    boundsX = serializers.IntegerField(source="bounds_x")
    boundsY = serializers.IntegerField(source="bounds_y")
    boundsWidth = serializers.IntegerField(source="bounds_width")
    boundsHeight = serializers.IntegerField(source="bounds_height")
    actionType = serializers.CharField(source="action_type")
    actionData = serializers.JSONField(source="action_data")

    class Meta:
        model = RichMenuArea
        fields = (
            "id", "boundsX", "boundsY", "boundsWidth", "boundsHeight",
            "actionType", "actionData",
        )


class RichMenuPageSerializer(serializers.ModelSerializer):
    orderIndex = serializers.IntegerField(source="order_index")
    aliasId = serializers.CharField(source="alias_id")
    lineRichmenuId = serializers.CharField(source="line_richmenu_id", allow_null=True)
    imageR2Key = serializers.CharField(source="image_r2_key", allow_null=True)
    imageContentType = serializers.CharField(source="image_content_type", allow_null=True)
    areas = RichMenuAreaSerializer(many=True, read_only=True)

    class Meta:
        model = RichMenuPage
        fields = (
            "id", "orderIndex", "name", "aliasId", "lineRichmenuId",
            "imageR2Key", "imageContentType", "areas",
        )


class RichMenuGroupListSerializer(serializers.ModelSerializer):
    accountId = serializers.PrimaryKeyRelatedField(source="account", read_only=True)
    chatBarText = serializers.CharField(source="chat_bar_text")
    defaultPageId = serializers.UUIDField(source="default_page_id", allow_null=True)
    isDefaultForAll = serializers.BooleanField(source="is_default_for_all")
    publishingAt = serializers.DateTimeField(source="publishing_at", allow_null=True)
    thumbnailR2Key = serializers.CharField(source="thumbnail_r2_key", allow_null=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = RichMenuGroup
        fields = (
            "id", "accountId", "name", "chatBarText", "size", "defaultPageId",
            "isDefaultForAll", "status", "publishingAt", "thumbnailR2Key",
            "createdAt", "updatedAt",
        )


class RichMenuGroupDetailSerializer(serializers.ModelSerializer):
    accountId = serializers.PrimaryKeyRelatedField(source="account", read_only=True)
    chatBarText = serializers.CharField(source="chat_bar_text")
    defaultPageId = serializers.UUIDField(source="default_page_id", allow_null=True)
    isDefaultForAll = serializers.BooleanField(source="is_default_for_all")
    publishingAt = serializers.DateTimeField(source="publishing_at", allow_null=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    pages = RichMenuPageSerializer(many=True, read_only=True)

    class Meta:
        model = RichMenuGroup
        fields = (
            "id", "accountId", "name", "chatBarText", "size", "defaultPageId",
            "isDefaultForAll", "status", "publishingAt", "createdAt", "updatedAt",
            "pages",
        )


class MessageTemplateSerializer(serializers.ModelSerializer):
    messageType = serializers.CharField(source="message_type")
    messageContent = serializers.CharField(source="message_content", allow_blank=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = MessageTemplate
        fields = (
            "id", "name", "messageType", "messageContent", "createdAt", "updatedAt",
        )
