from django.db.models import Count, Max
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from common.responses import err, ok
from crm.models import Friend

from .models import Form, FormSubmission
from .serializers import (
    FormDetailSerializer,
    FormSerializer,
    FormWriteSerializer,
    SubmissionSerializer,
)

# 認証はグローバル設定 (IsAuthenticated) により全て JWT 必須。
# ただし公開フォーム送信 (POST submissions) のみ AllowAny。


# ----------------------------------------------------------------------------
# Forms
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
def forms_list(request):
    if request.method == "GET":
        qs = Form.objects.annotate(
            submit_count=Count("submissions"),
            last_submitted_at=Max("submissions__created_at"),
        )
        return ok(FormSerializer(qs, many=True).data)

    serializer = FormWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    form = serializer.save()
    return ok(FormDetailSerializer(form).data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def form_detail(request, form_id):
    if request.method == "GET":
        form = get_object_or_404(
            Form.objects.annotate(
                submit_count=Count("submissions"),
                last_submitted_at=Max("submissions__created_at"),
            ),
            id=form_id,
        )
        return ok(FormDetailSerializer(form).data)

    form = get_object_or_404(Form, id=form_id)

    if request.method == "DELETE":
        form.delete()
        return ok(None)

    # PUT (partial update)
    serializer = FormWriteSerializer(form, data=request.data, partial=True)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)
    serializer.save()
    return ok(FormDetailSerializer(form).data)


# ----------------------------------------------------------------------------
# Submissions
# ----------------------------------------------------------------------------
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def form_submissions(request, form_id):
    """
    GET: 回答一覧 (JWT 必須 / グローバル設定)。
    POST: LIFF からの回答送信 (公開 / AllowAny)。

    注意: AllowAny はビュー全体に掛かるため、GET は明示的に認証を確認する。
    """
    if request.method == "GET":
        if not request.user or not request.user.is_authenticated:
            return err("認証が必要です", status=401)
        form = get_object_or_404(Form, id=form_id)
        qs = form.submissions.select_related("friend").all()
        return ok(SubmissionSerializer(qs, many=True).data)

    # POST (公開): body = {data: {...}, friendId?, lineUserId?}
    form = get_object_or_404(Form, id=form_id)
    data = request.data.get("data", {})
    if not isinstance(data, dict):
        return err("data はオブジェクトである必要があります", status=400)

    friend = None
    friend_id = request.data.get("friendId")
    line_user_id = request.data.get("lineUserId")
    if friend_id:
        friend = Friend.objects.filter(id=friend_id).first()
    if friend is None and line_user_id:
        friend = Friend.objects.filter(line_user_id=line_user_id).first()

    submission = FormSubmission.objects.create(form=form, friend=friend, data=data)
    return ok(SubmissionSerializer(submission).data, status=201)
