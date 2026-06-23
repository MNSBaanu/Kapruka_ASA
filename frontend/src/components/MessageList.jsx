import { useEffect, useRef } from 'react'
import UserBubble from './UserBubble'
import AssistantBubble from './AssistantBubble'
import ProductCard from './ProductCard'
import OrderCard from './OrderCard'
import ToolIndicator from './ToolIndicator'
import TypingIndicator from './TypingIndicator'
import WelcomeScreen from './WelcomeScreen'

function parseProductsFromText(text) {
  const products = []
  const lines = text.split('\n')
  let current = null

  for (const line of lines) {
    const nameMatch = line.match(/^\*\*(.+?)\*\*/)
    if (nameMatch) {
      if (current) products.push(current)
      current = { name: nameMatch[1] }
      continue
    }
    if (!current) continue
    const priceMatch = line.match(/LKR\s*([\d,]+(?:\.\d{2})?)/)
    if (priceMatch) {
      current.price = parseFloat(priceMatch[1].replace(/,/g, ''))
    }
    const stockMatch = line.match(/(✅|❌)\s*(In Stock|Out of Stock)/)
    if (stockMatch) {
      current.stock = stockMatch[2] === 'In Stock'
    }
    const urlMatch = line.match(/https?:\/\/[^\s]+/)
    if (urlMatch) {
      current.url = urlMatch[0]
    }
    const imageMatch = line.match(/!\[.*?\]\((.*?)\)/)
    if (imageMatch) {
      current.image = imageMatch[1]
    }
  }
  if (current) products.push(current)

  return products
}

export default function MessageList({
  messages,
  isLoading,
  activeTool,
  orderStatus,
  orderData,
  onSend,
}) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading, activeTool])

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="message-list">
        <WelcomeScreen onSend={onSend} />
      </div>
    )
  }

  return (
    <div className="message-list">
      {messages.map((msg, i) => {
        if (msg.role === 'user') {
          return <UserBubble key={i} content={msg.content} />
        }
        if (msg.role === 'tool') {
          return <ToolIndicator key={i} tool={msg.tool} />
        }
        if (msg.role === 'assistant') {
          const products = parseProductsFromText(msg.content)
          return (
            <div key={i}>
              <AssistantBubble content={msg.content} />
              {products.length > 0 && (
                <div className={`product-grid ${products.length >= 3 ? 'carousel' : ''}`}>
                  {products.map((p, j) => (
                    <ProductCard key={j} product={p} />
                  ))}
                </div>
              )}
            </div>
          )
        }
        if (msg.role === 'order') {
          return <OrderCard key={i} data={msg.data} status={msg.orderStatus || 'ready'} />
        }
        return null
      })}

      {activeTool && <ToolIndicator tool={activeTool} />}
      {isLoading && !activeTool && <TypingIndicator />}

      {(orderStatus === 'pending') && (
        <OrderCard status="pending" />
      )}

      <div ref={bottomRef} />
    </div>
  )
}
