export default function OrderCard({ data, status }) {
  if (status === 'pending' || !data) {
    return (
      <div className="order-card pending">
        <div className="order-card-header">
          <span className="order-card-spinner" />
          Preparing order...
        </div>
      </div>
    )
  }

  if (status === 'done') {
    return (
      <div className="order-card done">
        <div className="order-card-header">✓ Order placed</div>
        {data.order_number && (
          <div className="order-card-body">
            Order #{data.order_number}
          </div>
        )}
      </div>
    )
  }

  const payUrl = data.pay_url || data.payment_url || data.url || ''

  return (
    <div className="order-card ready">
      <div className="order-card-header">🛒 Order Confirmation</div>
      <div className="order-card-body">
        {data.message || 'Your order is ready!'}
      </div>
      {payUrl && (
        <>
          <a href={payUrl} target="_blank" rel="noopener noreferrer">
            <button className="order-card-pay-btn">
              Pay via Kapruka Pay
            </button>
          </a>
          <a
            className="order-card-link"
            href={payUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            {payUrl}
          </a>
        </>
      )}
    </div>
  )
}
