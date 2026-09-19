import { useCallback, useEffect, useRef, useState } from 'react'

const SESSION_KEY = 'kapruka.session'
const STATE_KEY = 'kapruka.chat'
const LAST_ORDER_KEY = 'kapruka.lastOrder'
const RETRY_DELAYS = [1000, 3000]
const EMPTY_CART = { items: [], count: 0, subtotal: 0, currency: 'LKR' }

function load(storage, key) {
  try {
    return JSON.parse(storage.getItem(key))
  } catch {
    return null
  }
}

function save(storage, key, value) {
  try {
    storage.setItem(key, JSON.stringify(value))
  } catch {
    return false
  }
  return true
}

function newSessionId() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID()
  return 'session_' + Date.now() + '_' + Math.random().toString(36).slice(2, 11)
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

function closeBubble(messages) {
  const last = messages[messages.length - 1]
  if (last?.role === 'assistant' && last.streaming) {
    return [...messages.slice(0, -1), { ...last, streaming: false }]
  }
  return messages
}

function lastIndex(messages, predicate) {
  for (let i = messages.length - 1; i >= 0; i--) if (predicate(messages[i])) return i
  return -1
}

function applyEvent(messages, event) {
  switch (event.type) {
    case 'text_delta': {
      const last = messages[messages.length - 1]
      if (last?.role === 'assistant' && last.streaming) {
        return [...messages.slice(0, -1), { ...last, content: last.content + event.content }]
      }
      return [...messages, { role: 'assistant', content: event.content, streaming: true }]
    }
    case 'replace': {
      const i = lastIndex(messages, (m) => m.role === 'assistant' || m.role === 'user')
      if (i >= 0 && messages[i].role === 'assistant') {
        return messages.map((m, j) => (j === i ? { ...m, content: event.content } : m))
      }
      return [...messages, { role: 'assistant', content: event.content }]
    }
    case 'retract': {
      const i = lastIndex(messages, (m) => m.role === 'assistant' || m.role === 'user')
      return i >= 0 && messages[i].role === 'assistant' ? messages.filter((_, j) => j !== i) : messages
    }
    case 'attach_products': {
      const i = lastIndex(messages, (m) => m.role === 'assistant')
      return i < 0 ? messages : messages.map((m, j) => (j === i ? { ...m, productIds: event.ids } : m))
    }
    case 'tool_call':
      return closeBubble(messages)
    case 'delivery':
      return [...closeBubble(messages), { role: 'delivery', data: event.data }]
    case 'tracking':
      return [...closeBubble(messages), { role: 'tracking', orderNumber: event.order_number, data: event.data }]
    case 'order_summary':
      return [
        ...closeBubble(messages).map((m) => (m.role === 'summary' && m.state === 'active' ? { ...m, state: 'replaced' } : m)),
        { role: 'summary', summary: event.summary, state: 'active' },
      ]
    case 'order':
      return [
        ...closeBubble(messages).map((m) => (m.role === 'summary' && m.state === 'active' ? { ...m, state: 'confirmed' } : m)),
        { role: 'order', data: event.data, status: 'ready' },
      ]
    default:
      return messages
  }
}

async function readEvents(res, onEvent) {
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''
    for (const block of blocks) {
      const line = block.split('\n').find((l) => l.startsWith('data: '))
      if (line) onEvent(JSON.parse(line.slice(6)))
    }
  }
}

