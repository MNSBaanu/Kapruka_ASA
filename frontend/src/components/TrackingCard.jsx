const STAGE_PATTERNS = [/receiv|placed|new/i, /confirm|process|prepar|pack/i, /out|dispatch|ship|transit|way|left|vehicle/i, /deliver|complete/i]

function pick(obj, keys) {
  for (const key of keys) if (obj?.[key]) return obj[key]
  return null
}

function formatTime(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export default function TrackingCard({ orderNumber, data, t }) {
  const status = String(pick(data, ['status', 'order_status', 'state']) || '')
  const timeline = pick(data, ['timeline', 'progress', 'events', 'history', 'tracking']) || []
  const items = pick(data, ['items', 'cart', 'products']) || []
  const cancelled = /cancel/i.test(status)
  let stage = -1
  STAGE_PATTERNS.forEach((pattern, i) => {
    if (pattern.test(status)) stage = i
  })

  return (
    <div className="tracking-card">
      <div className="tracking-header">
        <span>📦 {t.trackingTitle(orderNumber)}</span>
        {status && <span className={`tracking-status${cancelled ? ' cancelled' : ''}`}>{cancelled ? t.cancelled : status}</span>}
      </div>
      {!cancelled && (
        <div className="tracking-stages">
          {t.stages.map((label, i) => (
            <div key={label} className={`tracking-stage${i <= stage ? ' done' : ''}${i === stage ? ' current' : ''}`}>
              <span className="tracking-dot" />
              <span>{label}</span>
            </div>
          ))}
        </div>
      )}
      {Array.isArray(timeline) && timeline.length > 0 && (
        <ol className="tracking-timeline">
          {timeline.map((entry, i) => (
            <li key={i}>
              <span className="tracking-event">{typeof entry === 'string' ? entry : pick(entry, ['status', 'title', 'label', 'event', 'description', 'message'])}</span>
              {typeof entry === 'object' && pick(entry, ['timestamp', 'time', 'at', 'date']) && (
                <time>{formatTime(pick(entry, ['timestamp', 'time', 'at', 'date']))}</time>
              )}
            </li>
          ))}
        </ol>
      )}
      {Array.isArray(items) && items.length > 0 && (
        <div className="tracking-items">
          {items.map((item, i) => (
            <span key={i}>{item.quantity || item.qty || 1} × {pick(item, ['name', 'product_name', 'title']) || pick(item, ['product_id', 'id'])}</span>
          ))}
        </div>
      )}
      {(data?.delivery_photo_available || data?.has_delivery_photo || data?.photo_available) && <div className="tracking-photo">{t.photo}</div>}
    </div>
  )
}
