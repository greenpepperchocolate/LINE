"""
画像ストレージ抽象化レイヤー。

env (R2_BUCKET / R2_ENDPOINT / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY) が
すべて設定されていれば Cloudflare R2 (S3 互換 API) を使用し、未設定なら
backend/media/ にローカル保存する。これにより「env を入れれば R2、
入れなければローカル」で透過的に動作する。
"""
import mimetypes
import os

from django.conf import settings


def is_r2_enabled():
    return bool(
        settings.R2_BUCKET
        and settings.R2_ENDPOINT
        and settings.R2_ACCESS_KEY_ID
        and settings.R2_SECRET_ACCESS_KEY
    )


def _media_root():
    return os.path.normpath(os.path.join(str(settings.BASE_DIR), "media"))


def _client():
    import boto3  # 遅延 import (R2 未使用環境では boto3 不要)

    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def save_image(key, data, content_type):
    """画像を保存。R2 or ローカル。key は 'uploads/xxx.png' 等のスラッシュ区切り。"""
    if is_r2_enabled():
        _client().put_object(
            Bucket=settings.R2_BUCKET, Key=key, Body=data, ContentType=content_type
        )
    else:
        dest = os.path.join(_media_root(), *key.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
    return key


def load_image(key):
    """画像を取得。戻り値 (bytes, content_type) または None。"""
    if is_r2_enabled():
        try:
            obj = _client().get_object(Bucket=settings.R2_BUCKET, Key=key)
            return obj["Body"].read(), obj.get("ContentType", "application/octet-stream")
        except Exception:
            return None
    path = os.path.normpath(os.path.join(_media_root(), key))
    if not path.startswith(_media_root()) or not os.path.isfile(path):
        return None
    ct = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        return f.read(), ct


def delete_image(key):
    if is_r2_enabled():
        try:
            _client().delete_object(Bucket=settings.R2_BUCKET, Key=key)
        except Exception:
            pass
        return
    path = os.path.normpath(os.path.join(_media_root(), key))
    if path.startswith(_media_root()) and os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass


def public_url(key, request=None):
    """
    画像の公開 URL。
    - R2 公開URLが設定されていればそれを直接返す（CDN/独自ドメイン配信）。
    - それ以外は Django 配信エンドポイント /api/rich-menu-images/<key> を返す。
    """
    if settings.R2_PUBLIC_BASE_URL:
        return settings.R2_PUBLIC_BASE_URL.rstrip("/") + "/" + key
    path = f"/api/rich-menu-images/{key}"
    return request.build_absolute_uri(path) if request is not None else path
