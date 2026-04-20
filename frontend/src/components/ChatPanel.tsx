import { useState, useRef, useEffect } from 'react'
import { api } from '../api/client'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ChatPanelProps {
  networkId: string
  mode: 'learn' | 'command'
}

export default function ChatPanel({ networkId, mode }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const userMsg = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)

    try {
      const res = await api.chat(networkId, mode, userMsg)
      setMessages((prev) => [...prev, { role: 'assistant', content: res.message }])
    } catch (e: any) {
      setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${e.message}` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <p className="text-gray-500 text-sm">
            Ask about training progress, modify config, or get insights...
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`text-sm ${msg.role === 'user' ? 'text-white' : 'text-gray-300'}`}>
            <span className={`text-xs font-mono ${msg.role === 'user' ? 'text-accent-green' : 'text-accent-amber'}`}>
              {msg.role === 'user' ? 'you' : 'ai'}
            </span>
            <p className="mt-0.5 whitespace-pre-wrap">{msg.content}</p>
          </div>
        ))}
        {loading && (
          <div className="text-gray-500 text-sm animate-pulse">Thinking...</div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="border-t border-border-subtle p-2">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            placeholder={`Chat (${mode} mode)...`}
            className="flex-1 bg-bg-primary border border-border-subtle rounded px-3 py-1.5 text-sm focus:outline-none focus:border-accent-green"
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="px-3 py-1.5 bg-accent-green text-black text-sm rounded font-medium disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
