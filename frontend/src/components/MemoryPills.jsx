import { formatDate, formatMoney } from '../i18n'

export default function MemoryPills({ memory, t, lang }) {
  const pills = []
  if (typeof memory.budget === 'number') pills.push(`${t.memory.budget} ${formatMoney(memory.budget, memory.currency || 'LKR')}`)
  if (memory.city) pills.push(`${t.memory.city} ${memory.city}`)
  if (memory.delivery_date) pills.push(`${t.memory.delivery_date} ${formatDate(memory.delivery_date, lang)}`)
  if (memory.recipient) pills.push(`${t.memory.recipient} ${memory.recipient}`)
  if (memory.occasion && memory.occasion !== 'everyday') pills.push(`${t.memory.occasion} ${memory.occasion.replace('_', ' ')}`)
  if (!pills.length) return null

  return (
    <div className="memory-pills" aria-label="What I know so far">
      {pills.map((pill) => <span key={pill} className="memory-pill">{pill}</span>)}
    </div>
  )
}
