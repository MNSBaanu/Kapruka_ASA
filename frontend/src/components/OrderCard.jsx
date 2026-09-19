import { useEffect, useState } from 'react'
import { formatMoney } from '../i18n'

function minutesLeft(expiresAt) {
  const ms = expiresAt ? new Date(expiresAt).getTime() - Date.now() : NaN
  return Number.isNaN(ms) ? null : Math.max(0, Math.ceil(ms / 60000))
}

export default function OrderCard({ data, status, onPaid, t }) {
  const [mins, setMins] = useState(() => minutesLeft(data?.expires_at))

  useEffect(() => {
    if (status !== 'ready' || !data?.expires_at) return
    const timer = setInterval(() => setMins(minutesLeft(data.expires_at)), 30000)
    return () => clearInterval(timer)
  }, [status, data?.expires_at])

  if (status === 'pending' || !data) {
    return (
      <div className="order-card pending">
        <div className="order-card-header">
          <span className="order-card-spinner" />
          {t.orderPending}
        </div>
      </div>
    )
  }

  const totals = data.totals || {}
  const expired = mins === 0

  return (
    <div className={`order-card ${status}${expired ? ' expired' : ''}`}>
      <div className="order-card-header">🎉 {t.orderReady}</div>
      <div className="order-card-items">
        {data.items.map((item, i) => (
          <span key={i} className="order-card-item">
            {item.image && <img src={item.image} alt="" />}
            {item.quantity} × {item.name}
          </span>
        ))}
      </div>
      <dl className="summary-totals">
        {totals.items_total != null && <><dt>{t.subtotal}</dt><dd>{formatMoney(totals.items_total, totals.currency)}</dd></>}
        {totals.delivery_fee != null && <><dt>{t.deliveryFee}</dt><dd>{formatMoney(totals.delivery_fee, totals.currency)}</dd></>}
        {totals.grand_total != null && <><dt className="total">{t.grandTotal}</dt><dd className="total">{formatMoney(totals.grand_total, totals.currency)}</dd></>}
      </dl>
      <div className="order-card-body">{t.orderRef}: <strong>{data.order_ref}</strong></div>
      {status === 'done' ? (
        <div className="order-card-body">{t.orderDone}</div>
      ) : expired ? (
        <div className="order-card-body">{t.expired}</div>
      ) : (
        <>
          <a className="order-card-pay-btn" href={data.checkout_url} target="_blank" rel="noopener noreferrer">
            {t.pay} →
          </a>
          <div className="order-card-footer">
            {mins != null && <span>⏱ {t.priceLock(mins)}</span>}
            <button className="order-card-paid" onClick={onPaid}>{t.paid}</button>
          </div>
        </>
      )}
    </div>
  )
}
