export default function ToolIndicator({ tool }) {
  const labels = {
    search_products: '🔍 Searching products...',
    get_product: '🔍 Getting product details...',
    list_categories: '📂 Browsing categories...',
    list_delivery_cities: '📍 Checking delivery cities...',
    check_delivery: '🚚 Checking delivery...',
    create_order: '🛒 Placing order...',
    track_order: '📦 Tracking order...',
  }

  return (
    <div className="tool-indicator">
      {labels[tool] || `🔍 ${tool}...`}
    </div>
  )
}
