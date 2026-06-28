from django.contrib.auth import authenticate, get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from common.responses import err, ok

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


def _tokens_for(user):
    """ユーザーに対する access / refresh トークンを生成。"""
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """
    ユーザー登録。
    最初に登録したユーザーは自動的に owner 権限になる。
    """
    data = request.data.copy()
    if User.objects.count() == 0:
        data["role"] = "owner"
    else:
        # 2人目以降は明示が無ければ staff
        data.setdefault("role", "staff")

    serializer = RegisterSerializer(data=data)
    if not serializer.is_valid():
        return err("入力内容に誤りがあります", status=400, details=serializer.errors)

    user = serializer.save()
    return ok(UserSerializer(user).data, status=201, **_tokens_for(user))


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """email + password でログインし JWT を発行。"""
    email = request.data.get("email")
    password = request.data.get("password")
    if not email or not password:
        return err("メールアドレスとパスワードを入力してください", status=400)

    user = authenticate(request, username=email, password=password)
    if user is None:
        return err("メールアドレスまたはパスワードが正しくありません", status=401)

    return ok(UserSerializer(user).data, **_tokens_for(user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """現在ログイン中のユーザー情報を返す (セッション検証用)。"""
    return ok(UserSerializer(request.user).data)
