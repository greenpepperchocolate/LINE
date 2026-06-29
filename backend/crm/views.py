from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view

from common.responses import err, ok, paginate

from . import line_client
from .models import (
    AutoReply,
    Broadcast,
    Chat,
    Friend,
    FriendTag,
    LineAccount,
    LineSettings,
    Message,
    Scenario,
    ScenarioStep,
    Tag,
    Template,
)
from .serializers import (
    AutoReplySerializer,
    BroadcastSerializer,
    ChatDetailSerializer,
    ChatSerializer,
    FriendSerializer,
    LineAccountListSerializer,
    LineAccountSerializer,
    LineSettingsSerializer,
    ScenarioDetailSerializer,
    ScenarioSerializer,
    ScenarioStepSerializer,
    TagSerializer,
    TemplateSerializer,
)

# 認証はグローバル設定 (IsAuthenticated) により全て JWT 必須。


# ----------------------------------------------------------------------------
# Friends
# ----------------------------------------------------------------------------
@api_view(["GET"])
def friends_list(request):
    qs = Friend.objects.all().prefetch_related("tags")

    tag_id = request.query_params.get("tagId")
    if tag_id:
        qs = qs.filter(tags__id=tag_id)

    search = request.query_params.get("search")
    if search:
        qs = qs.filter(display_name__icontains=search)

    sort = request.query_params.get("sort")
    qs = qs.order_by("created_at") if sort == "oldest" else qs.order_by("-created_at")

    return ok(paginate(request, qs, FriendSerializer))


@api_view(["GET"])
def friends_count(request):
    return ok({"count": Friend.objects.count()})


@api_view(["GET"])
def friend_detail(request, friend_id):
    friend = get_object_or_404(Friend.objects.prefetch_related("tags"), id=friend_id)
    return ok(FriendSerializer(friend).data)


@api_view(["POST"])
def friend_add_tag(request, friend_id):
    friend = get_object_or_404(Friend, id=friend_id)
    tag_id = request.data.get("tagId")
    if not tag_id:
        return err("tagId は必須です", status=400)
    tag = get_object_or_404(Tag, id=tag_id)
    FriendTag.objects.get_or_create(friend=friend, tag=tag)
    return ok(None)


@api_view(["DELETE"])
def friend_remove_tag(request, friend_id, tag_id):
    FriendTag.objects.filter(friend_id=friend_id, tag_id=tag_id).delete()
    return ok(None)


# ----------------------------------------------------------------------------
# Tags
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def tags_list(request):
    if request.method == "GET":
        qs = Tag.objects.all()
        return ok(TagSerializer(qs, many=True).data)

    serializer = TagSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    tag = serializer.save()
    return ok(TagSerializer(tag).data, status=201)


@api_view(["DELETE"])
def tag_detail(request, tag_id):
    Tag.objects.filter(id=tag_id).delete()
    return ok(None)


