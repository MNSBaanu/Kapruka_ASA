import { useState, useRef, useCallback } from 'react'

export function useChat(sessionId = 'default') {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const abortRef = useRef(null)

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isLoading) return

    setIsLoading(true)
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
            setMessages((prev) => {
              const last = prev[prev.length - 1]
              if (last?.role === 'assistant') {
                return [...prev.slice(0, -1), { role: 'assistant', content: data.content }]
              }
              return [...prev, { role: 'assistant', content: data.content }]
            })
          }

          if (data.type === 'tool_call') {
            setMessages((prev) => [
              ...prev,
              { role: 'tool', tool: data.tool, args: data.args },
            ])
          }
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${err.message}` },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, isLoading])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return { messages, sendMessage, isLoading, clearMessages }
}
