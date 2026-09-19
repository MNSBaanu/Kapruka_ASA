import ProductCarousel from './ProductCarousel'

export default function ToolIndicator({ tool, stillLooking, t }) {
  return (
    <>
      <div className="tool-indicator">
        {stillLooking ? `⏳ ${t.stillLooking}` : t.tools[tool] || `🔍 ${tool}…`}
      </div>
      {tool === 'search_products' && <ProductCarousel skeleton={3} t={t} />}
    </>
  )
}
