import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view

from common.responses import err, ok
from crm.models import Friend, LineAccount

from .models import (
    MessageTemplate,
    RichMenuArea,
    RichMenuGroup,
    RichMenuPage,
    TestRecipient,
)
from .serializers import (
    MessageTemplateSerializer,
    RichMenuGroupDetailSerializer,
    RichMenuGroupListSerializer,
)

# 認証はグローバル設定 (IsAuthenticated) により全て JWT 必須。


# ----------------------------------------------------------------------------
# ヘルパー: 入力 (camelCase) から pages / areas を作成する
# ----------------------------------------------------------------------------
def _create_pages(group, pages_input):
    """pages_input: [{id?, name, orderIndex, areas:[{boundsX..., actionType, actionData}]}]"""
    for idx, page_data in enumerate(pages_input or []):
        page = RichMenuPage.objects.create(
            group=group,
            order_index=page_data.get("orderIndex", idx),
            name=page_data.get("name", ""),
            alias_id=page_data.get("aliasId", ""),
        )
        for area_data in page_data.get("areas", []) or []:
            RichMenuArea.objects.create(
                page=page,
                bounds_x=area_data.get("boundsX", 0),
                bounds_y=area_data.get("boundsY", 0),
                bounds_width=area_data.get("boundsWidth", 0),
                bounds_height=area_data.get("boundsHeight", 0),
                action_type=area_data.get("actionType", "uri"),
                action_data=area_data.get("actionData", {}) or {},
            )


# ----------------------------------------------------------------------------
# Rich menu groups
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def rich_menu_groups_list(request):
    if request.method == "GET":
        qs = RichMenuGroup.objects.all()
        account_id = request.query_params.get("accountId")
        if account_id:
            qs = qs.filter(account_id=account_id)
        return ok(RichMenuGroupListSerializer(qs, many=True).data)

    # POST: グループ + ページ + 領域を作成
    data = request.data
    account_id = data.get("accountId")
    if not account_id:
        return err("accountId は必須です", status=400)
    account = get_object_or_404(LineAccount, id=account_id)

    with transaction.atomic():
        group = RichMenuGroup.objects.create(
            account=account,
            name=data.get("name", ""),
            chat_bar_text=data.get("chatBarText", "メニュー"),
            size=data.get("size", "large"),
        )
        _create_pages(group, data.get("pages"))

    pages = [{"id": str(p.id)} for p in group.pages.all()]
    return ok({"id": str(group.id), "pages": pages}, status=201)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def rich_menu_group_detail(request, id):
    group = get_object_or_404(RichMenuGroup, id=id)

    if request.method == "GET":
        return ok(RichMenuGroupDetailSerializer(group).data)

    if request.method == "DELETE":
        # ?force=true は将来 LINE 上のメニューも削除する想定 (現状は DB のみ)。
        group.delete()
        return ok(None)

    # PUT / PATCH は部分更新として扱う
    data = request.data
    if "name" in data:
        group.name = data["name"]
    if "chatBarText" in data:
        group.chat_bar_text = data["chatBarText"]
    if "isDefaultForAll" in data:
        group.is_default_for_all = data["isDefaultForAll"]
    group.save()

    # pages が渡された場合は丸ごと差し替える
    if "pages" in data and data["pages"] is not None:
        with transaction.atomic():
            group.pages.all().delete()
            _create_pages(group, data["pages"])

    return ok({"id": str(group.id)})


@api_view(["POST"])
def rich_menu_group_publish(request, id):
    group = get_object_or_404(RichMenuGroup, id=id)
    pages = []
    # TODO: LINE API 連携 (rich menu 作成・画像アップロード・default 設定)
    for page in group.pages.all():
        new_id = f"richmenu-{uuid.uuid4().hex}"
        page.line_richmenu_id = new_id
        page.save(update_fields=["line_richmenu_id", "updated_at"])
        pages.append({"pageId": str(page.id), "newRichMenuId": new_id})
    group.status = "published"
    group.publishing_at = timezone.now()
    group.save(update_fields=["status", "publishing_at", "updated_at"])
    return ok({"pages": pages})


@api_view(["POST"])
def rich_menu_group_unpublish(request, id):
    group = get_object_or_404(RichMenuGroup, id=id)
    pages = []
    # TODO: LINE API 連携 (rich menu 削除・default 解除)
    for page in group.pages.all():
        cleared = page.line_richmenu_id
        page.line_richmenu_id = None
        page.save(update_fields=["line_richmenu_id", "updated_at"])
        pages.append({"pageId": str(page.id), "clearedRichMenuId": cleared})
    group.status = "draft"
    group.publishing_at = None
    group.save(update_fields=["status", "publishing_at", "updated_at"])
    return ok({"pages": pages, "warnings": []})


@api_view(["POST"])
def rich_menu_group_apply_to_tag(request, id):
    group = get_object_or_404(RichMenuGroup, id=id)
    mode = request.data.get("mode")
    # TODO: LINE API 連携 (タグ対象友だちへ linkRichMenu / set default)
    if mode == "set-default":
        group.is_default_for_all = True
        group.save(update_fields=["is_default_for_all", "updated_at"])
        return ok({"chunks": 0, "total": 0, "mode": mode})
    if mode == "bulk-link":
        return ok({"chunks": 0, "total": 0, "mode": mode})
    return err("mode は bulk-link / set-default のいずれかです", status=400)


