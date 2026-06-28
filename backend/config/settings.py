"""
Django 設定 — LINE Harness バックエンド (DRF + JWT)

Cloudflare Workers(Hono) + D1 を置き換える DRF バックエンドの設定。
- 認証: JWT (djangorestframework-simplejwt)
- DB: SQLite (D1 と同じ SQLite 系なので移行が容易)
- CORS: Next.js 管理画面 (localhost:3001) からのアクセスを許可
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# backend/.env があれば読み込む (秘密情報・環境別設定)
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-secret-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # サードパーティ
    "rest_framework",
    "corsheaders",
    # 自作アプリ
    "accounts",
    "crm",
    # 未移管機能の移管 (ドメイン別アプリ)
    "engage",
    "marketing",
    "richmenu",
    "booking",
    "events",
    "people",
    "pools",
    "forms",
    "publicapi",
]

MIDDLEWARE = [
    # CORS は最上部に置く
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # デフォルトは認証必須。公開エンドポイントは個別に AllowAny を付与する。
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "UNAUTHENTICATED_USER": None,
}

# --- JWT ---
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --- CORS ---
# JWT は Authorization ヘッダーで送るため Cookie 資格情報は不要。
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3001,http://localhost:3000",
).split(",")
CORS_ALLOW_CREDENTIALS = False

# --- LINE 連携 ---
# Messaging API のトークン/シークレット。実際の送信・署名検証に使う。
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
# Cloudflare Workers 中継 → Django webhook を認証する共有シークレット。
# Worker と Django で同じ値を設定する。
RELAY_SHARED_SECRET = os.environ.get("RELAY_SHARED_SECRET", "dev-relay-secret-change-me")

# --- 画像ストレージ (Cloudflare R2 / S3 互換) ---
# 以下がすべて設定されていれば R2 を使用。未設定なら backend/media/ にローカル保存。
R2_BUCKET = os.environ.get("R2_BUCKET", "")
R2_ENDPOINT = os.environ.get("R2_ENDPOINT", "")  # https://<account_id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
# 公開URL (R2 public bucket / 独自ドメイン)。設定時は画像配信をそこへリダイレクト。
R2_PUBLIC_BASE_URL = os.environ.get("R2_PUBLIC_BASE_URL", "")
