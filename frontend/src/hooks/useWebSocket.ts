import { useEffect, useRef, useCallback } from 'react'

export function useWebSocket(networkId: string | undefined, onMessage: (data: any) => void) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const connect = useCallback(() => {
    if (!networkId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/networks/${networkId}/activity`)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      reconnectTimer.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }

    wsRef.current = ws
  }, [networkId, onMessage])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  return wsRef
}
