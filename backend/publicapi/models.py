import uuid

from django.db import models

# 公開導線 (友だち追加 OAuth / トラッキングリンク) 用モデル。
# クリック記録のみ。友だち本体は crm.Friend を upsert する。


class LinkClick(models.Model):
    """
    /r/<ref_code> へのアクセス (クリック) を記録する。
    LINE Login へリダイレクトする前に 1 行 INSERT する。
    ref_code は marketing.EntryRoute.ref_code 等に対応する任意の文字列。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ref_code = models.CharField(max_length=255, db_index=True)
    user_agent = models.TextField(null=True, blank=True)
    ip_address = models.CharField(max_length=64, null=True, blank=True)
    referer = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "link_clicks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ref_code} @ {self.created_at:%Y-%m-%d %H:%M}"
