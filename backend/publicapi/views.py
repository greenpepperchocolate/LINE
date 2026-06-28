"""
LINE 公開導線 (旧 Cloudflare Worker apps/worker/src/routes の移管)。

- GET /auth/line       : LINE Login の認可URLへ 302 リダイレクト
- GET /auth/callback   : OAuth コールバック (コード交換 → id_token 検証 → 友だち紐付け)
- GET /r/<ref_code>    : クリック記録 → /auth/line?ref=<ref_code> へ 302

すべて公開エンドポイント (AllowAny)。LINE Login 資格情報が未設定の
ローカル環境でも例外で落とさず、説明用 HTML を返す (早期 return)。
外部 HTTP は標準ライブラリ urllib のみ使用 (crm/line_client.py 準拠)。
"""
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid

from django.http import HttpResponse, HttpResponseRedirect
from django.utils.html import escape
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

LINE_AUTHORIZE_URL = "https://access.line.me/oauth2/v2.1/authorize"
LINE_TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
LINE_VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify"
LINE_PROFILE_URL = "https://api.line.me/v2/profile"


# ---------------------------------------------------------------------------
# 共通ヘルパー
# ---------------------------------------------------------------------------
def _encode_state(payload):
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_state(state):
    if not state:
        return {}
    try:
        raw = base64.urlsafe_b64decode(state.encode("ascii"))
        return json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _safe_redirect_target(target):
    """
    オープンリダイレクト対策。http(s):// と相対パスのみ許可し、
    javascript:/data:/protocol-relative (//evil) は拒否する。
    """
    if not target:
        return None
    t = target.strip()
    low = t.lower()
    if low.startswith("javascript:") or low.startswith("data:") or low.startswith("vbscript:"):
        return None
    if t.startswith("//"):
        return None
    if t.startswith("/") or low.startswith("http://") or low.startswith("https://"):
        return t
    return None


def _resolve_login_credentials(ref, account_param):
    """
    LINE Login の (channel_id, channel_secret, account_channel_id) を解決する。
    優先順位 (worker /auth/line 準拠):
      1. ?account= (LineAccount.channel_id) の login_channel_id/secret
      2. ref → EntryRoute.pool_id → プールの有効アカウント
      3. 'main' TrafficPool の有効アカウント
      4. 環境変数 (LINE_LOGIN_CHANNEL_ID / LINE_LOGIN_CHANNEL_SECRET)
    どれも解決できなければ (None, None, None) を返す。
    """
    # 遅延 import (循環/未ロード回避)
    try:
        from crm.models import LineAccount
    except Exception:  # noqa: BLE001
        LineAccount = None

    def _from_account(acct):
        if acct and acct.login_channel_id:
            return (acct.login_channel_id, acct.login_channel_secret or "", acct.channel_id)
        return None

    # 1. ?account=
    if account_param and LineAccount is not None:
        try:
            acct = LineAccount.objects.filter(channel_id=account_param).first()
            resolved = _from_account(acct)
            if resolved:
                return resolved
        except Exception:  # noqa: BLE001
            pass

    # 2. ref → EntryRoute.pool_id
    if ref:
        try:
            from marketing.models import EntryRoute
            from pools.models import PoolAccount, TrafficPool

            route = EntryRoute.objects.filter(ref_code=ref, is_active=True).first()
            if route and route.pool_id:
                pool = TrafficPool.objects.filter(id=route.pool_id, is_active=True).first()
                if pool:
                    resolved = _resolve_from_pool(pool, PoolAccount)
                    if resolved:
                        return resolved
        except Exception:  # noqa: BLE001
            pass

    # 3. 'main' プール
    try:
        from pools.models import PoolAccount, TrafficPool

        pool = TrafficPool.objects.filter(slug="main", is_active=True).first()
        if pool:
            resolved = _resolve_from_pool(pool, PoolAccount)
            if resolved:
                return resolved
    except Exception:  # noqa: BLE001
        pass

    # 4. 環境変数フォールバック
    env_id = os.environ.get("LINE_LOGIN_CHANNEL_ID", "")
    env_secret = os.environ.get("LINE_LOGIN_CHANNEL_SECRET", "")
    if env_id:
        return (env_id, env_secret, account_param or "")

    return (None, None, None)


def _resolve_from_pool(pool, PoolAccount):
    """プールから有効な LINE アカウントの Login 資格情報を 1 件選ぶ。"""
    try:
        membership = (
            PoolAccount.objects.filter(pool=pool, is_active=True)
            .select_related("line_account")
            .order_by("?")
            .first()
        )
        if membership and membership.line_account and membership.line_account.login_channel_id:
            acct = membership.line_account
            return (acct.login_channel_id, acct.login_channel_secret or "", acct.channel_id)
    except Exception:  # noqa: BLE001
        pass
    # pool_accounts が無ければ active_account にフォールバック
    acct = getattr(pool, "active_account", None)
    if acct and acct.login_channel_id:
        return (acct.login_channel_id, acct.login_channel_secret or "", acct.channel_id)
    return None


