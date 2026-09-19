import { useState } from 'react'
import { formatMoney } from '../i18n'

export default function CartBar({ cart, disabled, onContinue, onRemove, t }) {
  const [open, setOpen] = useState(false)
  if (!cart?.count) return null

  return (
    <div className="cart-bar">
      {open && (
        <ul className="cart-lines">
          {cart.items.map((line) => (
            <li key={line.product_id} className="cart-line">
              {line.image ? <img src={line.image} alt="" /> : <span className="cart-line-thumb">📦</span>}
              <div className="cart-line-info">
                <div className="cart-line-name">{line.name}</div>
                <div className="cart-line-meta">
                  {line.quantity} × {formatMoney(line.price, line.currency)}
                  {line.icing_text && <> · 🎂 “{line.icing_text}”</>}
                </div>
              </div>
              <button className="cart-line-remove" disabled={disabled} onClick={() => onRemove(line)} aria-label={t.remove}>
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="cart-bar-row">
        <button className="cart-bar-toggle" onClick={() => setOpen(!open)} aria-expanded={open}>
          🛒 <strong>{t.cartTitle}</strong> · {t.cartItems(cart.count)} · {formatMoney(cart.subtotal, cart.currency)}
          <span className={`cart-caret${open ? ' open' : ''}`}>▾</span>
        </button>
        <button className="cart-bar-continue" disabled={disabled} onClick={onContinue}>
          {t.continueDelivery}
        </button>
      </div>
    </div>
  )
}