# ----------------------------------------------------------------------------
# Rich menu groups: external (LINE 上の rich menu)
# ----------------------------------------------------------------------------
@api_view(["GET"])
def rich_menu_groups_external(request):
    # TODO: LINE API 連携 (GET /v2/bot/richmenu/list)
    return ok({"currentDefault": None, "lineMenus": []})


@api_view(["GET", "DELETE"])
def rich_menu_groups_external_detail(request, external_id):
    # TODO: LINE API 連携 (取得 / 削除)
    return ok(None)


@api_view(["POST"])
def rich_menu_groups_import(request):
    account_id = request.query_params.get("accountId")
    rich_menu_id = request.query_params.get("richMenuId")
    if not account_id or not rich_menu_id:
        return err("accountId と richMenuId は必須です", status=400)
    account = get_object_or_404(LineAccount, id=account_id)
    # TODO: LINE API 連携 (rich menu 取得 → ページ/領域として取り込み)
    name = f"取り込み {rich_menu_id}"
    group = RichMenuGroup.objects.create(account=account, name=name)
    return ok({"id": str(group.id), "name": group.name}, status=201)


# ----------------------------------------------------------------------------
# Message templates
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def message_templates_list(request):
    if request.method == "GET":
        qs = MessageTemplate.objects.all()
        return ok(MessageTemplateSerializer(qs, many=True).data)

    serializer = MessageTemplateSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    tpl = serializer.save()
    return ok(MessageTemplateSerializer(tpl).data, status=201)


# ----------------------------------------------------------------------------
# Account settings: test recipients
# ----------------------------------------------------------------------------
@api_view(["GET", "POST", "PUT"])
def test_recipients(request):
    if request.method == "GET":
        account_id = request.query_params.get("accountId")
        if not account_id:
            return err("accountId は必須です", status=400)
        qs = TestRecipient.objects.filter(account_id=account_id).select_related("friend")
        data = [
            {
                "id": str(tr.friend.id),
                "displayName": tr.friend.display_name,
                "pictureUrl": tr.friend.picture_url,
            }
            for tr in qs
        ]
        return ok(data)

    # POST / PUT: テスト配信先を丸ごと差し替える
    account_id = request.data.get("accountId")
    friend_ids = request.data.get("friendIds", [])
    if not account_id:
        return err("accountId は必須です", status=400)
    account = get_object_or_404(LineAccount, id=account_id)

    with transaction.atomic():
        TestRecipient.objects.filter(account=account).delete()
        for fid in friend_ids or []:
            friend = Friend.objects.filter(id=fid).first()
            if friend:
                TestRecipient.objects.create(account=account, friend=friend)
    return ok(None)


# ----------------------------------------------------------------------------
# リッチメニュー画像配信 (公開) — /api/rich-menu-images/<key>
# ----------------------------------------------------------------------------
import os  # noqa: E402

from django.conf import settings as dj_settings  # noqa: E402
from django.http import FileResponse, Http404  # noqa: E402
from rest_framework.decorators import permission_classes  # noqa: E402
from rest_framework.permissions import AllowAny  # noqa: E402


@api_view(["GET"])
@permission_classes([AllowAny])
def rich_menu_image(request, key):
    """media/ 配下に保存された画像を配信。img src から直接アクセスされる(認証不要)。"""
    base = os.path.normpath(os.path.join(dj_settings.BASE_DIR, "media"))
    path = os.path.normpath(os.path.join(base, key))
    if not path.startswith(base) or not os.path.isfile(path):
        raise Http404("image not found")
    return FileResponse(open(path, "rb"))


# ----------------------------------------------------------------------------
# リッチメニュー ページ画像アップロード / external 画像
# ----------------------------------------------------------------------------
import os  # noqa: E402

from django.conf import settings as dj_settings  # noqa: E402
from django.http import Http404  # noqa: E402
from rest_framework.decorators import permission_classes  # noqa: E402
from rest_framework.permissions import AllowAny  # noqa: E402

_EXT_BY_CT = {"image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg"}


@api_view(["POST"])
def rich_menu_page_image(request, id, page_id):
    """ページ画像をアップロード (Content-Type: image/* の生バイナリ)。"""
    page = get_object_or_404(RichMenuPage, id=page_id, group_id=id)
    data = request.body
    if not data:
        return err("画像データがありません", status=400)
    ct = request.headers.get("Content-Type", "image/png").split(";")[0].strip()
    ext = _EXT_BY_CT.get(ct, "png")
    key = f"richmenu/{page_id}.{ext}"
    path = os.path.join(dj_settings.BASE_DIR, "media", key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)
    page.image_r2_key = key
    page.image_content_type = ct
    page.save(update_fields=["image_r2_key", "image_content_type", "updated_at"])
    return ok({"imageR2Key": key, "imageUrl": f"/api/rich-menu-images/{key}"})


@api_view(["GET"])
@permission_classes([AllowAny])
def rich_menu_external_image(request, id):
    """external (LINE 上の既存メニュー) 画像。MVP では未保持のため 404。"""
    raise Http404("external rich menu image not available")
