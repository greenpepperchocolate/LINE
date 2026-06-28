'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { setTokens } from '@/lib/api'

type Mode = 'login' | 'register'

export default function LoginPage() {
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL
      if (!apiUrl) {
        setError('NEXT_PUBLIC_API_URL is not set in build env')
        setLoading(false)
        return
      }

      const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
      const body =
        mode === 'login'
          ? { email, password }
          : { email, password, name }

      const res = await fetch(`${apiUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      const data = await res.json().catch(() => null)

      if (res.ok && data?.success) {
        // JWT トークンを保存
        setTokens(data.access, data.refresh)
        if (data.data?.name) localStorage.setItem('lh_staff_name', data.data.name)
        if (data.data?.role) localStorage.setItem('lh_staff_role', data.data.role)
        router.push('/')
        return
      }

      if (res.status === 401) {
        setError('メールアドレスまたはパスワードが正しくありません')
      } else {
        setError(data?.error || (mode === 'login' ? 'ログインに失敗しました' : '登録に失敗しました'))
      }
    } catch {
      setError('接続に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-white">
      <div className="glass-card p-8 w-full max-w-sm">
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-base mx-auto mb-3 shadow-lg" style={{ background: 'linear-gradient(135deg, #06C755, #0ea5e9)' }}>
            LV
          </div>
          <h1 className="text-xl font-bold text-gradient">LINE VALUE</h1>
          <p className="text-sm text-gray-500 mt-1">
            {mode === 'login' ? '管理画面にログイン' : '管理アカウントを作成'}
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {mode === 'register' && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">名前</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="表示名"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
          )}

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">メールアドレス</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              autoFocus
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">パスワード</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === 'register' ? '8文字以上' : 'パスワードを入力'}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              required
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 mb-4">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !email || !password}
            className="w-full py-3 text-white font-medium rounded-lg transition-opacity hover:opacity-90 disabled:opacity-50"
            style={{ backgroundColor: '#06C755' }}
          >
            {loading
              ? (mode === 'login' ? 'ログイン中...' : '登録中...')
              : (mode === 'login' ? 'ログイン' : 'アカウント作成')}
          </button>
        </form>

        <div className="text-center mt-5">
          <button
            type="button"
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}
            className="text-sm text-gray-500 hover:text-green-600 transition-colors"
          >
            {mode === 'login'
              ? 'アカウントをお持ちでない方はこちら（新規登録）'
              : 'すでにアカウントをお持ちの方はこちら（ログイン）'}
          </button>
        </div>
      </div>
    </div>
  )
}
