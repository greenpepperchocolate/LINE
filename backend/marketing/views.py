from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view

from common.responses import err, ok

from crm.models import Friend

from .models import (
    Affiliate,
    AffiliateClick,
    Automation,
    AutomationLog,
    ConversionEvent,
    ConversionPoint,
    EntryRoute,
    ScoringRule,
)
from .serializers import (
    AffiliateSerializer,
    AutomationDetailSerializer,
    AutomationLogSerializer,
    AutomationSerializer,
    ConversionEventSerializer,
    ConversionPointSerializer,
    EntryRouteSerializer,
    ScoringRuleSerializer,
)

# 認証はグローバル設定 (IsAuthenticated) により全て JWT 必須。


# ----------------------------------------------------------------------------
# Conversions (CV 計測)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def conversion_points_list(request):
    if request.method == "GET":
        qs = ConversionPoint.objects.all()
        return ok(ConversionPointSerializer(qs, many=True).data)

    serializer = ConversionPointSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    point = serializer.save()
    return ok(ConversionPointSerializer(point).data, status=201)


@api_view(["PUT", "DELETE"])
def conversion_point_detail(request, id):
    point = get_object_or_404(ConversionPoint, id=id)
    if request.method == "DELETE":
        point.delete()
        return ok(None)
    serializer = ConversionPointSerializer(point, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(ConversionPointSerializer(point).data)


@api_view(["GET"])
def conversions_report(request):
    """CV 計測レポート (簡易集計)。"""
    start_date = request.query_params.get("startDate")
    end_date = request.query_params.get("endDate")

    result = []
    for point in ConversionPoint.objects.all():
        events = ConversionEvent.objects.filter(conversion_point=point)
        if start_date:
            events = events.filter(created_at__gte=start_date)
        if end_date:
            events = events.filter(created_at__lte=end_date)
        count = events.count()
        result.append({
            "conversionPointId": str(point.id),
            "conversionPointName": point.name,
            "eventType": point.event_type,
            "totalCount": count,
            "totalValue": (point.value or 0) * count,
        })
    return ok(result)


@api_view(["POST"])
def conversions_track(request):
    """CV イベント記録 (スタブ)。"""
    point_id = request.data.get("conversionPointId")
    friend_id = request.data.get("friendId")
    if not point_id:
        return err("conversionPointId は必須です", status=400)

    point = ConversionPoint.objects.filter(id=point_id).first()
    if point is None:
        return err("conversionPointId が不正です", status=400)

    friend = Friend.objects.filter(id=friend_id).first() if friend_id else None

    event = ConversionEvent.objects.create(
        conversion_point=point,
        friend=friend,
        user_id=request.data.get("userId"),
        affiliate_code=request.data.get("affiliateCode"),
        metadata=request.data.get("metadata") or {},
    )
    return ok(ConversionEventSerializer(event).data, status=201)


# ----------------------------------------------------------------------------
# Affiliates (アフィリエイト)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def affiliates_list(request):
    if request.method == "GET":
        qs = Affiliate.objects.all()
        return ok(AffiliateSerializer(qs, many=True).data)

    serializer = AffiliateSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    affiliate = serializer.save()
    return ok(AffiliateSerializer(affiliate).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def affiliate_detail(request, id):
    affiliate = get_object_or_404(Affiliate, id=id)
    if request.method == "GET":
        return ok(AffiliateSerializer(affiliate).data)
    if request.method == "DELETE":
        affiliate.delete()
        return ok(None)
    serializer = AffiliateSerializer(affiliate, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(AffiliateSerializer(affiliate).data)


@api_view(["GET"])
def affiliate_report(request, id):
    """アフィリエイトレポート (簡易集計)。"""
    affiliate = get_object_or_404(Affiliate, id=id)
    total_clicks = AffiliateClick.objects.filter(affiliate=affiliate).count()
    conversions = ConversionEvent.objects.filter(affiliate_code=affiliate.code)

    start_date = request.query_params.get("startDate")
    end_date = request.query_params.get("endDate")
    if start_date:
        conversions = conversions.filter(created_at__gte=start_date)
    if end_date:
        conversions = conversions.filter(created_at__lte=end_date)

    total_conversions = conversions.count()
    total_value = sum(
        (ev.conversion_point.value or 0) for ev in conversions.select_related("conversion_point")
    )
    total_revenue = total_value * (affiliate.commission_rate / 100.0)

    return ok({
        "affiliateId": str(affiliate.id),
        "affiliateName": affiliate.name,
        "code": affiliate.code,
        "commissionRate": affiliate.commission_rate,
        "totalClicks": total_clicks,
        "totalConversions": total_conversions,
        "totalRevenue": total_revenue,
    })


# ----------------------------------------------------------------------------
# Scoring (リードスコアリング)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def scoring_rules_list(request):
    if request.method == "GET":
        qs = ScoringRule.objects.all()
        return ok(ScoringRuleSerializer(qs, many=True).data)

    serializer = ScoringRuleSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    rule = serializer.save()
    return ok(ScoringRuleSerializer(rule).data, status=201)


@api_view(["PUT", "DELETE"])
def scoring_rule_detail(request, id):
    rule = get_object_or_404(ScoringRule, id=id)
    if request.method == "DELETE":
        rule.delete()
        return ok(None)
    serializer = ScoringRuleSerializer(rule, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(ScoringRuleSerializer(rule).data)


# ----------------------------------------------------------------------------
# Entry routes (流入経路)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def entry_routes_list(request):
    if request.method == "GET":
        qs = EntryRoute.objects.all()
        return ok(EntryRouteSerializer(qs, many=True).data)

    serializer = EntryRouteSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    route = serializer.save()
    return ok(EntryRouteSerializer(route).data, status=201)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def entry_route_detail(request, id):
    route = get_object_or_404(EntryRoute, id=id)
    if request.method == "GET":
        return ok(EntryRouteSerializer(route).data)
    if request.method == "DELETE":
        route.delete()
        return ok(None)
    # PUT / PATCH はどちらも部分更新として扱う
    serializer = EntryRouteSerializer(route, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(EntryRouteSerializer(route).data)


@api_view(["GET"])
def entry_route_funnel(request, id):
    """流入ファネル (簡易: 友だち追加数のみ ref_code 一致で集計、他は 0)。"""
    route = get_object_or_404(EntryRoute, id=id)
    friend_add_count = Friend.objects.filter(ref_code=route.ref_code).count()
    return ok({
        "click_count": 0,
        "friend_add_count": friend_add_count,
        "form_submission_count": 0,
        "cv_count": 0,
    })


# ----------------------------------------------------------------------------
# Automations (オートメーション)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def automations_list(request):
    if request.method == "GET":
        qs = Automation.objects.all()
        return ok(AutomationSerializer(qs, many=True).data)

    serializer = AutomationSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    automation = serializer.save()
    return ok(AutomationSerializer(automation).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def automation_detail(request, id):
    automation = get_object_or_404(Automation, id=id)
    if request.method == "GET":
        return ok(AutomationDetailSerializer(automation).data)
    if request.method == "DELETE":
        automation.delete()
        return ok(None)
    serializer = AutomationSerializer(automation, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(AutomationSerializer(automation).data)


@api_view(["GET"])
def automation_logs(request, id):
    automation = get_object_or_404(Automation, id=id)
    qs = automation.logs.all()
    try:
        limit = int(request.query_params.get("limit", 0))
    except (TypeError, ValueError):
        limit = 0
    if limit > 0:
        qs = qs[:limit]
    return ok(AutomationLogSerializer(qs, many=True).data)


# ----------------------------------------------------------------------------
# Segments (セグメント)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def segments_count(request):
    """条件に合う友だち数を返す (簡易: tagId 指定時のみ絞り込み)。"""
    conditions = request.data.get("conditions") if request.method == "POST" else None
    qs = Friend.objects.all()

    tag_id = None
    if isinstance(conditions, dict):
        tag_id = conditions.get("tagId")
    tag_id = tag_id or request.query_params.get("tagId")
    if tag_id:
        qs = qs.filter(tags__id=tag_id)

    count = qs.count()
    # フロントは top-level の `count` を読む。ApiResponse 互換のため data にも格納。
    return ok({"count": count}, count=count)


# ----------------------------------------------------------------------------
# Duplicates (重複検出)
# ----------------------------------------------------------------------------
@api_view(["GET"])
def duplicates_stats(request):
    """重複検出の統計 (簡易集計)。"""
    following = Friend.objects.filter(is_following=True)
    total_following = following.count()

    # user_id でグルーピングできるものは重複候補。null は各々ユニーク扱い。
    with_user = following.exclude(user_id__isnull=True).exclude(user_id="")
    without_user = total_following - with_user.count()
    distinct_user_ids = (
        with_user.values("user_id").annotate(c=Count("id"))
    )
    unique_grouped = distinct_user_ids.count()
    dup_groups = sum(1 for row in distinct_user_ids if row["c"] > 1)
    friend_dups = sum((row["c"] - 1) for row in distinct_user_ids if row["c"] > 1)
    unique_people = without_user + unique_grouped

    return ok({
        "totalFollowing": total_following,
        "uniquePeople": unique_people,
        "friendDups": friend_dups,
        "duplicateGroups": dup_groups,
        "wastedPerBroadcastYen": 0,
        "msgUnitYen": 3,
        "perAccount": [],
        "pairwiseOverlap": [],
    })


# ----------------------------------------------------------------------------
# Analytics (リファラル/流入 集計) — /api/analytics/*
# ----------------------------------------------------------------------------
from django.db.models import Max  # noqa: E402


@api_view(["GET"])
def analytics_ref_summary(request):
    """リファラル別の友だち数・クリック数サマリ。"""
    friends = Friend.objects.all()
    total = friends.count()
    with_ref_qs = friends.exclude(ref_code__isnull=True).exclude(ref_code="")
    with_ref = with_ref_qs.count()

    grouped = (
        with_ref_qs.values("ref_code")
        .annotate(friend_count=Count("id"), latest_at=Max("created_at"))
    )
    name_map = {e.ref_code: e.name for e in EntryRoute.objects.all()}

    # クリック数 (publicapi.LinkClick, 任意)
    click_map = {}
    try:
        from publicapi.models import LinkClick
        for row in LinkClick.objects.values("ref_code").annotate(c=Count("id")):
            click_map[row["ref_code"]] = row["c"]
    except Exception:  # noqa: BLE001
        pass

    routes = [
        {
            "refCode": g["ref_code"],
            "name": name_map.get(g["ref_code"], g["ref_code"]),
            "friendCount": g["friend_count"],
            "clickCount": click_map.get(g["ref_code"], 0),
            "latestAt": g["latest_at"].isoformat() if g["latest_at"] else None,
        }
        for g in grouped
    ]
    routes.sort(key=lambda r: r["friendCount"], reverse=True)

    return ok({
        "routes": routes,
        "totalFriends": total,
        "friendsWithRef": with_ref,
        "friendsWithoutRef": total - with_ref,
    })


@api_view(["GET"])
def analytics_ref_detail(request, ref_code):
    """特定リファラルから流入した友だち一覧。"""
    friends = Friend.objects.filter(ref_code=ref_code).order_by("-created_at")
    name = (
        EntryRoute.objects.filter(ref_code=ref_code)
        .values_list("name", flat=True)
        .first()
        or ref_code
    )
    return ok({
        "refCode": ref_code,
        "name": name,
        "friends": [
            {
                "id": str(f.id),
                "displayName": f.display_name,
                "trackedAt": f.created_at.isoformat() if f.created_at else None,
            }
            for f in friends
        ],
    })
