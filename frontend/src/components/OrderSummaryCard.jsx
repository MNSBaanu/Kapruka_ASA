import { formatDate, formatMoney } from '../i18n'

export default function OrderSummaryCard({ summary, state, disabled, onConfirm, onEdit, t, lang }) {
  const { items, delivery, recipient, sender } = summary

  return (
    <div className={`summary-card ${state}`}>
      <div className="summary-title">🧾 {t.summaryTitle}</div>
      <ul className="summary-items">
        {items.map((item) => (
          <li key={item.product_id}>
            {item.image ? <img src={item.image} alt="" /> : <span className="cart-line-thumb">📦</span>}
            <span className="summary-item-name">
              {item.quantity} × {item.name}
              {item.icing_text && <small>🎂 {t.icing}: “{item.icing_text}”</small>}
            </span>
            <span className="summary-item-price">{formatMoney(item.line_total, item.currency)}</span>
          </li>
        ))}
      </ul>
      <dl className="summary-totals">
        <dt>{t.subtotal}</dt><dd>{formatMoney(summary.subtotal, summary.currency)}</dd>
        <dt>{t.deliveryFee}</dt><dd>{formatMoney(summary.delivery_fee, summary.delivery_fee_currency)}</dd>
        {summary.estimated_total != null && <><dt className="total">{t.total}</dt><dd className="total">{formatMoney(summary.estimated_total, summary.currency)}</dd></>}
      </dl>
      <dl className="summary-details">
        <dt>{t.to}</dt>
        <dd>{recipient.name} · {recipient.phone}<br />{delivery.address}, {delivery.city}</dd>
        <dt>{t.deliverOn}</dt>
        <dd>{formatDate(delivery.date, lang)}{delivery.instructions && <><br /><small>{delivery.instructions}</small></>}</dd>
        <dt>{t.from}</dt>
        <dd>{sender.anonymous ? t.anonymous : sender.name}</dd>
        {summary.gift_message && <><dt>{t.giftMessage}</dt><dd className="summary-gift">“{summary.gift_message}”</dd></>}
      </dl>
      {summary.warnings?.length > 0 && (
        <ul className="summary-warnings">
          {summary.warnings.map((w, i) => <li key={i}>⚠️ {w}</li>)}
        </ul>
      )}
      {state === 'active' ? (
        <div className="summary-actions">
          <button className="summary-confirm" disabled={disabled} onClick={onConfirm}>{t.confirm}</button>
          <button className="summary-edit" disabled={disabled} onClick={onEdit}>{t.edit}</button>
        </div>
      ) : (
        <div className="summary-state">{state === 'confirmed' ? t.confirmed : t.replaced}</div>
      )}
    </div>
  )
}
