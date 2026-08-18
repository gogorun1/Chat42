import { useEffect, useRef, useState } from 'react'

// Broadcast payload shape from broadcast_sighting() in notification_service.py
export type SightingBroadcast = {
  channel: 'sighting'
  sighting_id: number
  zone_id: number
  zone_name: string
  created_at: string
  image_url: string
  message: string
}

// Payload shape from notify_user() - addressed, per-user notifications
export type NotificationPush = {
  channel: 'notification'
  id: string
  type: string
  title: string
  body: string | null
  data: Record<string, unknown>
  created_at: string
}

export type SocketMessage = SightingBroadcast | NotificationPush

export function useSightingSocket(onMessage: (msg: SocketMessage) => void, enabled = true) {
  const [connected, setConnected] = useState(false)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  useEffect(() => {
    if (!enabled) return
    let socket: WebSocket | null = null
    let heartbeat: ReturnType<typeof setInterval> | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let cancelled = false

    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      socket = new WebSocket(`${protocol}//${window.location.host}/ws/sightings`)

      socket.onopen = () => {
        setConnected(true)
        heartbeat = setInterval(() => socket?.readyState === WebSocket.OPEN && socket.send('ping'), 25000)
      }

      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data) as SocketMessage
          onMessageRef.current(parsed)
        } catch {
          // non-JSON frame (e.g. a stray pong) - ignore
        }
      }

      socket.onclose = () => {
        setConnected(false)
        if (heartbeat) clearInterval(heartbeat)
        if (!cancelled) reconnectTimer = setTimeout(connect, 3000)
      }

      socket.onerror = () => socket?.close()
    }

    connect()

    return () => {
      cancelled = true
      if (heartbeat) clearInterval(heartbeat)
      if (reconnectTimer) clearTimeout(reconnectTimer)
      socket?.close()
    }
  }, [enabled])

  return { connected }
}
