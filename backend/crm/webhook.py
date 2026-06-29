"""
LINE Webhook 取り込みエンドポイント。

Cloudflare Workers の中継 (apps/webhook-relay) から、LINE イベントが
転送されてくる。Worker とは共有シークレット (X-Relay-Secret) で認証する。

署名検証はこの Django 側で行う。検証には「LINEアカウント管理」画面で登録した
各アカウントの channel secret を使い (マルチアカウント対応)、マッチした
アカウントの access token で返信・送信を行う。アカウント未登録時は
LINE設定 (LineSettings) / 環境変数の値にフォールバックする。

処理するイベント:
  - follow   : 友だち登録/復活 + friend_add シナリオ購読
  - unfollow : ブロック (is_following=False)
  - message  : 受信ログ + チャット更新 + キーワード自動応答
"""
import base64
import hashlib
import hmac
import json
import mimetypes

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common import storage

from . import line_client
from .config import get_line_access_token, get_line_channel_secret, get_relay_secret
from .models import AutoReply, Chat, Friend, FriendScenario, LineAccount, Message, Scenario


def _ensure_friend(line_user_id, access_token=None):
    """友だちを取得、無ければプロフィールを引いて作成。"""
    friend = Friend.objects.filter(line_user_id=line_user_id).first()
    if friend:
        return friend
    profile = line_client.get_profile(line_user_id, access_token) or {}
    return Friend.objects.create(
        line_user_id=line_user_id,
        display_name=profile.get("displayName", "") or "",
        picture_url=profile.get("pictureUrl"),
        status_message=profile.get("statusMessage"),
        is_following=True,
    )


def _handle_follow(event, access_token=None, request=None):
    user_id = event.get("source", {}).get("userId")
    if not user_id:
        return
    friend = _ensure_friend(user_id, access_token)
    if not friend.is_following:
        friend.is_following = True
        friend.save(update_fields=["is_following", "updated_at"])

    # friend_add シナリオに購読登録。delay 0 の先頭ステップは即時プッシュ。
    for scenario in Scenario.objects.filter(trigger_type="friend_add", is_active=True):
        enrollment, created = FriendScenario.objects.get_or_create(
            friend=friend, scenario=scenario,
            defaults={"status": "active", "current_step_order": 0},
        )
        if not created:
            continue
        first_step = scenario.steps.order_by("step_order").first()
        if first_step and first_step.delay_minutes == 0:
            ok_sent, _ = line_client.push_text(user_id, first_step.message_content, access_token)
            if ok_sent:
                Message.objects.create(
                    friend=friend, direction="outgoing",
                    message_type=first_step.message_type,
                    content=first_step.message_content, delivery_type="push",
                )
                enrollment.current_step_order = first_step.step_order
                enrollment.save(update_fields=["current_step_order", "updated_at"])


def _handle_unfollow(event, access_token=None, request=None):
    user_id = event.get("source", {}).get("userId")
    if not user_id:
        return
    Friend.objects.filter(line_user_id=user_id).update(
        is_following=False, updated_at=timezone.now()
    )


def _matches(auto_reply, text):
    if auto_reply.match_type == "exact":
        return text.strip() == auto_reply.keyword.strip()
    return auto_reply.keyword in text


_MEDIA_LABELS = {
    "image": "[画像]", "video": "[動画]", "audio": "[音声]",
    "file": "[ファイル]", "location": "[位置情報]",
}


_DEFAULT_STICKER_URL = "https://stickershop.line-scdn.net/stickershop/v1/sticker/{sid}/iPhone/sticker@2x.png"


def _ext_for(content_type):
    ext = mimetypes.guess_extension((content_type or "").split(";")[0].strip() or "")
    return (ext or ".bin").lstrip(".")


def _save_media(data, content_type, key, request):
    """R2 (env あり) or ローカル (media/) に保存し、配信用 URL を返す。"""
    storage.save_image(key, data, content_type or "application/octet-stream")
    return storage.public_url(key, request)


def _sticker_content(message):
    """
    スタンプをフロント (parseStickerMessageContent) が解釈できる JSON にする。
    スタンプ画像は公開・恒久的な LINE CDN にあるため保存せず、CDN URL を直接参照する。
    """
    sid = str(message.get("stickerId") or "")
    pid = message.get("packageId")
    return json.dumps({
        "type": "sticker",
        "packageId": str(pid) if pid else None,
        "stickerId": sid,
        "stickerResourceType": message.get("stickerResourceType"),
        "stickerUrl": _DEFAULT_STICKER_URL.format(sid=sid),
        "fallback": "[スタンプ]",
    }, ensure_ascii=False)


