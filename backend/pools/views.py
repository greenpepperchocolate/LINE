import mimetypes
import os
import uuid as uuid_lib

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import BaseParser, FormParser, MultiPartParser

from common.responses import err, ok

from .models import PoolAccount, TrafficPool
from .serializers import PoolAccountSerializer, TrafficPoolSerializer

# 認証はグローバル設定 (IsAuthenticated) により全て JWT 必須。


# ----------------------------------------------------------------------------
# Traffic pools
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def traffic_pools_list(request):
    if request.method == "GET":
        qs = TrafficPool.objects.all().select_related("active_account")
        return ok(TrafficPoolSerializer(qs, many=True).data)

    serializer = TrafficPoolSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    pool = serializer.save()
    return ok(TrafficPoolSerializer(pool).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def traffic_pool_detail(request, id):
    pool = get_object_or_404(
        TrafficPool.objects.select_related("active_account"), id=id
    )

    if request.method == "GET":
        return ok(TrafficPoolSerializer(pool).data)

    if request.method == "DELETE":
        pool.delete()
        return ok(None)

    # PUT (partial update — name / activeAccountId / isActive)
    serializer = TrafficPoolSerializer(pool, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(TrafficPoolSerializer(pool).data)


# ----------------------------------------------------------------------------
# Pool accounts
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def pool_accounts_list(request, id):
    pool = get_object_or_404(TrafficPool, id=id)

    if request.method == "GET":
        qs = pool.accounts.all().select_related("line_account")
        return ok(PoolAccountSerializer(qs, many=True).data)

    serializer = PoolAccountSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    account = serializer.save(pool=pool)
    return ok(PoolAccountSerializer(account).data, status=201)


@api_view(["PUT", "DELETE"])
def pool_account_detail(request, id, account_id):
    account = get_object_or_404(
        PoolAccount.objects.select_related("line_account"),
        id=account_id,
        pool_id=id,
    )

    if request.method == "DELETE":
        account.delete()
        return ok(None)

    # PUT (toggle isActive 等)
    serializer = PoolAccountSerializer(account, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(PoolAccountSerializer(account).data)


# ----------------------------------------------------------------------------
# Image upload (POST /api/images)
# ----------------------------------------------------------------------------
class RawImageParser(BaseParser):
    """
    フロント (apps/web の api.uploads.image) は multipart ではなく
    画像バイナリを生のまま body に載せ、Content-Type に image/* を指定して送る。
    DRF のデフォルトパーサでは image/* を扱えず 415 になるため、生バイト列を
    そのまま返すパーサを追加する。
    """

    media_type = "image/*"

    def parse(self, stream, media_type=None, parser_context=None):
        return stream.read()


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser, RawImageParser])
def upload_image(request):
    # 1) multipart の場合 (file / image フィールド)
    upload = request.FILES.get("file") or request.FILES.get("image")
    if upload is not None:
        content = upload.read()
        content_type = upload.content_type or "application/octet-stream"
        orig_name = upload.name or ""
    # 2) 生バイナリの場合 (RawImageParser が bytes を返す)
    elif isinstance(request.data, (bytes, bytearray)) and request.data:
        content = bytes(request.data)
        content_type = request.content_type or "application/octet-stream"
        orig_name = ""
    else:
        return err("画像データがありません", status=400)

    if not content:
        return err("画像データがありません", status=400)
    if len(content) > 10 * 1024 * 1024:
        return err("ファイルサイズが大きすぎます (最大10MB)", status=400)
    if not str(content_type).startswith("image/"):
        return err("画像ファイルのみアップロードできます", status=400)

    ext = (
        mimetypes.guess_extension(content_type.split(";")[0].strip())
        or os.path.splitext(orig_name)[1]
        or ".bin"
    )
    file_id = str(uuid_lib.uuid4())
    key = f"uploads/{file_id}{ext}"

    # R2 (env 設定時) or ローカル(media/) に保存。
    from common.storage import public_url, save_image
    save_image(key, content, content_type)
    url = public_url(key, request)
    return ok(
        {
            "id": file_id,
            "key": key,
            "url": url,
            "mimeType": content_type,
            "size": len(content),
        },
        status=201,
    )
