import { useState } from 'react'
import { useChat } from './hooks/useChat'
import MessageList from './components/MessageList'
import ChatInput from './components/ChatInput'
import './App.css'

function generateSessionId() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID()
  return 'session_' + Date.now() + '_' + Math.random().toString(36).slice(2, 9)
}

function App() {
  const [sessionId] = useState(() => generateSessionId())
  const {
    messages,
    sendMessage,
    isLoading,
    activeTool,
    orderStatus,
    orderData,
    error,
  } = useChat(sessionId)

  return (
    <div className="app">
      <header className="app-header">
        <svg className="app-logo" viewBox="0 0 95 32" aria-label="Kapruka">
          <text x="0" y="24" fontWeight="700" fontSize="22" fill="#1f6b0c" fontFamily="Arial, sans-serif">
            Kapruka
          </text>
        </svg>
      </header>

      {error && (
        <div className="error-banner">
          ⚠️ Connection lost. Retrying...
        </div>
      )}

      <MessageList
        messages={messages}
        isLoading={isLoading}
        activeTool={activeTool}
        orderStatus={orderStatus}
        orderData={orderData}
        onSend={sendMessage}
      />

      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  )
}

export default App
