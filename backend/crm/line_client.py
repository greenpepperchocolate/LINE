"""
LINE Messaging API クライアント (標準ライブラリ urllib のみ使用)。
返信 (reply) / プッシュ (push) / プロフィール取得をサポート。
"""
import json
import urllib.error
import urllib.request

from .config import get_line_access_token

LINE_API_BASE = "https://api.line.me/v2/bot"


def _post(path, payload, access_token=None):
    token = access_token or get_line_access_token()
    if not token:
        # トークン未設定ならスキップ (ローカルで LINE 未接続でも落とさない)
        return False, "LINE_CHANNEL_ACCESS_TOKEN 未設定"
    req = urllib.request.Request(
        f"{LINE_API_BASE}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return False, f"{e.code}: {e.read().decode('utf-8', 'ignore')}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def reply_text(reply_token, text, access_token=None):
    """replyToken を使って即時返信 (無料)。"""
    return _post(
        "/message/reply",
        {"replyToken": reply_token, "messages": [{"type": "text", "text": text}]},
        access_token,
    )


def push_text(line_user_id, text, access_token=None):
    """任意のタイミングでプッシュ送信。"""
    return _post(
        "/message/push",
        {"to": line_user_id, "messages": [{"type": "text", "text": text}]},
        access_token,
    )


def get_profile(line_user_id, access_token=None):
    """友だちのプロフィールを取得。失敗時は None。"""
    token = access_token or get_line_access_token()
    if not token:
        return None
    req = urllib.request.Request(
        f"{LINE_API_BASE}/profile/{line_user_id}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None
