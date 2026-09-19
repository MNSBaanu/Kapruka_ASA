import ProductCarousel from './ProductCarousel'

const MARKER = /\[\[product:([A-Za-z0-9_-]+)\]\]/g
const INLINE = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|!\[[^\]]*\]\([^)\s]+\)|\[[^\]]+\]\([^)\s]+\)|https?:\/\/[^\s<)]+)/g

function safeUrl(url) {
  return /^https?:\/\//i.test(url) ? url : null
}

function renderInline(text, keyPrefix) {
  return text.split(INLINE).map((token, i) => {
    const key = `${keyPrefix}-${i}`
    if (!token) return null
    if (token.startsWith('**') && token.endsWith('**') && token.length > 4) return <strong key={key}>{token.slice(2, -2)}</strong>
    if (token.startsWith('`') && token.endsWith('`') && token.length > 2) return <code key={key}>{token.slice(1, -1)}</code>
    const image = token.match(/^!\[([^\]]*)\]\(([^)\s]+)\)$/)
    if (image) {
      const src = safeUrl(image[2])
      return src ? <img key={key} className="inline-image" src={src} alt={image[1]} loading="lazy" /> : null
    }
    const link = token.match(/^\[([^\]]+)\]\(([^)\s]+)\)$/)
    if (link) {
      const href = safeUrl(link[2])
      return href ? <a key={key} href={href} target="_blank" rel="noopener noreferrer">{link[1]}</a> : link[1]
    }
    if (/^https?:\/\//.test(token)) return <a key={key} href={token} target="_blank" rel="noopener noreferrer">{token}</a>
    if (token.startsWith('*') && token.endsWith('*') && token.length > 2) return <em key={key}>{token.slice(1, -1)}</em>
    return token
  })
}

function toBlocks(content) {
  const blocks = []
  const push = (block) => {
    const last = blocks[blocks.length - 1]
    if (block.type === 'products' && last?.type === 'products') last.ids.push(...block.ids)
    else if (block.type === 'list' && last?.type === 'list' && last.ordered === block.ordered) last.items.push(...block.items)
    else blocks.push(block)
  }
  for (const rawLine of content.split('\n')) {
    const ids = [...rawLine.matchAll(MARKER)].map((m) => m[1])
    const line = rawLine.replace(MARKER, '').trim()
    if (line) {
      const bullet = line.match(/^(?:[-*•]|(\d+)[.)])\s+(.*)$/)
      if (bullet) push({ type: 'list', ordered: Boolean(bullet[1]), items: [bullet[2]] })
      else push({ type: 'p', text: line })
    } else if (!ids.length && blocks[blocks.length - 1]?.type !== 'gap') {
      push({ type: 'gap' })
    }
    if (ids.length) push({ type: 'products', ids })
  }
  return blocks.filter((b) => b.type !== 'gap')
}

export default function AssistantBubble({ content, streaming, productIds, products, cart, onChoose, onDetails, onMore, t }) {
  const visible = streaming ? content.replace(/\[\[[^\]]*$/, '') : content
  const blocks = toBlocks(visible)
  if (productIds?.length) blocks.push({ type: 'products', ids: productIds })

  const out = []
  let textBlocks = []
  const flushText = () => {
    if (!textBlocks.length) return
    out.push(
      <div className="assistant-bubble" key={`t${out.length}`}>
        {textBlocks.map((block, i) => {
          if (block.type === 'list') {
            const Tag = block.ordered ? 'ol' : 'ul'
            return <Tag key={i}>{block.items.map((item, j) => <li key={j}>{renderInline(item, `${i}-${j}`)}</li>)}</Tag>
          }
          return <p key={i}>{renderInline(block.text, String(i))}</p>
        })}
      </div>,
    )
    textBlocks = []
  }
  for (const block of blocks) {
    if (block.type !== 'products') {
      textBlocks.push(block)
      continue
    }
    flushText()
    const items = [...new Set(block.ids.map((id) => id.toLowerCase()))].map((id) => products[id]).filter(Boolean)
    if (items.length) {
      out.push(<ProductCarousel key={`p${out.length}`} items={items} cart={cart} onChoose={onChoose} onDetails={onDetails} onMore={onMore} t={t} />)
    }
  }
  flushText()
  return <div className="assistant-turn">{out}</div>
}
