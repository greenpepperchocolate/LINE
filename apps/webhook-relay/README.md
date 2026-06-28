# LINE Webhook 中継 Worker (`line-webhook-relay`)

LINE からの Webhook を **Cloudflare のエッジで爆速受信**し、署名検証後に
**即座に 200 OK** を返しつつ、裏側で **Django API へ非同期転送**する薄い中継 Worker。

```
LINE ──webhook──▶ Cloudflare Worker (この中継)
                      │  1. X-Line-Signature 検証 (HMAC-SHA256)
                      │  2. LINE へ即 200 OK
                      └─ 3. waitUntil で Django /api/line/webhook へ非同期 POST
                            (X-Relay-Secret 共有シークレット付き)
                                     │
                                     ▼
                            Django (本処理: 友だち登録/自動応答/チャット)
```

## なぜこの構成か

- LINE は Webhook に **~1 秒以内**の応答を要求する。重い本処理を待つとタイムアウトする。
- Cloudflare Workers は**コールドスタートが速い**ため、受信と即時応答に最適。
- 本処理 (DB 書き込み・LINE API 呼び出し) は Django に寄せ、Worker は中継に専念。

## ローカル開発

```bash
cd apps/webhook-relay
cp .dev.vars.example .dev.vars   # LINE_CHANNEL_SECRET / RELAY_SHARED_SECRET を設定
npx wrangler dev --port 8787     # http://localhost:8787/webhook
```

`DJANGO_WEBHOOK_URL` は `wrangler.toml` の `[vars]` で設定 (既定: `http://localhost:8000/api/line/webhook`)。

## 本番デプロイ

```bash
npx wrangler secret put LINE_CHANNEL_SECRET
npx wrangler secret put RELAY_SHARED_SECRET
# wrangler.toml の DJANGO_WEBHOOK_URL を本番 Django の URL に変更
npx wrangler deploy
```

デプロイ後の `https://line-webhook-relay.<account>.workers.dev/webhook` を
**LINE Developers Console の Webhook URL** に設定する。

## 環境変数

| 名前 | 種別 | 説明 |
|------|------|------|
| `LINE_CHANNEL_SECRET` | secret | 署名検証用。LINE Messaging API チャネルシークレット |
| `RELAY_SHARED_SECRET` | secret | Django の `RELAY_SHARED_SECRET` と同じ値 |
| `DJANGO_WEBHOOK_URL` | var | 転送先 Django webhook URL |
