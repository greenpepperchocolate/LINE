from datetime import date, timedelta

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from common.responses import err  # noqa: F401  (共通エラーレスポンス)

from .models import BookingMenu, BookingRequest, BookingStaff, Shift, StaffMenu
from .serializers import (
    BookingMenuSerializer,
    BookingRequestSerializer,
    BookingShiftSerializer,
    BookingStaffSerializer,
)

# 認証はグローバル設定 (IsAuthenticated) により全エンドポイント JWT 必須。
# フロント (apps/web の bookingApi) は ?account_id= でアカウントスコープし、
# 生のレスポンス形 ({menus:[...]}, {id}, {ok:true} 等) を期待するため、
# 成功時は common.responses.ok ラッパーを使わず Response で素の dict を返す。


def _account_id(request):
    """?account_id= を取得 (アカウントスコープ用)。"""
    return request.query_params.get("account_id")


# ----------------------------------------------------------------------------
# Menus
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def menus(request):
    account_id = _account_id(request)

    if request.method == "GET":
        qs = BookingMenu.objects.all()
        if account_id:
            qs = qs.filter(line_account_id=account_id)
        return Response({"menus": BookingMenuSerializer(qs, many=True).data})

    serializer = BookingMenuSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    menu = serializer.save(line_account_id=account_id)
    return Response({"id": str(menu.id)}, status=201)


