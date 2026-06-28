"""
LINE 連携設定の解決ヘルパー。

優先順位:
  1. 「LINEアカウント管理」(/accounts) で登録した有効アカウント (LineAccount)
  2. 環境変数 (settings.py)

チャネルの資格情報は /accounts に一本化した。relay 共有シークレットのみ
LineSettings (= /accounts 画面内の「中継Worker設定」) で全体管理する。
"""
from django.conf import settings


def _row():
    from .models import LineSettings
    return LineSettings.load()


def _first_account():
    from .models import LineAccount
    return LineAccount.objects.filter(is_active=True).first()


def get_line_access_token():
    acc = _first_account()
    if acc and acc.channel_access_token:
        return acc.channel_access_token
    return settings.LINE_CHANNEL_ACCESS_TOKEN


def get_line_channel_secret():
    acc = _first_account()
    if acc and acc.channel_secret:
        return acc.channel_secret
    return settings.LINE_CHANNEL_SECRET


def get_relay_secret():
    return _row().relay_shared_secret or settings.RELAY_SHARED_SECRET
