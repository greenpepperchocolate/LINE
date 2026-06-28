from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view

from common.responses import err, ok
from crm.models import Friend, LineAccount, Message

from .models import AccountHealthLog, AccountMigration, StaffMember, User
from .models import generate_api_key
from .serializers import (
    AccountHealthLogSerializer,
    AccountMigrationSerializer,
    StaffMemberSerializer,
    UserSerializer,
)

# 認証はグローバル設定 (IsAuthenticated) により全て JWT 必須。


def _account_name_map():
    """LineAccount.id (str) -> name の辞書。"""
    return {str(a.id): a.name for a in LineAccount.objects.all()}


def _paginate_rows(rows, page, page_size):
    """Python リストを page / pageSize でスライスする。"""
    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    return rows[start:end], total


def _int_param(request, key, default):
    try:
        v = int(request.query_params.get(key, default))
        return v if v > 0 else default
    except (TypeError, ValueError):
        return default


# ----------------------------------------------------------------------------
# Users (cross-account の内部ユーザー)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def users_list(request):
    if request.method == "GET":
        qs = User.objects.all()
        return ok(UserSerializer(qs, many=True).data)

    serializer = UserSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    user = serializer.save()
    return ok(UserSerializer(user).data, status=201)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "GET":
        return ok(UserSerializer(user).data)

    if request.method == "DELETE":
        user.delete()
        return ok(None)

    serializer = UserSerializer(user, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(UserSerializer(user).data)


@api_view(["POST"])
def user_link(request, user_id):
    """友だち (crm.Friend) を内部ユーザーに紐づける。"""
    user = get_object_or_404(User, id=user_id)
    friend_id = request.data.get("friendId")
    if not friend_id:
        return err("friendId は必須です", status=400)
    friend = get_object_or_404(Friend, id=friend_id)
    friend.user_id = str(user.id)
    friend.save(update_fields=["user_id", "updated_at"])
    return ok(None)


@api_view(["GET"])
def user_accounts(request, user_id):
    """内部ユーザーに紐づく友だち (= 各 LINE アカウントでの友だち) 一覧。"""
    user = get_object_or_404(User, id=user_id)
    friends = Friend.objects.filter(user_id=str(user.id))
    data = [
        {
            "id": str(f.id),
            "lineUserId": f.line_user_id,
            "displayName": f.display_name or None,
            "isFollowing": f.is_following,
        }
        for f in friends
    ]
    return ok(data)


# ----------------------------------------------------------------------------
# Users grouped (友だちを同一人物でまとめる)
# ----------------------------------------------------------------------------
@api_view(["GET"])
def users_grouped(request):
    q = (request.query_params.get("q") or "").strip()
    only_dups = request.query_params.get("onlyDups") in ("1", "true")
    account = request.query_params.get("account")
    page = _int_param(request, "page", 1)
    page_size = _int_param(request, "pageSize", 50)

    name_map = _account_name_map()

    # 友だちの最新メッセージから所属アカウントを推定する。
    friend_account = {}
    for m in Message.objects.exclude(line_account_id__isnull=True).order_by("created_at"):
        if m.line_account_id:
            friend_account[m.friend_id] = m.line_account_id

    groups = {}  # key -> row dict
    for f in Friend.objects.all():
        if q and q.lower() not in (f.display_name or "").lower():
            continue
        if f.user_id:
            key, kind = f.user_id, "uid"
        else:
            key, kind = str(f.id), "solo"

        acc_id = friend_account.get(f.id) or ""
        if account and acc_id != account:
            continue

        joined_at = f.created_at.isoformat() if f.created_at else ""
        activity_at = f.updated_at.isoformat() if f.updated_at else joined_at
        acc_entry = {
            "accountId": acc_id,
            "accountName": name_map.get(acc_id, ""),
            "lineUserId": f.line_user_id,
            "isFollowing": f.is_following,
            "joinedAt": joined_at,
            "friendId": str(f.id),
        }

        row = groups.get(key)
        if row is None:
            groups[key] = {
                "identityKey": key,
                "identityKeyKind": kind,
                "displayName": f.display_name or None,
                "pictureUrl": f.picture_url or None,
                "accounts": [acc_entry],
                "xUsername": None,
                "emails": [],
                "phones": [],
                "lastActivityAt": activity_at,
                "isDuplicate": False,
            }
        else:
            row["accounts"].append(acc_entry)
            if activity_at > row["lastActivityAt"]:
                row["lastActivityAt"] = activity_at

    rows = list(groups.values())
    for row in rows:
        row["isDuplicate"] = len(row["accounts"]) > 1
    if only_dups:
        rows = [r for r in rows if r["isDuplicate"]]
    rows.sort(key=lambda r: r["lastActivityAt"], reverse=True)

    page_rows, total = _paginate_rows(rows, page, page_size)
    return ok({
        "total": total,
        "page": page,
        "pageSize": page_size,
        "computedAt": timezone.now().isoformat(),
        "rows": page_rows,
    })


# ----------------------------------------------------------------------------
# Staff
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def staff_list(request):
    if request.method == "GET":
        qs = StaffMember.objects.all()
        return ok(StaffMemberSerializer(qs, many=True).data)

    name = request.data.get("name")
    if not name:
        return err("name は必須です", status=400)
    staff = StaffMember.objects.create(
        name=name,
        email=request.data.get("email") or None,
        role=request.data.get("role") or "staff",
    )
    return ok(StaffMemberSerializer(staff).data, status=201)


@api_view(["GET"])
def staff_me(request):
    """ログイン中ユーザー (accounts.User) の情報を返す。"""
    u = request.user
    return ok({
        "id": str(u.id),
        "name": getattr(u, "name", "") or "",
        "role": getattr(u, "role", "staff"),
        "email": getattr(u, "email", None),
    })


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def staff_detail(request, id):
    staff = get_object_or_404(StaffMember, id=id)

    if request.method == "GET":
        return ok(StaffMemberSerializer(staff).data)

    if request.method == "DELETE":
        staff.delete()
        return ok(None)

    data = request.data
    if "name" in data:
        staff.name = data.get("name")
    if "email" in data:
        staff.email = data.get("email") or None
    if "role" in data:
        staff.role = data.get("role")
    if "isActive" in data:
        staff.is_active = bool(data.get("isActive"))
    staff.save()
    return ok(StaffMemberSerializer(staff).data)


@api_view(["POST"])
def staff_regenerate_key(request, id):
    staff = get_object_or_404(StaffMember, id=id)
    staff.api_key = generate_api_key()
    staff.save(update_fields=["api_key", "updated_at"])
    return ok({"apiKey": staff.api_key})


# ----------------------------------------------------------------------------
# Inbox (未返信)
# ----------------------------------------------------------------------------
def _unanswered_rows(request):
    """最新メッセージが incoming の友だち = 未返信、を行データとして返す。"""
    q = (request.query_params.get("q") or "").strip()
    account = request.query_params.get("account")
    min_wait = _int_param(request, "minWaitMinutes", 0) if request.query_params.get("minWaitMinutes") else 0
    name_map = _account_name_map()
    now = timezone.now()

    # 友だちごとの incoming / outgoing 最新を集計。
    last_incoming = {}   # friend_id -> Message
    last_outgoing = {}   # friend_id -> Message
    incoming_account = {}  # friend_id -> account id (最新 incoming の)
    for m in Message.objects.all().order_by("created_at"):
        if m.direction == "incoming":
            last_incoming[m.friend_id] = m
            incoming_account[m.friend_id] = m.line_account_id or ""
        else:
            last_outgoing[m.friend_id] = m

    rows = []
    friends = {f.id: f for f in Friend.objects.all()}
    for fid, inc in last_incoming.items():
        out = last_outgoing.get(fid)
        # outgoing が incoming より後なら返信済み。
        if out and out.created_at >= inc.created_at:
            continue
        f = friends.get(fid)
        if not f:
            continue
        if q and q.lower() not in (f.display_name or "").lower():
            continue
        acc_id = incoming_account.get(fid, "")
        if account and acc_id != account:
            continue
        wait_minutes = (now - inc.created_at).total_seconds() / 60 if inc.created_at else 0
        if min_wait and wait_minutes < min_wait:
            continue
        rows.append({
            "friendId": str(f.id),
            "displayName": f.display_name or None,
            "pictureUrl": f.picture_url or None,
            "accountId": acc_id,
            "accountName": name_map.get(acc_id, ""),
            "lastIncomingAt": inc.created_at.isoformat() if inc.created_at else "",
            "lastManualAt": out.created_at.isoformat() if out and out.created_at else None,
            "lastMachineAt": None,
            "lastIncomingType": inc.message_type,
            "lastIncomingContent": inc.content,
            "_waitMinutes": wait_minutes,
        })

    rows.sort(key=lambda r: r["lastIncomingAt"])
    return rows


@api_view(["GET"])
def inbox_unanswered(request):
    page = _int_param(request, "page", 1)
    page_size = _int_param(request, "pageSize", 50)
    rows = _unanswered_rows(request)
    for r in rows:
        r.pop("_waitMinutes", None)
    page_rows, total = _paginate_rows(rows, page, page_size)
    return ok({
        "total": total,
        "page": page,
        "pageSize": page_size,
        "rows": page_rows,
    })


@api_view(["GET"])
def inbox_unanswered_count(request):
    rows = _unanswered_rows(request)
    by_account = {}
    oldest_wait = None
    for r in rows:
        acc = r["accountId"]
        if acc not in by_account:
            by_account[acc] = {
                "accountId": acc,
                "accountName": r["accountName"],
                "count": 0,
            }
        by_account[acc]["count"] += 1
        wait = r.get("_waitMinutes", 0)
        if oldest_wait is None or wait > oldest_wait:
            oldest_wait = wait
    return ok({
        "total": len(rows),
        "byAccount": list(by_account.values()),
        "oldestWaitMinutes": int(oldest_wait) if oldest_wait is not None else None,
    })


# ----------------------------------------------------------------------------
# Health / Accounts 移行
# ----------------------------------------------------------------------------
@api_view(["GET"])
def account_health(request, id):
    qs = AccountHealthLog.objects.filter(line_account_id=str(id))
    latest = qs.first()
    risk_level = latest.risk_level if latest else "normal"
    return ok({
        "riskLevel": risk_level,
        "logs": AccountHealthLogSerializer(qs, many=True).data,
    })


@api_view(["GET"])
def account_migrations(request):
    qs = AccountMigration.objects.all()
    return ok(AccountMigrationSerializer(qs, many=True).data)


@api_view(["POST"])
def account_migrate(request, id):
    to_account_id = request.data.get("toAccountId")
    if not to_account_id:
        return err("toAccountId は必須です", status=400)
    # 簡易スタブ: 即時 completed としてレコードを作成する。
    migration = AccountMigration.objects.create(
        from_account_id=str(id),
        to_account_id=str(to_account_id),
        status="completed",
        migrated_count=0,
        total_count=0,
        completed_at=timezone.now(),
    )
    return ok(AccountMigrationSerializer(migration).data, status=201)


@api_view(["GET"])
def account_migration_detail(request, id):
    migration = get_object_or_404(AccountMigration, id=id)
    return ok(AccountMigrationSerializer(migration).data)
