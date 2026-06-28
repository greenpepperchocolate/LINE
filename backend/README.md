# LINE Harness — Django REST Framework バックエンド

Cloudflare Workers(Hono) + D1 を置き換える **Django REST Framework (DRF)** バックエンド。
管理画面 (Next.js / `apps/web`) のバックエンドとして動作する。

## 仕様 (MVP)

| 項目 | 内容 |
|------|------|
| フレームワーク | Django + Django REST Framework |
| 認証 | JWT (`djangorestframework-simplejwt`) — email + password でログイン |
| DB | SQLite (`db.sqlite3`) |
| CORS | `django-cors-headers`（既定で `localhost:3001` を許可） |
| レスポンス形式 | `{ success, data }`（フロントの `ApiResponse<T>` と互換、camelCase） |

旧バックエンドの API キー方式（Worker の `API_KEY` 照合）から、
**ユーザーアカウント + JWT** によるログイン認証に置き換えた。

## ディレクトリ構成

```
backend/
  config/        # Django プロジェクト設定 (settings, urls, wsgi)
  common/        # レスポンス共通ヘルパー (ApiResponse 互換ラッパー)
  accounts/      # カスタムユーザー + 認証 (register / login / me / refresh)
  crm/           # 友だち・タグ・配信 (friends / tags / broadcasts)
  requirements.txt
  manage.py
```

## セットアップ（ローカル）

```bash
cd backend

# 1. 仮想環境
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 2. 依存インストール
pip install -r requirements.txt

# 3. DB マイグレーション
python manage.py migrate

# 4. (任意) Django 管理用スーパーユーザー
python manage.py createsuperuser

# 5. 起動 (http://localhost:8000)
python manage.py runserver 8000
```

管理画面 (`apps/web`) 側の `.env.local` に
`NEXT_PUBLIC_API_URL=http://localhost:8000` を設定する。

## API エンドポイント

### 認証 (`/api/auth/`)

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| POST | `/api/auth/register` | ユーザー登録（最初の登録者は owner） | 不要 |
| POST | `/api/auth/login` | ログイン → JWT 発行 | 不要 |
| POST | `/api/auth/refresh` | access トークン再発行 | 不要(refresh必須) |
| GET  | `/api/auth/me` | ログイン中ユーザー情報 | 必要 |

ログイン応答例:
```json
{
  "success": true,
  "data": { "id": "...", "email": "a@b.com", "name": "管理者", "role": "owner" },
  "access": "<JWT access>",
  "refresh": "<JWT refresh>"
}
```

### CRM (`/api/`) — すべて JWT 必須

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/friends` | 友だち一覧（ページネーション） |
| GET | `/api/friends/count` | 友だち数 |
| GET | `/api/friends/:id` | 友だち詳細 |
| POST | `/api/friends/:id/tags` | タグ付与 (`{tagId}`) |
| DELETE | `/api/friends/:id/tags/:tagId` | タグ削除 |
| GET | `/api/tags` | タグ一覧 |
| POST | `/api/tags` | タグ作成 (`{name, color}`) |
| DELETE | `/api/tags/:id` | タグ削除 |
| GET | `/api/broadcasts` | 配信一覧 |
| POST | `/api/broadcasts` | 配信作成 |
| GET/PUT/DELETE | `/api/broadcasts/:id` | 配信 取得/更新/削除 |

## 認証の流れ（フロント連携）

1. 管理画面のログイン画面で email/password を送信 → `/api/auth/login`
2. 応答の `access` / `refresh` を localStorage に保存
3. 以降の API 呼び出しは `Authorization: Bearer <access>` ヘッダーを付与
4. `401` が返ったらトークン破棄してログイン画面へ

### 追加機能 (`/api/`) — すべて JWT 必須

| メソッド | パス | 説明 |
|---------|------|------|
| GET/POST | `/api/templates` | テンプレート一覧/作成 |
| GET/PUT/DELETE | `/api/templates/:id` | テンプレート 取得/更新/削除 |
| GET/POST | `/api/auto-replies` | 自動応答 一覧/作成 |
| GET/PUT/DELETE | `/api/auto-replies/:id` | 自動応答 取得/更新/削除 |
| GET/POST | `/api/scenarios` | シナリオ 一覧/作成 |
| GET/PUT/DELETE | `/api/scenarios/:id` | シナリオ 取得(steps付)/更新/削除 |
| POST | `/api/scenarios/:id/steps` | ステップ追加 |
| PUT/DELETE | `/api/scenarios/:id/steps/:stepId` | ステップ 更新/削除 |
| POST | `/api/scenarios/:id/steps/reorder` | ステップ並び替え |
| GET/POST | `/api/chats` | チャット 一覧/作成 |
| GET/PUT | `/api/chats/:id` | チャット 取得(messages付)/更新 |
| POST | `/api/chats/:id/send` | メッセージ送信 (LINE プッシュ) |

## LINE Webhook 取り込み (ハイブリッド構成)

LINE → **Cloudflare Workers 中継** (`apps/webhook-relay`) → **Django** の流れ。

```
LINE ──▶ Worker(中継): 署名検証 → 即 200 OK → waitUntil で非同期転送
                                                  │ X-Relay-Secret
                                                  ▼
         Django: POST /api/line/webhook (共有シークレット認証, JWT 不要)
           - follow   → 友だち登録 + friend_add シナリオ購読
           - unfollow → is_following=False
           - message  → 受信ログ + チャット起票 + キーワード自動応答
```

| メソッド | パス | 認証 | 説明 |
|---------|------|------|------|
| POST | `/api/line/webhook` | `X-Relay-Secret` 共有シークレット | 中継 Worker からの LINE イベント取り込み |

必要な環境変数 (`backend/.env`): `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`,
`RELAY_SHARED_SECRET`（中継 Worker と同じ値）。詳細は `.env.example` 参照。

## 今後の拡張

リッチメニュー、リマインダ、CV計測、スコアリング、Webhook(送受信)、予約、
シナリオの遅延ステップ自動配信(cron) などは未移植。旧 Worker のルートを
参照して順次 `crm` に追加していく。
