import { useEffect, useState } from 'react'

const MAX_AUTO_RETRY_SECONDS = 60

export default function ErrorNotice({ message, retry, retryAfter, disabled, onRetry, t }) {
  const [seconds, setSeconds] = useState(retry && retryAfter <= MAX_AUTO_RETRY_SECONDS ? retryAfter : null)

  useEffect(() => {
    if (seconds == null) return
    if (seconds <= 0) {
      onRetry(retry)
      return
    }
    const timer = setTimeout(() => setSeconds(seconds - 1), 1000)
    return () => clearTimeout(timer)
  }, [seconds, retry, onRetry])

  return (
    <div className="error-inline">
      <span>
        ⚠️ {message || t.somethingWrong}
        {seconds > 0 && <> {t.retryIn(seconds)}</>}
      </span>
      {retry && <button onClick={() => onRetry(retry)} disabled={disabled}>{t.tryAgain}</button>}
    </div>
  )
}
