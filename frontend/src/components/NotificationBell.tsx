import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import type { NotificationPush, SocketMessage } from '../lib/useSightingSocket'
import { useSightingSocket } from '../lib/useSightingSocket'

type NotificationItem = {
  id: string
  type: string
  title: string
  body: string | null
  data: Record<string, unknown>
  created_at: string
  read_at: string | null
}

type NotificationListResponse = {
  items: NotificationItem[]
  unread_count: number
  total: number
  page: number
  page_size: number
}

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState<NotificationItem[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const fetchNotifications = useCallback(async () => {
    setLoading(true)
    try {
      // NOTE: confirm this path against main.py's app.include_router() --
      // your codebase mixes prefixed (/api/search/...) and unprefixed
      // (/sightings/zones) routes, and I haven't seen how notification.py
      // is mounted. Change to '/api/notifications' if it's registered
      // under the /api prefix.
      const data = await api.get<NotificationListResponse>('/notifications?page=1&page_size=20')
      setItems(data.items)
      setUnreadCount(data.unread_count)
    } catch {
      // swallow -- an empty bell is better than a crashed header
    } finally {
      setLoading(false)
    }
  }, [])

  // initial load
  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  // live push -> prepend directly and bump the badge, so unread count
  // never goes stale even if the panel is closed
  const handleSocketMessage = useCallback((msg: SocketMessage) => {
    if (msg.channel !== 'notification') return
    const push = msg as NotificationPush
    setUnreadCount((prev) => prev + 1)
    setItems((prev) => [
      {
        id: push.id,
        type: push.type,
        title: push.title,
        body: push.body,
        data: push.data,
        created_at: push.created_at,
        read_at: null,
      },
      ...prev,
    ])
  }, [])
  useSightingSocket(handleSocketMessage)

  // close on outside click
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  async function markRead(id: string) {
    setItems((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n))
    )
    setUnreadCount((prev) => Math.max(0, prev - 1))
    try {
      await api.post(`/notifications/${id}/read`)
    } catch {
      // best-effort -- local state already updated optimistically
    }
  }

  async function markAllRead() {
    setItems((prev) => prev.map((n) => ({ ...n, read_at: n.read_at ?? new Date().toISOString() })))
    setUnreadCount(0)
    try {
      await api.post('/notifications/read-all')
    } catch {
      // best-effort -- local state already updated optimistically
    }
  }

  return (
    <div className="relative" ref={containerRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative rounded-full p-2 text-slate-300 hover:bg-slate-800 hover:text-slate-100"
        aria-label="Notifications"
      >
        <BellIcon />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-md border border-slate-700 bg-slate-900 shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
            <span className="text-sm font-medium text-slate-200">Notifications</span>
            {unreadCount > 0 && (
              <button onClick={markAllRead} className="text-xs text-sky-400 hover:text-sky-300">
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {loading && items.length === 0 && (
              <p className="px-3 py-4 text-sm text-slate-500">Loading…</p>
            )}
            {!loading && items.length === 0 && (
              <p className="px-3 py-4 text-sm text-slate-500">No notifications yet.</p>
            )}
            {items.map((n) => (
              <button
                key={n.id}
                onClick={() => !n.read_at && markRead(n.id)}
                className={`block w-full border-b border-slate-800 px-3 py-2 text-left last:border-0 hover:bg-slate-800 ${
                  n.read_at ? 'opacity-60' : ''
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-sm font-medium text-slate-100">{n.title}</span>
                  {!n.read_at && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-sky-400" />}
                </div>
                {n.body && <p className="mt-0.5 text-xs text-slate-400">{n.body}</p>}
                <p className="mt-1 text-[11px] text-slate-500">
                  {new Date(n.created_at).toLocaleString()}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5">
      <path
        d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M13.73 21a2 2 0 01-3.46 0"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}