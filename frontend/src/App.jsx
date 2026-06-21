import { useChat } from './hooks/useChat'

function App() {
  const { messages, sendMessage, isLoading } = useChat()

  return (
    <div>
      <p>Kapruka ASA — UI coming soon</p>
      <p>Messages: {messages.length}</p>
    </div>
  )
}

export default App
