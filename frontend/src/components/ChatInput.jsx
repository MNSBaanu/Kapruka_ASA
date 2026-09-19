import { useState } from 'react'

export default function ChatInput({ onSend, disabled, hasError, t }) {
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
          className={`chat-input${hasError ? ' has-error' : ''}`}
          type="text"
          placeholder={t.placeholder}
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={disabled}
          maxLength={2000}
          enterKeyHint="send"
          aria-label={t.placeholder}
        />
        <button
          type="submit"
          className={`send-btn${disabled ? ' loading' : ''}${isEmpty ? ' empty' : ''}`}
          disabled={disabled || isEmpty}
          aria-label={t.send}
        >
          {disabled ? '...' : '➤'}
        </button>
      </form>
    </div>
  )
}