@api_view(["PUT", "DELETE"])
def menu_detail(request, id):
    menu = get_object_or_404(BookingMenu, id=id)

    if request.method == "DELETE":
        menu.delete()
        return Response({"ok": True})

    serializer = BookingMenuSerializer(menu, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return Response({"ok": True})


# ----------------------------------------------------------------------------
# Staff
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def staff(request):
    account_id = _account_id(request)

    if request.method == "GET":
        qs = BookingStaff.objects.all()
        if account_id:
            qs = qs.filter(line_account_id=account_id)
        return Response({"staff": BookingStaffSerializer(qs, many=True).data})

    serializer = BookingStaffSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    member = serializer.save(line_account_id=account_id)
    return Response({"id": str(member.id)}, status=201)


@api_view(["GET", "PUT", "DELETE"])
def staff_detail(request, id):
    member = get_object_or_404(BookingStaff, id=id)

    if request.method == "GET":
        return Response(BookingStaffSerializer(member).data)

    if request.method == "DELETE":
        member.delete()
        return Response({"ok": True})

    serializer = BookingStaffSerializer(member, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return Response({"ok": True})


# ----------------------------------------------------------------------------
# Staff x Menu マトリクス
# ----------------------------------------------------------------------------
@api_view(["GET", "PUT"])
def staff_menus(request, id):
    member = get_object_or_404(BookingStaff, id=id)
    account_id = _account_id(request) or member.line_account_id

    if request.method == "GET":
        menu_qs = BookingMenu.objects.all()
        if account_id:
            menu_qs = menu_qs.filter(line_account_id=account_id)

        offered = {sm.menu_id: sm for sm in member.staff_menus.all()}
        matrix = []
        for m in menu_qs:
            sm = offered.get(m.id)
            matrix.append({
                "menu_id": str(m.id),
                "name": m.name,
                "is_offered": sm.is_offered if sm else 0,
                "override_duration_minutes": sm.override_duration_minutes if sm else None,
                "override_price": sm.override_price if sm else None,
            })
        return Response({"matrix": matrix})

    # PUT: menus=[{menu_id, is_offered, override_duration_minutes?, override_price?}]
    for row in request.data.get("menus", []):
        menu_id = row.get("menu_id")
        if not menu_id:
            continue
        if not BookingMenu.objects.filter(id=menu_id).exists():
            continue
        StaffMenu.objects.update_or_create(
            staff=member,
            menu_id=menu_id,
            defaults={
                "is_offered": 1 if row.get("is_offered") else 0,
                "override_duration_minutes": row.get("override_duration_minutes"),
                "override_price": row.get("override_price"),
            },
        )
    return Response({"ok": True})


# ----------------------------------------------------------------------------
# Shifts
# ----------------------------------------------------------------------------
@api_view(["GET", "PUT", "POST"])
def staff_shifts(request, id):
    member = get_object_or_404(BookingStaff, id=id)

    if request.method == "GET":
        qs = member.shifts.all()
        return Response({"shifts": BookingShiftSerializer(qs, many=True).data})

    # PUT / POST: shifts=[{work_date, start_time, end_time}] で全置換
    rows = request.data.get("shifts", [])
    member.shifts.all().delete()
    objs = [
        Shift(
            staff=member,
            work_date=r.get("work_date"),
            start_time=r.get("start_time"),
            end_time=r.get("end_time"),
        )
        for r in rows
        if r.get("work_date") and r.get("start_time") and r.get("end_time")
    ]
    Shift.objects.bulk_create(objs)
    return Response({"ok": True, "count": len(objs)})


@api_view(["PUT", "DELETE"])
def staff_shift_detail(request, id, shift_id):
    shift = get_object_or_404(Shift, id=shift_id, staff_id=id)

    if request.method == "DELETE":
        shift.delete()
        return Response({"ok": True})

    serializer = BookingShiftSerializer(shift, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return Response({"ok": True})


# 曜日キー → Python weekday (Mon=0 .. Sun=6) のマッピング。
# weekly_template のキーは複数フォーマットを許容する。
_WEEKDAY_NAMES = {
    "mon": 0, "monday": 0,
    "tue": 1, "tues": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2,
    "thu": 3, "thur": 3, "thurs": 3, "thursday": 3,
    "fri": 4, "friday": 4,
    "sat": 5, "saturday": 5,
    "sun": 6, "sunday": 6,
}


def _template_for(weekly_template, d):
    """日付 d に対応する weekly_template エントリ (or None) を返す。"""
    py_wd = d.weekday()            # Mon=0 .. Sun=6
    js_wd = (d.weekday() + 1) % 7  # Sun=0 .. Sat=6 (JS getDay 互換)
    candidates = [
        str(py_wd),
        str(js_wd),
        d.strftime("%a").lower(),
        d.strftime("%A").lower(),
    ]
    for key, val in weekly_template.items():
        k = str(key).strip().lower()
        # 名前キーは weekday へ正規化して比較
        normalized = _WEEKDAY_NAMES.get(k, k)
        if k in candidates or str(normalized) == str(py_wd):
            return val
    return None


@api_view(["POST"])
def staff_shifts_generate(request, id):
    """
    シフト自動生成 (簡易版)。
    body: { from_date: "YYYY-MM-DD", weeks: int,
            weekly_template: { <曜日>: {start, end} | null } }
    from_date から weeks 週分、weekly_template に従って Shift を生成。
    既存 (staff, work_date, start_time) と重複する枠はスキップ。
    """
    member = get_object_or_404(BookingStaff, id=id)

    from_date_str = request.data.get("from_date")
    weeks = request.data.get("weeks", 1)
    weekly_template = request.data.get("weekly_template") or {}

    if not from_date_str:
        return err("from_date は必須です", status=400)
    try:
        start = date.fromisoformat(from_date_str)
        weeks = int(weeks)
    except (TypeError, ValueError):
        return err("from_date / weeks の形式が不正です", status=400)

    existing = {
        (s.work_date.isoformat(), s.start_time)
        for s in member.shifts.all()
    }
    inserted = 0
    total_days = max(0, weeks) * 7
    for offset in range(total_days):
        d = start + timedelta(days=offset)
        tpl = _template_for(weekly_template, d)
        if not tpl:
            continue
        start_time = tpl.get("start")
        end_time = tpl.get("end")
        if not start_time or not end_time:
            continue
        key = (d.isoformat(), start_time)
        if key in existing:
            continue
        Shift.objects.create(
            staff=member, work_date=d, start_time=start_time, end_time=end_time,
        )
        existing.add(key)
        inserted += 1

    return Response({"inserted": inserted})


# ----------------------------------------------------------------------------
# 予約リクエスト
# ----------------------------------------------------------------------------
# action -> 遷移後ステータス
_ACTION_STATUS = {
    "approve": "confirmed",
    "reject": "rejected",
    "cancel": "cancelled",
    "no_show": "no_show",
    "complete": "completed",
}


@api_view(["GET"])
def requests_list(request):
    account_id = _account_id(request)
    qs = BookingRequest.objects.select_related("menu", "staff", "friend")
    if account_id:
        qs = qs.filter(line_account_id=account_id)
    status_filter = request.query_params.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)
    return Response({"requests": BookingRequestSerializer(qs, many=True).data})


@api_view(["PUT", "PATCH"])
def request_detail(request, id):
    booking = get_object_or_404(BookingRequest, id=id)
    action = request.data.get("action")
    new_status = _ACTION_STATUS.get(action)
    if not new_status:
        return err("action が不正です", status=400)
    booking.status = new_status
    booking.save(update_fields=["status", "updated_at"])
    return Response({"status": booking.status})


@api_view(["GET"])
def pending_count(request):
    account_id = _account_id(request)
    qs = BookingRequest.objects.filter(status="requested")
    if account_id:
        qs = qs.filter(line_account_id=account_id)
    return Response({"count": qs.count()})
