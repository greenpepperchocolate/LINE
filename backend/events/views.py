from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view

from common.responses import err, ok
from crm.models import Friend

from .models import Event, EventBooking, EventSlot
from .serializers import (
    EventBookingSerializer,
    EventListSerializer,
    EventSerializer,
    EventSlotSerializer,
)

# 認証はグローバル設定 (IsAuthenticated) により全て JWT 必須。
# フロントは ?account_id= を送るが、MVP では絞り込みに使うのみ。


# ----------------------------------------------------------------------------
# Events
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def events_list(request):
    if request.method == "GET":
        qs = Event.objects.all().prefetch_related("slots", "bookings")
        account_id = request.query_params.get("account_id")
        if account_id:
            qs = qs.filter(line_account_id=account_id)
        return ok({"items": EventListSerializer(qs, many=True).data})

    serializer = EventSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    event = serializer.save()
    return ok(EventSerializer(event).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def event_detail(request, id):
    event = get_object_or_404(Event, id=id)

    if request.method == "GET":
        return ok(EventSerializer(event).data)

    if request.method == "DELETE":
        event.delete()
        return ok(None)

    serializer = EventSerializer(event, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(EventSerializer(event).data)


# ----------------------------------------------------------------------------
# Slots
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def slots_list(request, id):
    event = get_object_or_404(Event, id=id)

    if request.method == "GET":
        qs = event.slots.all().prefetch_related("bookings")
        return ok({"items": EventSlotSerializer(qs, many=True).data})

    # POST: { slots: [{ starts_at, ends_at, capacity, is_active?, sort_order? }] }
    slots_payload = request.data.get("slots", [])
    if not isinstance(slots_payload, list):
        return err("slots は配列で指定してください", status=400)

    created = []
    for entry in slots_payload:
        slot = EventSlot.objects.create(
            event=event,
            starts_at=entry.get("starts_at"),
            ends_at=entry.get("ends_at"),
            capacity=entry.get("capacity"),
            is_active=entry.get("is_active", 1),
            sort_order=entry.get("sort_order", 0),
        )
        created.append(slot)
    return ok({"items": EventSlotSerializer(created, many=True).data}, status=201)


@api_view(["PUT", "DELETE"])
def slot_detail(request, id, slot_id):
    slot = get_object_or_404(EventSlot, id=slot_id, event_id=id)

    if request.method == "DELETE":
        slot.delete()
        return ok(None)

    serializer = EventSlotSerializer(slot, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(EventSlotSerializer(slot).data)


# ----------------------------------------------------------------------------
# Bookings
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def bookings_list(request, id):
    event = get_object_or_404(Event, id=id)

    if request.method == "GET":
        qs = event.bookings.select_related("slot", "friend")
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        slot_id = request.query_params.get("slot_id")
        if slot_id:
            qs = qs.filter(slot_id=slot_id)
        return ok({"items": EventBookingSerializer(qs, many=True).data})

    # POST: 管理画面からの予約登録 (slot_id / friend_id 必須)。
    slot_id = request.data.get("slot_id")
    friend_id = request.data.get("friend_id")
    if not slot_id or not friend_id:
        return err("slot_id と friend_id は必須です", status=400)
    slot = get_object_or_404(EventSlot, id=slot_id, event=event)
    friend = get_object_or_404(Friend, id=friend_id)
    booking = EventBooking.objects.create(
        event=event,
        slot=slot,
        friend=friend,
        line_account_id=request.data.get("line_account_id"),
        status=request.data.get("status", "pending"),
        customer_note=request.data.get("customer_note"),
        internal_note=request.data.get("internal_note"),
    )
    return ok(EventBookingSerializer(booking).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def booking_detail(request, id, booking_id):
    booking = get_object_or_404(
        EventBooking.objects.select_related("slot", "friend"),
        id=booking_id, event_id=id,
    )

    if request.method == "GET":
        return ok(EventBookingSerializer(booking).data)

    if request.method == "DELETE":
        booking.delete()
        return ok(None)

    # PUT: { internal_note?, status?: 'attended' | 'no_show' }
    if "internal_note" in request.data:
        booking.internal_note = request.data["internal_note"]
    if "status" in request.data:
        booking.status = request.data["status"]
    booking.save()
    return ok(EventBookingSerializer(booking).data)


@api_view(["POST"])
def booking_decide(request, id, booking_id):
    """承認 / 却下 (status 更新スタブ)。body: { action: 'confirm'|'reject', reason? }"""
    booking = get_object_or_404(
        EventBooking.objects.select_related("slot", "friend"),
        id=booking_id, event_id=id,
    )
    action = request.data.get("action")
    if action == "confirm":
        booking.status = "confirmed"
    elif action == "reject":
        booking.status = "rejected"
    else:
        return err("action は confirm / reject のいずれかです", status=400)
    booking.decided_at = timezone.now()
    booking.save(update_fields=["status", "decided_at"])
    return ok(EventBookingSerializer(booking).data)


@api_view(["POST"])
def booking_cancel(request, id, booking_id):
    """管理者によるキャンセル (status 更新スタブ)。"""
    booking = get_object_or_404(EventBooking, id=booking_id, event_id=id)
    booking.status = "cancelled"
    booking.cancelled_at = timezone.now()
    booking.cancelled_by = "admin"
    booking.save(update_fields=["status", "cancelled_at", "cancelled_by"])
    return ok({"ok": True})


# ----------------------------------------------------------------------------
# Notifications
# ----------------------------------------------------------------------------
@api_view(["GET"])
def notifications_pending(request):
    """承認待ち予約の件数 (バッジ表示用)。"""
    qs = EventBooking.objects.filter(status="pending")
    account_id = request.query_params.get("account_id")
    if account_id:
        qs = qs.filter(line_account_id=account_id)
    return ok({"count": qs.count()})
