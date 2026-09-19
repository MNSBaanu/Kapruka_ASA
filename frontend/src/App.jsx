import { useEffect, useState } from 'react'
import { useChat } from './hooks/useChat'
import { LANGS, STRINGS } from './i18n'
import MessageList from './components/MessageList'
import ChatInput from './components/ChatInput'
import CartBar from './components/CartBar'
import MemoryPills from './components/MemoryPills'
import './App.css'

const UI_LANG_KEY = 'kapruka.uiLang'

function initialUiLang() {
  try {
    const stored = localStorage.getItem(UI_LANG_KEY)
    if (STRINGS[stored]) return { lang: stored, manual: true }
  } catch {
    return { lang: 'en', manual: false }
  }
  const browser = (navigator.language || 'en').slice(0, 2)
  return { lang: STRINGS[browser] ? browser : 'en', manual: false }
}

function useConnection() {
  const [state, setState] = useState('connecting')

  useEffect(() => {
    let cancelled = false
    let attempt = 0
    let timer
    const check = async () => {
      try {
        const res = await fetch('/api/health')
        const data = await res.json()
        if (!cancelled) setState(data.status === 'ok' ? 'ok' : 'degraded')
      } catch {
        if (cancelled) return
        attempt += 1
        setState(attempt >= 3 ? 'offline' : 'connecting')
        timer = setTimeout(check, Math.min(2000 * attempt, 10000))
      }
    }
    check()
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [])

  return state
}

function App() {
  const chat = useChat()
  const connection = useConnection()
  const [ui, setUi] = useState(initialUiLang)
  const detected = chat.lang
  const uiLang = !ui.manual && STRINGS[detected] ? detected : ui.lang
  const t = STRINGS[uiLang]

  useEffect(() => {
    document.documentElement.lang = detected || uiLang
  }, [detected, uiLang])

  function chooseLang(lang) {
    setUi({ lang, manual: true })
    try {
      localStorage.setItem(UI_LANG_KEY, lang)
    } catch {
      return
    }
  }

  if (connection === 'connecting' && chat.messages.length === 0) {
    return (
      <div className="loading-screen">
        <img className="loading-logo" src="/kapruka-logo.jpg" alt="Kapruka" />
        <div className="loading-spinner" />
        <div className="loading-text">{t.connecting}</div>
      </div>
    )
  }

  const banner = chat.retrying ? t.retrying : connection === 'offline' ? t.offline : connection === 'degraded' ? t.degraded : null

  return (
    <div className="app">
      <header className="app-header">
        <button className="header-btn" onClick={chat.reset} disabled={chat.isLoading || chat.messages.length === 0}>
          ＋ {t.newChat}
        </button>
        <img className="app-logo" src="/kapruka-logo.jpg" alt="Kapruka" />
        <div className="lang-switch" role="group" aria-label="Language">
          {LANGS.map(({ code, label }) => (
            <button key={code} className={uiLang === code ? 'active' : ''} onClick={() => chooseLang(code)} lang={code}>
              {label}
            </button>
          ))}
        </div>
      </header>

      {banner && <div className="error-banner">{banner}</div>}
      <MemoryPills memory={chat.memory} t={t} lang={uiLang} />

      <MessageList chat={chat} t={t} lang={uiLang} />

      <CartBar
        cart={chat.cart}
        disabled={chat.isLoading}
        onContinue={() => chat.sendMessage(t.continueMessage)}
        onRemove={(line) => chat.sendMessage(t.removeMessage(line.name), { type: 'remove_from_cart', product_id: line.product_id })}
        t={t}
      />
      <ChatInput onSend={chat.sendMessage} disabled={chat.isLoading} hasError={chat.failed} t={t} />
    </div>
  )
}

export default App
