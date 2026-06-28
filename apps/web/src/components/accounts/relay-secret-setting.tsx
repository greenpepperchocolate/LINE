'use client'
import { useEffect, useState } from 'react'
import { fetchApi } from '@/lib/api'

type ApiResponse<T> = { success: true; data: T } | { success: false; error: string }

/**
 * 中継 Worker (apps/webhook-relay) との共有シークレット設定。
 * LINE のチャネル資格情報はアカウント単位 (上の一覧/フォーム) で管理するが、
 * この共有シークレットだけは全体共通なのでここで 1 箇所だけ設定する。
 */
export default function RelaySecretSetting() {
  const [secret, setSecret] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const r = await fetchApi<ApiResponse<{ relaySharedSecret: string }>>('/api/settings/line')
        if (r.success) setSecret(r.data.relaySharedSecret || '')
      } catch (e) {
        const forbidden = e instanceof Error && e.message.includes('403')
        setMsg({ type: 'err', text: forbidden ? 'owner / admin のみ閲覧できます' : '設定の取得に失敗しました' })
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMsg(null)
    try {
      const r = await fetchApi<ApiResponse<{ relaySharedSecret: string }>>('/api/settings/line', {
        method: 'PUT',
        body: JSON.stringify({ relaySharedSecret: secret }),
      })
      setMsg(r.success ? { type: 'ok', text: '保存しました' } : { type: 'err', text: '保存に失敗しました' })
    } catch (e) {
      const forbidden = e instanceof Error && e.message.includes('403')
      setMsg({ type: 'err', text: forbidden ? '保存権限がありません (owner / admin のみ)' : '保存に失敗しました' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) return null

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between text-left"
      >
        <div>
          <h3 className="text-sm font-semibold text-gray-900">中継 Worker 設定（共有シークレット）</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            LINE Webhook を中継する Cloudflare Worker と Django を認証する全体共通の鍵
          </p>
        </div>
        <span className="text-gray-400 text-xs">{open ? '閉じる ▲' : '開く ▼'}</span>
      </button>

      {open && (
        <form onSubmit={save} className="mt-4">
          <label className="block text-xs font-medium text-gray-700 mb-1">RELAY_SHARED_SECRET</label>
          <input
            type="password"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
            placeholder="中継 Worker の RELAY_SHARED_SECRET と同じ値"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
            autoComplete="off"
          />
          <p className="text-xs text-gray-500 mt-1">
            中継 Worker（apps/webhook-relay）の <code>.dev.vars</code> / secret と必ず同じ値にしてください。
          </p>
          {msg && (
            <p className={`text-xs mt-2 ${msg.type === 'ok' ? 'text-green-600' : 'text-red-600'}`}>{msg.text}</p>
          )}
          <button
            type="submit"
            disabled={saving}
            className="mt-3 px-4 py-2 text-white text-sm font-medium rounded-lg disabled:opacity-50"
            style={{ backgroundColor: '#06C755' }}
          >
            {saving ? '保存中...' : '保存する'}
          </button>
        </form>
      )}
    </div>
  )
}
