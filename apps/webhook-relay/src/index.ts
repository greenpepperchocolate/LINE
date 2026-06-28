/**
 * LINE Webhook 中継 Worker (純粋な中継)
 *
 * 役割:
 *   1. LINE からの Webhook を爆速で受け取る (Cloudflare のエッジ起動)
 *   2. LINE 側へ即座に 200 OK を返す (LINE は ~1 秒以内の応答を要求)
 *   3. 裏側で Django API サーバーへイベントを非同期転送 (waitUntil)
 *
 * 署名検証 (X-Line-Signature) は Django 側で行う。これにより
 * LINE_CHANNEL_SECRET を「管理画面 (DB)」で一元管理でき、Worker に
 * チャネルシークレットを持たせずに済む。Worker は X-Line-Signature を
 * そのまま転送し、Django が DB のシークレットで検証する。
 *
 * Django 側 (/api/line/webhook) は共有シークレット (X-Relay-Secret) で
 * この Worker からのリクエストのみを受け付ける。
 */

export interface Env {
  /** 転送先 Django webhook URL (例: https://api.example.com/api/line/webhook) */
  DJANGO_WEBHOOK_URL: string;
  /** Django と共有する転送認証シークレット (Django の RELAY_SHARED_SECRET と同値) */
  RELAY_SHARED_SECRET: string;
}

const json200 = () =>
  new Response(JSON.stringify({ status: 'ok' }), {
    status: 200,
    headers: { 'content-type': 'application/json' },
  });

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // ヘルスチェック
    if (request.method === 'GET') {
      return new Response('LINE webhook relay: OK', { status: 200 });
    }

    if (request.method !== 'POST' || url.pathname !== '/webhook') {
      return new Response('Not found', { status: 404 });
    }

    const rawBody = await request.text();
    const signature = request.headers.get('X-Line-Signature') ?? '';

    // ★ Django へ非同期転送 (応答をブロックしない)。署名は転送し Django が検証。
    ctx.waitUntil(
      fetch(env.DJANGO_WEBHOOK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Relay-Secret': env.RELAY_SHARED_SECRET,
          'X-Line-Signature': signature,
        },
        body: rawBody,
      }).catch((err) => console.error('[relay] forward to Django failed:', err)),
    );

    // ★ LINE には即 200 OK
    return json200();
  },
};