export function useChat() {
  const [saved] = useState(() => load(sessionStorage, STATE_KEY) || {})
  const [sessionId, setSessionId] = useState(() => load(sessionStorage, SESSION_KEY) || newSessionId())
  const [messages, setMessages] = useState(() => (saved.messages || []).map((m) => ({ ...m, streaming: false })))
  const [products, setProducts] = useState(() => saved.products || {})
  const [cart, setCart] = useState(() => saved.cart || EMPTY_CART)
  const [memory, setMemory] = useState(() => saved.memory || {})
  const [isLoading, setIsLoading] = useState(false)
  const [activeTool, setActiveTool] = useState(null)
  const [stillLooking, setStillLooking] = useState(false)
  const [orderPending, setOrderPending] = useState(false)
  const [retrying, setRetrying] = useState(false)
  const [failed, setFailed] = useState(false)
  const [lang, setLang] = useState(null)
  const busy = useRef(false)
  const request = useRef(null)
  const started = useRef(messages.length > 0)

  useEffect(() => {
    save(sessionStorage, SESSION_KEY, sessionId)
  }, [sessionId])

  useEffect(() => {
    if (!isLoading) save(sessionStorage, STATE_KEY, { messages, products, cart, memory })
  }, [messages, products, cart, memory, isLoading])

  const handleEvent = useCallback((event) => {
    switch (event.type) {
      case 'meta':
        setLang(event.lang)
        break
      case 'products':
        setProducts((prev) => ({ ...prev, ...Object.fromEntries(event.items.map((p) => [p.id.toLowerCase(), p])) }))
        break
      case 'cart':
        setCart(event.cart)
        break
      case 'memory':
        setMemory(event.memory)
        break
      case 'tool_call':
        setActiveTool(event.tool)
        break
      case 'text_delta':
        setActiveTool(null)
        break
      case 'status':
        setStillLooking(true)
        break
      case 'order_pending':
        setOrderPending(true)
        break
      case 'order':
        setOrderPending(false)
        save(localStorage, LAST_ORDER_KEY, {
          items: event.data.items.map(({ product_id, name, quantity }) => ({ product_id, name, quantity })),
          city: event.data.city,
        })
        break
      case 'order_failed':
        setOrderPending(false)
        break
      case 'error':
        setFailed(true)
        setMessages((prev) => [
          ...closeBubble(prev),
          { role: 'error', message: event.message, retryAfter: event.retry_after, retry: event.code === 'busy' ? null : request.current },
        ])
        return
      default:
        break
    }
    setMessages((prev) => applyEvent(prev, event))
  }, [])

  const post = useCallback(async (body) => {
    for (let attempt = 0; ; attempt++) {
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Session-Id': sessionId },
          body,
        })
        if (res.status >= 500 || !res.body) throw new Error(`Server error ${res.status}`)
        if (!res.ok) throw Object.assign(new Error(`Request failed ${res.status}`), { final: true })
        setRetrying(false)
        return res
      } catch (err) {
        if (err.final || attempt >= RETRY_DELAYS.length) throw err
        setRetrying(true)
        await sleep(RETRY_DELAYS[attempt])
      }
    }
  }, [sessionId])

  const sendMessage = useCallback(async (text, action = null, { resend = false } = {}) => {
    const content = (text || '').trim()
    if ((!content && !action) || busy.current) return
    busy.current = true
    setIsLoading(true)
    setFailed(false)
    setStillLooking(false)
    setActiveTool(null)
    setMessages((prev) => {
      const kept = prev.filter((m) => m.role !== 'error')
      return content && !resend ? [...kept, { role: 'user', content }] : kept
    })

    request.current = { text: content, action }
    const profile = started.current ? null : { last_order: load(localStorage, LAST_ORDER_KEY) }
    started.current = true
    try {
      const res = await post(JSON.stringify({ message: content, action, profile }))
      await readEvents(res, handleEvent)
    } catch {
      setFailed(true)
      setMessages((prev) => [...closeBubble(prev), { role: 'error', retry: { text: content, action } }])
    } finally {
      busy.current = false
      setIsLoading(false)
      setActiveTool(null)
      setStillLooking(false)
      setOrderPending(false)
      setRetrying(false)
      setMessages(closeBubble)
    }
  }, [post, handleEvent])

  const retry = useCallback((request) => {
    sendMessage(request.text, request.action, { resend: true })
  }, [sendMessage])

  const updateMessage = useCallback((index, patch) => {
    setMessages((prev) => prev.map((m, i) => (i === index ? { ...m, ...patch } : m)))
  }, [])

  const reset = useCallback(() => {
    if (busy.current) return
    fetch('/api/reset', { method: 'POST', headers: { 'X-Session-Id': sessionId } }).catch(() => null)
    setMessages([])
    setProducts({})
    setCart(EMPTY_CART)
    setMemory({})
    setFailed(false)
    started.current = false
    setSessionId(newSessionId())
  }, [sessionId])

  return {
    messages, products, cart, memory, lang,
    isLoading, activeTool, stillLooking, orderPending, retrying, failed,
    sendMessage, retry, updateMessage, reset,
  }
}
