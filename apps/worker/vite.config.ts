import { cloudflare } from "@cloudflare/vite-plugin";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// React + Tailwind は salon-booking ページ (?page=salon-book) でのみ使う。
// main.ts から動的 import するので React チャンクは別ファイルに分離され、
// 既存の form / Google Calendar booking 利用者には load されない。
export default defineConfig({
  plugins: [cloudflare(), react(), tailwindcss()],
  // Vite 開発サーバー内蔵の CORS を無効化する。有効のままだと OPTIONS
  // プリフライトを Vite が握りつぶし、credentials 無しの CORS ヘッダーで
  // 204 応答してしまうため、credentials: 'include' を使う管理画面ログイン
  // (localhost:3001 → :5173) がプリフライトでブロックされる。無効化して
  // Worker (Hono cors) に CORS 処理を一任する。
  server: { cors: false },
});