def _http_post_form(url, fields, timeout=10):
    """application/x-www-form-urlencoded POST。(ok, parsed_json_or_text) を返す。"""
    data = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            try:
                return True, json.loads(body)
            except Exception:  # noqa: BLE001
                return True, body
    except urllib.error.HTTPError as e:
        return False, f"{e.code}: {e.read().decode('utf-8', 'ignore')}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def _http_get_json(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# HTML レスポンス
# ---------------------------------------------------------------------------
def _html(body, status=200):
    return HttpResponse(body, status=status, content_type="text/html; charset=utf-8")


def _page(title, message, status=200):
    return _html(
        f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Hiragino Sans',system-ui,sans-serif;background:#f5f7f5;
display:flex;justify-content:center;align-items:center;min-height:100vh}}
.card{{background:#fff;border-radius:20px;box-shadow:0 2px 20px rgba(0,0,0,.06);
text-align:center;max-width:480px;width:90%;padding:48px;border:1px solid rgba(0,0,0,.04)}}
h1{{font-size:18px;color:#222;margin-bottom:16px}}
p{{font-size:14px;color:#555;line-height:1.7}}
</style></head>
<body><div class="card"><h1>{escape(title)}</h1><p>{message}</p></div></body></html>""",
        status=status,
    )


def _error_page(message):
    return _page("エラー", escape(message), status=400)


# ---------------------------------------------------------------------------
# GET /auth/line — LINE Login 認可URLへリダイレクト
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def auth_line(request):
    ref = request.GET.get("ref", "") or ""
    account = request.GET.get("account", "") or ""
    redirect = request.GET.get("redirect", "") or ""

    channel_id, _secret, account_channel_id = _resolve_login_credentials(ref, account)
    if not channel_id:
        return _page(
            "LINE Login 未設定",
            "LINE Login の資格情報が設定されていません。"
            "管理画面の「LINEアカウント管理」で Login チャネル ID / シークレットを"
            "登録するか、環境変数 LINE_LOGIN_CHANNEL_ID を設定してください。",
        )

    callback_url = request.build_absolute_uri("/auth/callback")
    state = _encode_state({"ref": ref, "redirect": redirect, "account": account or account_channel_id or ""})

    params = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": channel_id,
            "redirect_uri": callback_url,
            "scope": "profile openid email",
            "bot_prompt": "aggressive",
            "state": state,
        }
    )
    return HttpResponseRedirect(f"{LINE_AUTHORIZE_URL}?{params}")


# ---------------------------------------------------------------------------
# GET /auth/callback — LINE Login コールバック
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def auth_callback(request):
    code = request.GET.get("code")
    state_param = request.GET.get("state", "") or ""
    oauth_error = request.GET.get("error")

    state = _decode_state(state_param)
    ref = state.get("ref", "") or ""
    redirect = state.get("redirect", "") or ""
    account = state.get("account", "") or ""

    if oauth_error or not code:
        return _error_page(oauth_error or "認可に失敗しました")

    # Login 資格情報を解決 (channel_id だけでなく secret も必要)
    channel_id, channel_secret, _acct = _resolve_login_credentials(ref, account)
    if not channel_id or not channel_secret:
        return _page(
            "LINE Login 未設定",
            "LINE Login の資格情報 (channel_id / secret) が解決できませんでした。"
            "管理画面でアカウントを登録してください。",
        )

    callback_url = request.build_absolute_uri("/auth/callback")

    # 1. コード → トークン交換
    ok_token, tokens = _http_post_form(
        LINE_TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": callback_url,
            "client_id": channel_id,
            "client_secret": channel_secret,
        },
    )
    if not ok_token or not isinstance(tokens, dict) or "id_token" not in tokens:
        return _error_page("トークン交換に失敗しました")

    # 2. id_token 検証 → sub (= LINE userId)
    ok_verify, verified = _http_post_form(
        LINE_VERIFY_URL,
        {"id_token": tokens["id_token"], "client_id": channel_id},
    )
    if not ok_verify or not isinstance(verified, dict) or not verified.get("sub"):
        return _error_page("id_token の検証に失敗しました")

    line_user_id = verified["sub"]
    display_name = verified.get("name") or "Unknown"
    picture_url = verified.get("picture")

    # 3. アクセストークンでプロフィール補完 (任意・失敗許容)
    access_token = tokens.get("access_token")
    if access_token:
        profile = _http_get_json(
            LINE_PROFILE_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
        if isinstance(profile, dict):
            display_name = profile.get("displayName") or display_name
            picture_url = profile.get("pictureUrl") or picture_url

    # 4. Friend を upsert + ref_code / user_id 紐付け
    try:
        from crm.models import Friend

        friend, created = Friend.objects.get_or_create(
            line_user_id=line_user_id,
            defaults={
                "display_name": display_name or "",
                "picture_url": picture_url,
            },
        )
        changed = False
        if not created:
            if display_name and friend.display_name != display_name:
                friend.display_name = display_name
                changed = True
            if picture_url and friend.picture_url != picture_url:
                friend.picture_url = picture_url
                changed = True
        # first-touch: ref_code は未設定の時だけ書き込む
        if ref and not friend.ref_code:
            friend.ref_code = ref
            changed = True
        # user_id 採番 (未設定なら UUID を発番)
        if not friend.user_id:
            friend.user_id = str(uuid.uuid4())
            changed = True
        if changed or created:
            friend.save()
    except Exception:  # noqa: BLE001
        # DB 紐付けに失敗しても OAuth 自体は成立しているので落とさない
        pass

    # 5. リダイレクト or 完了 HTML
    safe = _safe_redirect_target(redirect)
    if safe:
        return HttpResponseRedirect(safe)

    pic = (
        f'<img src="{escape(picture_url)}" alt="" '
        'style="width:72px;height:72px;border-radius:50%;margin-bottom:16px">'
        if picture_url
        else ""
    )
    return _html(
        f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>友だち追加が完了しました</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Hiragino Sans',system-ui,sans-serif;background:#f5f7f5;
display:flex;justify-content:center;align-items:center;min-height:100vh}}
.card{{background:#fff;border-radius:20px;box-shadow:0 2px 20px rgba(0,0,0,.06);
text-align:center;max-width:480px;width:90%;padding:48px;border:1px solid rgba(0,0,0,.04)}}
h1{{font-size:18px;color:#06C755;margin-bottom:12px}}
p{{font-size:14px;color:#555;line-height:1.7}}
</style></head>
<body><div class="card">{pic}
<h1>友だち追加が完了しました</h1>
<p>{escape(display_name)} さん、ありがとうございます。<br>このままLINEアプリに戻ってください。</p>
</div></body></html>"""
    )


# ---------------------------------------------------------------------------
# GET /r/<ref_code> — クリック記録 → /auth/line?ref=... へ
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def tracking_redirect(request, ref_code):
    # クリック記録 (失敗してもリダイレクトは続行)
    try:
        from .models import LinkClick

        LinkClick.objects.create(
            ref_code=ref_code,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:2000] or None,
            ip_address=(
                request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
                or request.META.get("REMOTE_ADDR")
                or None
            ),
            referer=request.META.get("HTTP_REFERER") or None,
        )
    except Exception:  # noqa: BLE001
        pass

    # ref 以外のクエリ (account / redirect 等) も引き継ぐ
    passthrough = {k: v for k, v in request.GET.items() if k != "ref"}
    passthrough["ref"] = ref_code
    qs = urllib.parse.urlencode(passthrough)
    target = request.build_absolute_uri("/auth/line")
    return HttpResponseRedirect(f"{target}?{qs}")


# ----------------------------------------------------------------------------
# 自己アップデート機能のスタブ (/admin/version, /admin/update/*)
# 注意: 自己アップデートは Cloudflare Worker 専用機構であり、Django バックエンド
#       には適用されない。UI がエラーにならないよう互換レスポンスを返すスタブ。
# ----------------------------------------------------------------------------
from rest_framework.decorators import api_view as _api_view  # noqa: E402
from rest_framework.decorators import permission_classes as _perm  # noqa: E402
from rest_framework.permissions import AllowAny as _AllowAny  # noqa: E402
from rest_framework.response import Response as _Response  # noqa: E402


@_api_view(["GET"])
@_perm([_AllowAny])
def admin_version(request):
    return _Response({
        "version": "0.15.0-django",
        "worker_hash": "", "admin_hash": "", "liff_hash": "",
    })


@_api_view(["GET"])
@_perm([_AllowAny])
def admin_update_history(request):
    return _Response({"history": []})


@_api_view(["POST"])
@_perm([_AllowAny])
def admin_update_start(request):
    return _Response(
        {"error": "self-update is not supported on the Django backend"},
        status=400,
    )


@_api_view(["GET"])
@_perm([_AllowAny])
def admin_update_status(request, update_id):
    return _Response({
        "id": update_id, "status": "unsupported", "events": [],
        "error": "self-update is not supported on the Django backend",
    })
