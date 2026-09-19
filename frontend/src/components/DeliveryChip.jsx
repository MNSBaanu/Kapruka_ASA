import { formatDate, formatMoney } from '../i18n'

export default function DeliveryChip({ data, t, lang }) {
  const ok = data.available !== false
  return (
    <div className={`delivery-chip${ok ? '' : ' unavailable'}`}>
      <div className="delivery-chip-main">
        🚚 <strong>{t.deliveryTo(data.city, formatDate(data.checked_date, lang))}</strong>
        {data.product_name && <span className="delivery-chip-product"> · {data.product_name}</span>}
      </div>
      <div className="delivery-chip-status">
        {ok ? `✓ ${t.available}` : `✗ ${t.unavailable}`}
        {ok && typeof data.rate === 'number' && <> · {formatMoney(data.rate, data.currency || 'LKR')}</>}
        {!ok && data.next_available_date && <> · {t.nextAvailable(formatDate(data.next_available_date, lang))}</>}
      </div>
      {data.perishable_warning && <div className="delivery-chip-warning">⚠️ {data.perishable_warning}</div>}
    </div>
  )
}
