import { useCallback, useState } from 'react'
import { type SocketMessage } from '../lib/useSightingSocket'
import { useSocketSubscription } from '../context/SocketContext'

type Toast = {
  id: string
  text: string
}

export function LiveToasts() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const handleMessage = useCallback((msg: SocketMessage) => {
    const id = crypto.randomUUID()
    const text = msg.channel === 'sighting' ? msg.message : msg.title

    setToasts((prev) => [...prev, { id, text }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 6000)
  }, [])

  useSocketSubscription(handleMessage)

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="rounded-md border border-slate-700 bg-slate-900/95 px-4 py-3 text-sm text-slate-100 shadow-lg animate-in fade-in slide-in-from-bottom-2"
        >
          {t.text}
        </div>
      ))}
    </div>
  )
}
