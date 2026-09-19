import { useState } from 'react'

function isoDate(offsetDays) {
  const date = new Date(Date.now() + offsetDays * 86400000)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

export default function WelcomeScreen({ onSend, t }) {
  const [gift, setGift] = useState(true)
  const [budget, setBudget] = useState('')
  const [when, setWhen] = useState(() => isoDate(1))
  const [city, setCity] = useState('')

  function submitPlan(e) {
    e.preventDefault()
    const preferences = { recipient: gift ? null : 'myself', budget: Number(budget) || null, delivery_date: when || null, city: city.trim() || null }
    onSend(t.planMessage({ gift, budget: budget && Number(budget).toLocaleString('en-LK'), when, city: city.trim() }), { type: 'set_preferences', preferences })
  }

  return (
    <div className="welcome-screen">
      <div className="welcome-smile" aria-hidden="true" />
      <h1 className="welcome-heading">{t.welcomeHeading}</h1>
      <p className="welcome-sub">{t.welcomeSub}</p>
      <div className="welcome-chips">
        {t.chips.map((chip) => (
          <button key={chip} className="chip" onClick={() => onSend(chip.replace(/^\S+\s/, ''))}>
            {chip}
          </button>
        ))}
      </div>
      <form className="quick-plan" onSubmit={submitPlan}>
        <div className="quick-plan-title">{t.planTitle}</div>
        <div className="quick-plan-row">
          <span className="quick-plan-label">{t.planFor}</span>
          <div className="segmented">
            <button type="button" className={gift ? '' : 'active'} onClick={() => setGift(false)}>{t.planForMe}</button>
            <button type="button" className={gift ? 'active' : ''} onClick={() => setGift(true)}>{t.planForGift}</button>
          </div>
        </div>
        <div className="quick-plan-fields">
          <label>
            <span>{t.planBudget}</span>
            <input type="number" min="0" step="500" inputMode="numeric" value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="10,000" />
          </label>
          <label>
            <span>{t.planWhen}</span>
            <input type="date" min={isoDate(0)} value={when} onChange={(e) => setWhen(e.target.value)} />
          </label>
          <label>
            <span>{t.planCity}</span>
            <input type="text" value={city} onChange={(e) => setCity(e.target.value)} placeholder="Colombo 05" maxLength={60} />
          </label>
        </div>
        <button className="quick-plan-go" type="submit">{t.planGo} →</button>
      </form>
    </div>
  )
}
