import { useState } from 'react'

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText('')
  }

  const isEmpty = !text.trim()

  return (
    <div className="chat-input-wrapper">
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          className={`chat-input${isEmpty ? '' : ''}`}
          type="text"
          placeholder="ඔබට අවශ්‍ය කුමක්ද? / What do you need?"
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={disabled}
        />
        <button
          type="submit"
          className={`send-btn${disabled ? ' loading' : ''}${isEmpty ? ' empty' : ''}`}
          disabled={disabled || isEmpty}
        >
          {disabled ? '...' : '➤'}
        </button>
      </form>
    </div>
  )
}