# ----------------------------------------------------------------------------
# Broadcasts
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def broadcasts_list(request):
    if request.method == "GET":
        qs = Broadcast.objects.all()
        return ok(BroadcastSerializer(qs, many=True).data)

    serializer = BroadcastSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    broadcast = serializer.save()
    return ok(BroadcastSerializer(broadcast).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def broadcast_detail(request, broadcast_id):
    broadcast = get_object_or_404(Broadcast, id=broadcast_id)

    if request.method == "GET":
        return ok(BroadcastSerializer(broadcast).data)

    if request.method == "DELETE":
        broadcast.delete()
        return ok(None)

    # PUT (partial update)
    serializer = BroadcastSerializer(broadcast, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(BroadcastSerializer(broadcast).data)


# ----------------------------------------------------------------------------
# Templates
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def templates_list(request):
    if request.method == "GET":
        qs = Template.objects.all()
        category = request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return ok(TemplateSerializer(qs, many=True).data)

    serializer = TemplateSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    tpl = serializer.save()
    return ok(TemplateSerializer(tpl).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def template_detail(request, template_id):
    tpl = get_object_or_404(Template, id=template_id)
    if request.method == "GET":
        return ok(TemplateSerializer(tpl).data)
    if request.method == "DELETE":
        tpl.delete()
        return ok(None)
    serializer = TemplateSerializer(tpl, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(TemplateSerializer(tpl).data)


# ----------------------------------------------------------------------------
# Auto-replies
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def auto_replies_list(request):
    if request.method == "GET":
        qs = AutoReply.objects.all()
        account_id = request.query_params.get("accountId")
        if account_id:
            qs = qs.filter(line_account_id=account_id)
        return ok(AutoReplySerializer(qs, many=True).data)

    serializer = AutoReplySerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    ar = serializer.save()
    return ok(AutoReplySerializer(ar).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def auto_reply_detail(request, auto_reply_id):
    ar = get_object_or_404(AutoReply, id=auto_reply_id)
    if request.method == "GET":
        return ok(AutoReplySerializer(ar).data)
    if request.method == "DELETE":
        ar.delete()
        return ok(None)
    serializer = AutoReplySerializer(ar, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(AutoReplySerializer(ar).data)


# ----------------------------------------------------------------------------
# Scenarios (+ steps)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def scenarios_list(request):
    if request.method == "GET":
        qs = Scenario.objects.all()
        account_id = request.query_params.get("lineAccountId")
        if account_id:
            qs = qs.filter(line_account_id=account_id)
        return ok(ScenarioSerializer(qs, many=True).data)

    serializer = ScenarioSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    scenario = serializer.save()
    return ok(ScenarioSerializer(scenario).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def scenario_detail(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if request.method == "GET":
        return ok(ScenarioDetailSerializer(scenario).data)
    if request.method == "DELETE":
        scenario.delete()
        return ok(None)
    serializer = ScenarioSerializer(scenario, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(ScenarioSerializer(scenario).data)


@api_view(["POST"])
def scenario_steps(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    serializer = ScenarioStepSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    step = serializer.save(scenario=scenario)
    return ok(ScenarioStepSerializer(step).data, status=201)


@api_view(["PUT", "DELETE"])
def scenario_step_detail(request, scenario_id, step_id):
    step = get_object_or_404(ScenarioStep, id=step_id, scenario_id=scenario_id)
    if request.method == "DELETE":
        step.delete()
        return ok(None)
    serializer = ScenarioStepSerializer(step, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(ScenarioStepSerializer(step).data)


@api_view(["POST"])
def scenario_steps_reorder(request, scenario_id):
    """orders: [{stepId, stepOrder}] で並び替え。"""
    orders = request.data.get("orders", [])
    for entry in orders:
        ScenarioStep.objects.filter(
            id=entry.get("stepId"), scenario_id=scenario_id
        ).update(step_order=entry.get("stepOrder"))
    return ok(None)


# ----------------------------------------------------------------------------
# Chats (+ messages)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def chats_list(request):
    if request.method == "GET":
        qs = Chat.objects.select_related("friend").prefetch_related("friend__messages")

        # ステータス絞り込み (未読 / 対応中 / 解決済)。'all' は絞らない。
        status = request.query_params.get("status")
        if status and status != "all":
            qs = qs.filter(status=status)

        # 担当オペレーター絞り込み
        operator_id = request.query_params.get("operatorId")
        if operator_id:
            qs = qs.filter(operator_id=operator_id)

        chats = list(qs)

        # 未対応のみ: 最新メッセージが incoming (= まだ返信していない) のチャット
        unanswered = request.query_params.get("unansweredOnly")
        if unanswered in ("1", "true", "True"):
            def _is_unanswered(c):
                last = c.friend.messages.all().order_by("-created_at").first()
                return bool(last and last.direction == "incoming")
            chats = [c for c in chats if _is_unanswered(c)]

        # 最新メッセージ順 (新しい順)
        chats.sort(key=lambda c: c.last_message_at or c.created_at, reverse=True)
        return ok(ChatSerializer(chats, many=True).data)

    friend_id = request.data.get("friendId")
    friend = get_object_or_404(Friend, id=friend_id)
    chat, _ = Chat.objects.get_or_create(friend=friend)
    operator_id = request.data.get("operatorId")
    if operator_id:
        chat.operator_id = operator_id
        chat.save(update_fields=["operator_id", "updated_at"])
    return ok(ChatSerializer(chat).data, status=201)


@api_view(["GET", "PUT"])
def chat_detail(request, chat_id):
    # フロントは friend_id をチャット識別子として渡す。無ければ自動作成。
    friend = get_object_or_404(Friend, id=chat_id)
    chat, _ = Chat.objects.get_or_create(friend=friend)
    chat = Chat.objects.select_related("friend").get(pk=chat.pk)
    if request.method == "GET":
        return ok(ChatDetailSerializer(chat).data)
    # PUT: status / operatorId / notes
    if "status" in request.data:
        chat.status = request.data["status"]
    if "operatorId" in request.data:
        chat.operator_id = request.data["operatorId"]
    if "notes" in request.data:
        chat.notes = request.data["notes"]
    chat.save()
    return ok(ChatSerializer(chat).data)


@api_view(["POST"])
def chat_loading(request, chat_id):
    """LINE のローディング表示を開始。# TODO: POST /v2/bot/chat/loading/start 連携"""
    get_object_or_404(Friend, id=chat_id)
    return ok(None)


@api_view(["POST"])
def chat_send(request, chat_id):
    """オペレーターから友だちへメッセージ送信 (LINE プッシュ)。chat_id = friend_id。"""
    friend = get_object_or_404(Friend, id=chat_id)
    chat, _ = Chat.objects.get_or_create(friend=friend)
    content = request.data.get("content", "")
    message_type = request.data.get("messageType", "text")
    if not content:
        return err("content は必須です", status=400)

    sent, detail = line_client.push_text(chat.friend.line_user_id, content)
    Message.objects.create(
        friend=chat.friend, direction="outgoing",
        message_type=message_type, content=content, delivery_type="push",
    )
    now = timezone.now()
    chat.last_message_at = now
    chat.status = "in_progress"
    chat.save(update_fields=["last_message_at", "status", "updated_at"])
    return ok({"sent": sent, "detail": detail})


# ----------------------------------------------------------------------------
# LINE Settings (管理画面から登録 / owner・admin のみ)
# ----------------------------------------------------------------------------
@api_view(["GET", "PUT"])
def line_settings(request):
    # owner / admin のみアクセス可
    if getattr(request.user, "role", None) not in ("owner", "admin"):
        return err("権限がありません (owner / admin のみ)", status=403)

    obj = LineSettings.load()

    if request.method == "GET":
        return ok(LineSettingsSerializer(obj).data)

    # PUT: 送られたフィールドのみ更新 (空文字も明示更新として扱う)
    serializer = LineSettingsSerializer(obj, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(LineSettingsSerializer(obj).data)


# ----------------------------------------------------------------------------
# LINE Accounts (マルチアカウント / 「LINEアカウント管理」画面から登録)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def line_accounts_list(request):
    if request.method == "GET":
        qs = LineAccount.objects.all()
        return ok(LineAccountListSerializer(qs, many=True).data)

    serializer = LineAccountSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    account = serializer.save()
    return ok(LineAccountSerializer(account).data, status=201)


@api_view(["PATCH"])
def line_accounts_order(request):
    """並び替え: ordered=[{id, displayOrder}]。"""
    for entry in request.data.get("ordered", []):
        LineAccount.objects.filter(id=entry.get("id")).update(
            display_order=entry.get("displayOrder", 0)
        )
    return ok(None)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def line_account_detail(request, account_id):
    account = get_object_or_404(LineAccount, id=account_id)

    if request.method == "GET":
        return ok(LineAccountSerializer(account).data)
    if request.method == "DELETE":
        account.delete()
        return ok(None)

    # PUT / PATCH はどちらも部分更新として扱う
    serializer = LineAccountSerializer(account, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(LineAccountSerializer(account).data)


# ----------------------------------------------------------------------------
# Friends 拡張 (rich-menu / score)
# ----------------------------------------------------------------------------
@api_view(["GET"])
def friend_rich_menu(request, friend_id):
    get_object_or_404(Friend, id=friend_id)
    # 個別リッチメニューは未割当 (MVP)
    return ok({"id": None, "name": None, "isDefault": False})


@api_view(["GET"])
def friend_score(request, friend_id):
    friend = get_object_or_404(Friend, id=friend_id)
    return ok({"totalScore": friend.score, "history": []})


# ----------------------------------------------------------------------------
# Broadcasts 拡張 (send / insight / preview-count / progress 等)
# ----------------------------------------------------------------------------
def _broadcast_targets(broadcast):
    qs = Friend.objects.filter(is_following=True)
    if broadcast.target_type == "tag" and broadcast.target_tag_id:
        qs = qs.filter(tags__id=broadcast.target_tag_id)
    return qs


@api_view(["POST"])
def broadcast_send(request, broadcast_id):
    """配信実行: 対象友だちへ LINE プッシュ送信し、ステータス更新。"""
    broadcast = get_object_or_404(Broadcast, id=broadcast_id)
    targets = list(_broadcast_targets(broadcast).distinct())
    success = 0
    for friend in targets:
        sent, _ = line_client.push_text(friend.line_user_id, broadcast.message_content)
        if sent:
            success += 1
        Message.objects.create(
            friend=friend, direction="outgoing",
            message_type=broadcast.message_type, content=broadcast.message_content,
            delivery_type="push",
        )
    broadcast.status = "sent"
    broadcast.sent_at = timezone.now()
    broadcast.total_count = len(targets)
    broadcast.success_count = success
    broadcast.save()
    return ok(BroadcastSerializer(broadcast).data)


@api_view(["POST"])
def broadcast_send_segment(request, broadcast_id):
    # セグメント配信は通常配信と同等に扱う (MVP)
    return broadcast_send(request, broadcast_id)


@api_view(["GET"])
def broadcast_insight(request, broadcast_id):
    get_object_or_404(Broadcast, id=broadcast_id)
    return ok(None)  # 保存済みインサイトなし


@api_view(["POST"])
def broadcast_fetch_insight(request, broadcast_id):
    broadcast = get_object_or_404(Broadcast, id=broadcast_id)
    # LINE インサイト API は未連携。ゼロ値を返す。 # TODO: LINE Insight 連携
    return ok({
        "broadcastId": str(broadcast.id),
        "delivered": broadcast.success_count,
        "uniqueImpression": None, "uniqueClick": None, "uniqueMediaPlayed": None,
        "openRate": None, "clickRate": None,
        "status": broadcast.status, "fetchedAt": timezone.now().isoformat(),
    })


@api_view(["POST"])
def broadcast_test_send(request, broadcast_id):
    get_object_or_404(Broadcast, id=broadcast_id)
    return ok(None, sent=0, failed=0)  # テスト送信先未設定 (MVP)


@api_view(["GET"])
def broadcast_progress(request, broadcast_id):
    broadcast = get_object_or_404(Broadcast, id=broadcast_id)
    return ok({
        "status": broadcast.status,
        "totalCount": broadcast.total_count,
        "successCount": broadcast.success_count,
        "batchOffset": 0,
    })


@api_view(["GET"])
def broadcast_preview_count(request, broadcast_id):
    broadcast = get_object_or_404(Broadcast, id=broadcast_id)
    count = _broadcast_targets(broadcast).distinct().count()
    return ok({"count": count})


@api_view(["GET"])
def broadcast_per_account_stats(request, broadcast_id):
    get_object_or_404(Broadcast, id=broadcast_id)
    return ok([])  # マルチアカウント統計は MVP 未対応


@api_view(["POST"])
def broadcast_dedup_preview(request):
    return ok({
        "totalSelected": 0, "uniqueRecipients": 0,
        "reduction": 0, "reductionRate": 0, "perAccount": [],
    })


# ----------------------------------------------------------------------------
# Templates 拡張 (usages)
# ----------------------------------------------------------------------------
@api_view(["GET"])
def template_usages(request, template_id):
    tpl = get_object_or_404(Template, id=template_id)
    auto_replies = [
        {"id": str(ar.id), "keyword": ar.keyword, "lineAccountId": ar.line_account_id}
        for ar in tpl.auto_replies.all()
    ]
    scenario_steps = [
        {
            "scenarioId": str(s.scenario_id),
            "scenarioName": s.scenario.name,
            "stepId": str(s.id),
            "stepOrder": s.step_order,
        }
        for s in tpl.scenario_steps.select_related("scenario").all()
    ]
    return ok({"autoReplies": auto_replies, "scenarioSteps": scenario_steps})


# ----------------------------------------------------------------------------
# Scenarios 拡張 (preview / stats)
# ----------------------------------------------------------------------------
@api_view(["GET"])
def scenario_preview(request, scenario_id):
    from datetime import timedelta

    from django.utils.dateparse import parse_datetime

    scenario = get_object_or_404(Scenario, id=scenario_id)
    start_raw = request.query_params.get("startAt")
    start = (parse_datetime(start_raw) if start_raw else None) or timezone.now()

    steps = []
    cumulative = 0
    for s in scenario.steps.order_by("step_order"):
        # relative モード: 前ステップからの遅延を累積。他モードも近似で累積。
        cumulative += (s.delay_minutes or 0)
        if s.offset_days:
            cumulative += s.offset_days * 24 * 60
        if s.offset_minutes:
            cumulative += s.offset_minutes
        dt = start + timedelta(minutes=cumulative)
        steps.append({
            "stepOrder": s.step_order,
            "deliveryAt": dt.isoformat(),
            "deliveryAtLabel": dt.strftime("%Y-%m-%d %H:%M"),
            "messageType": s.message_type,
            "messageContent": s.message_content,
        })
    return ok({"startAt": start.isoformat(), "steps": steps})


@api_view(["GET"])
def scenario_stats(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    enrollments = scenario.enrollments.all()
    total = enrollments.count()
    active = enrollments.filter(status="active").count()
    completed = enrollments.filter(status="completed").count()
    paused = enrollments.filter(status="paused").count()

    steps = []
    for s in scenario.steps.order_by("step_order"):
        reached = enrollments.filter(current_step_order__gte=s.step_order).count()
        rate = round(reached / total * 100, 1) if total else 0
        steps.append({"stepOrder": s.step_order, "reachedCount": reached, "reachRate": rate})

    return ok({
        "enrolledTotal": total, "activeNow": active,
        "completed": completed, "paused": paused, "steps": steps,
    })


# ----------------------------------------------------------------------------
# Friends 拡張 (messages: 取得 / 送信)
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def friend_messages(request, friend_id):
    friend = get_object_or_404(Friend, id=friend_id)

    if request.method == "GET":
        msgs = friend.messages.order_by("created_at")
        return ok([
            {
                "id": str(m.id),
                "direction": m.direction,
                "messageType": m.message_type,
                "content": m.content,
                "createdAt": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs
        ])

    # POST: オペレーターから送信 (LINE プッシュ)
    content = request.data.get("content", "")
    message_type = request.data.get("messageType", "text")
    if not content:
        return err("content は必須です", status=400)
    sent, _ = line_client.push_text(friend.line_user_id, content)
    msg = Message.objects.create(
        friend=friend, direction="outgoing",
        message_type=message_type, content=content, delivery_type="push",
    )
    # チャットの最終メッセージ時刻も更新
    chat = Chat.objects.filter(friend=friend).first()
    if chat:
        chat.last_message_at = timezone.now()
        chat.status = "in_progress"
        chat.save(update_fields=["last_message_at", "status", "updated_at"])
    return ok({
        "id": str(msg.id), "direction": "outgoing",
        "messageType": message_type, "content": content,
        "createdAt": msg.created_at.isoformat(), "sent": sent,
    })
