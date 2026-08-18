import { createContext, useContext, useEffect, useRef, type ReactNode } from 'react'
import { useSightingSocket, type SocketMessage } from '../lib/useSightingSocket'
import { useAuth } from './AuthContext'

type Listener = (msg: SocketMessage) => void

type SocketContextValue = {
  subscribe: (listener: Listener) => () => void
  connected: boolean
}

const SocketContext = createContext<SocketContextValue | undefined>(undefined)

export function SocketProvider({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const listenersRef = useRef<Set<Listener>>(new Set())

  const { connected } = useSightingSocket(
    (msg) => {
      listenersRef.current.forEach((listener) => listener(msg))
    },
    !loading && user !== null,
  )

  function subscribe(listener: Listener) {
    listenersRef.current.add(listener)

    return () => {
      listenersRef.current.delete(listener)
    }
  }

  return (
    <SocketContext.Provider value={{ subscribe, connected }}>
      {children}
    </SocketContext.Provider>
  )
}

export function useSocketSubscription(onMessage: (msg: SocketMessage) => void) {
  const ctx = useContext(SocketContext)
  if (!ctx) {
    throw new Error('useSocketSubscription must be used within a SocketProvider')
  }

  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  useEffect(() => {
    return ctx.subscribe((msg) => onMessageRef.current(msg))
  }, [ctx])

  return { connected: ctx.connected }
}