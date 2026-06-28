import type { Metadata } from 'next'
import './globals.css'
import AppShell from '@/components/app-shell'

export const metadata: Metadata = {
  title: 'LINE VALUE',
  description: 'LINE VALUE 管理画面',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body className="text-gray-900 antialiased">
        <AppShell>
          {children}
        </AppShell>
      </body>
    </html>
  )
}
