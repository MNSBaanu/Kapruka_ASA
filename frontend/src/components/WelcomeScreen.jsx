export default function WelcomeScreen({ onSend }) {
  const suggestions = [
    'I need a birthday gift',
    'Find me flowers',
    'What chocolates do you have?',
  ]

  return (
    <div className="welcome-screen">
      <div className="welcome-icon">🛍️</div>
      <div className="welcome-heading">
        I'm your Kapruka assistant!
      </div>
      <div className="welcome-sub">
        Ask me to find products, check delivery, or place an order.
      </div>
      <ul className="welcome-suggestions">
        {suggestions.map((s, i) => (
          <li key={i}>
            <button
              onClick={() => onSend(s)}
              style={{
                background: 'none',
                border: 'none',
                color: 'inherit',
                fontSize: 'inherit',
                cursor: 'pointer',
                padding: 0,
                fontFamily: 'inherit',
              }}
            >
              {s}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
