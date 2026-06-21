import { useState, useRef, useCallback } from 'react'

export function useChat(sessionId = 'default') {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [activeTool, setActiveTool] = useState(null)
  const [orderStatus, setOrderStatus] = useState(null)
  const [orderData, setOrderData] = useState(null)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isLoading) return

    setIsLoading(true)
    setError(null)
    setActiveTool(null)
    setOrderStatus(null)
    setOrderData(null)

    const userMsg = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Id': sessionId,
        },
        body: JSON.stringify({ message: text }),
      })

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = JSON.parse(line.slice(6))

          if (data.type === 'text') {
            setActiveTool(null)
            setMessages((prev) => {
              const last = prev[prev.length - 1]
              if (last?.role === 'assistant') {
                return [...prev.slice(0, -1), { role: 'assistant', content: data.content }]
              }
              return [...prev, { role: 'assistant', content: data.content }]
            })
          }

          if (data.type === 'tool_call') {
            setActiveTool(data.tool)
            setMessages((prev) => [
              ...prev,
              { role: 'tool', tool: data.tool, args: data.args },
            ])
          }

          if (data.type === 'order_confirmation') {
            setActiveTool(null)
            setOrderStatus('ready')
            setOrderData(data.data)
            setMessages((prev) => [
              ...prev,
              { role: 'order', data: data.data, orderStatus: 'ready' },
            ])
          }
        }
      }
    } catch (err) {
      setError(err.message)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Something went wrong: ${err.message}. Please try again.` },
      ])
    } finally {
      setIsLoading(false)
      setActiveTool(null)
    }
  }, [sessionId, isLoading])

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
    setActiveTool(null)
    setOrderStatus(null)
    setOrderData(null)
  }, [])

  return { messages, sendMessage, isLoading, activeTool, orderStatus, orderData, error, clearMessages }
}