def _handle_message(event, access_token=None, request=None):
    user_id = event.get("source", {}).get("userId")
    message = event.get("message", {})
    mtype = message.get("type")
    if not user_id or not mtype:
        return
    friend = _ensure_friend(user_id, access_token)
    now = timezone.now()

    text = ""
    if mtype == "text":
        # テキスト (Unicode 絵文字はそのまま content に含まれる)
        text = message.get("text", "")
        Message.objects.create(
            friend=friend, direction="incoming", message_type="text", content=text,
        )
    elif mtype == "sticker":
        Message.objects.create(
            friend=friend, direction="incoming", message_type="sticker",
            content=_sticker_content(message),
        )
    elif mtype in ("image", "video", "audio", "file"):
        # 実体を LINE コンテンツ API で取得し R2/ローカルへ保存。content=保存先URL。
        content = _MEDIA_LABELS.get(mtype, f"[{mtype}]")
        msg_id = message.get("id")
        fetched = line_client.get_message_content(msg_id, access_token) if msg_id else None
        if fetched:
            data, ct = fetched
            key = f"line-media/{friend.id}/{msg_id}.{_ext_for(ct)}"
            try:
                content = _save_media(data, ct, key, request)
            except Exception:  # noqa: BLE001
                content = _MEDIA_LABELS.get(mtype, f"[{mtype}]")
        Message.objects.create(
            friend=friend, direction="incoming", message_type=mtype, content=content,
        )
    else:
        # 位置情報 等はプレースホルダで記録
        Message.objects.create(
            friend=friend, direction="incoming", message_type=mtype,
            content=_MEDIA_LABELS.get(mtype, f"[{mtype}]"),
        )

    # キーワード自動応答 (テキストのみ) を先に判定
    matched_auto_reply = False
    if mtype == "text":
        reply_token = event.get("replyToken")
        for ar in AutoReply.objects.filter(is_active=True):
            if _matches(ar, text):
                matched_auto_reply = True
                if reply_token:
                    sent, _ = line_client.reply_text(reply_token, ar.response_content, access_token)
                    if sent:
                        Message.objects.create(
                            friend=friend, direction="outgoing",
                            message_type=ar.response_type, content=ar.response_content,
                            delivery_type="reply",
                        )
                break

    # チャット更新: 自動応答で処理されなかった受信は「未読(要対応)」にする。
    # (オペレーター対応中でも新着があれば未読に戻して気付けるようにする)
    chat, _ = Chat.objects.get_or_create(friend=friend)
    chat.last_message_at = now
    if not matched_auto_reply:
        chat.status = "unread"
    chat.save()


_HANDLERS = {
    "follow": _handle_follow,
    "unfollow": _handle_unfollow,
    "message": _handle_message,
}


def _sig_ok(secret, body_bytes, signature):
    mac = hmac.new(secret.encode(), body_bytes, hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(mac).decode(), signature)


def _resolve_signature(request):
    """
    署名を検証し、マッチしたアカウントを返す。
    戻り値: (account_or_None, valid, access_token_or_None)
    """
    signature = request.headers.get("X-Line-Signature", "")
    body = request.body

    candidates = []  # (account_or_None, secret, access_token)
    for acc in LineAccount.objects.filter(is_active=True):
        if acc.channel_secret:
            candidates.append((acc, acc.channel_secret, acc.channel_access_token))
    global_secret = get_line_channel_secret()
    if global_secret:
        candidates.append((None, global_secret, get_line_access_token()))

    # 何も設定が無ければ検証スキップ (ローカル/未接続時)
    if not candidates:
        return None, True, None

    for acc, secret, token in candidates:
        if _sig_ok(secret, body, signature):
            return acc, True, token
    return None, False, None


@api_view(["POST"])
@permission_classes([AllowAny])
def line_webhook(request):
    """中継 Worker からの LINE イベントを取り込む。"""
    # ① 共有シークレット認証 (Worker からの呼び出しか, 定数時間比較)
    provided = request.headers.get("X-Relay-Secret", "")
    if not hmac.compare_digest(provided, get_relay_secret()):
        return Response({"success": False, "error": "unauthorized"}, status=401)

    # ② LINE 署名検証 (登録アカウントの channel secret を使用)
    account, valid, access_token = _resolve_signature(request)
    if not valid:
        return Response({"success": False, "error": "invalid signature"}, status=401)

    events = (request.data or {}).get("events", [])
    for event in events:
        try:
            handler = _HANDLERS.get(event.get("type"))
            if handler:
                handler(event, access_token, request)
        except Exception as exc:  # noqa: BLE001 — 1件の失敗で全体を止めない
            print(f"[line_webhook] event error: {exc}")

    return Response({"success": True, "data": {"processed": len(events)}})
