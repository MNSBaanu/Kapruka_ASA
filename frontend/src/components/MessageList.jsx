import { useEffect, useRef } from 'react'
import UserBubble from './UserBubble'
import AssistantBubble from './AssistantBubble'
import OrderCard from './OrderCard'
import OrderSummaryCard from './OrderSummaryCard'
import TrackingCard from './TrackingCard'
import DeliveryChip from './DeliveryChip'
import ToolIndicator from './ToolIndicator'
import TypingIndicator from './TypingIndicator'
import WelcomeScreen from './WelcomeScreen'

export default function MessageList({ chat, t, lang }) {
  const { messages, products, cart, isLoading, activeTool, stillLooking, orderPending, sendMessage, retry, updateMessage } = chat
  const bottomRef = useRef(null)
  const last = messages[messages.length - 1]

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages.length, last?.content, isLoading, activeTool, orderPending])

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="message-list">
        <WelcomeScreen onSend={sendMessage} t={t} />
      </div>
    )
  }

  const onChoose = (p) => sendMessage(t.chooseMessage(p.name), { type: 'select_product', product_id: p.id })
  const onDetails = (p) => sendMessage(t.detailsMessage(p.name), { type: 'product_details', product_id: p.id })
  const streaming = last?.role === 'assistant' && last.streaming
  const lastAssistant = messages.findLastIndex((m) => m.role === 'assistant')

  return (
    <div className="message-list" aria-live="polite">
      {messages.map((msg, i) => {
        switch (msg.role) {
          case 'user':
            return <UserBubble key={i} content={msg.content} />
          case 'assistant':
            return (
              <AssistantBubble
                key={i}
                content={msg.content}
                streaming={msg.streaming}
                productIds={msg.productIds}
                products={products}
                cart={cart}
                onChoose={isLoading ? null : onChoose}
                onDetails={isLoading ? null : onDetails}
                onMore={isLoading || i !== lastAssistant ? null : () => sendMessage(t.moreMessage)}
                t={t}
              />
            )
          case 'delivery':
            return <DeliveryChip key={i} data={msg.data} t={t} lang={lang} />
          case 'tracking':
            return <TrackingCard key={i} orderNumber={msg.orderNumber} data={msg.data} t={t} />
          case 'summary':
            return (
              <OrderSummaryCard
                key={i}
                summary={msg.summary}
                state={msg.state}
                disabled={isLoading}
                onConfirm={() => sendMessage(t.confirmMessage, { type: 'confirm_order' })}
                onEdit={() => sendMessage(t.editMessage)}
                t={t}
                lang={lang}
              />
            )
          case 'order':
            return (
              <OrderCard
                key={i}
                data={msg.data}
                status={msg.status}
                t={t}
                onPaid={() => {
                  updateMessage(i, { status: 'done' })
                  sendMessage(t.paidMessage, { type: 'paid', order_ref: msg.data.order_ref })
                }}
              />
            )
          case 'error':
            return (
              <div key={i} className="error-inline">
                <span>⚠️ {msg.message || t.somethingWrong}</span>
                {msg.retry && <button onClick={() => retry(msg.retry)} disabled={isLoading}>{t.tryAgain}</button>}
              </div>
            )
          default:
            return null
        }
      })}

      {orderPending && <OrderCard status="pending" t={t} />}
      {isLoading && activeTool && !orderPending && <ToolIndicator tool={activeTool} stillLooking={stillLooking} t={t} />}
      {isLoading && !activeTool && !streaming && !orderPending && <TypingIndicator />}

      <div ref={bottomRef} />
    </div>
  )
}
