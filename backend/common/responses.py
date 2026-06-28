"""
レスポンス共通ヘルパー。

Next.js 管理画面は以下の形式 (ApiResponse<T>) を期待する:
  成功: { "success": true, "data": <T> }
  失敗: { "success": false, "error": "...", "details": {...} }

一覧は PaginatedResponse:
  { "items": [...], "total": N, "page": N, "limit": N, "hasNextPage": bool }
"""
from rest_framework.response import Response


def ok(data=None, status=200, **extra):
    """成功レスポンス。extra で access/refresh など追加フィールドを混ぜられる。"""
    payload = {"success": True, "data": data}
    payload.update(extra)
    return Response(payload, status=status)


def err(message, status=400, details=None):
    """失敗レスポンス。"""
    payload = {"success": False, "error": message}
    if details is not None:
        payload["details"] = details
    return Response(payload, status=status)


def paginate(request, queryset, serializer_class, default_limit=50, context=None):
    """
    offset / limit ベースのページネーション。
    フロントは ?offset= & ?limit= を送り、PaginatedResponse 形式を期待する。
    """
    try:
        offset = int(request.query_params.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0
    try:
        limit = int(request.query_params.get("limit", default_limit))
    except (TypeError, ValueError):
        limit = default_limit
    if limit <= 0:
        limit = default_limit
    if offset < 0:
        offset = 0

    total = queryset.count()
    items = serializer_class(
        queryset[offset:offset + limit], many=True, context=context
    ).data
    page = (offset // limit) + 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "hasNextPage": offset + limit < total,
    }
