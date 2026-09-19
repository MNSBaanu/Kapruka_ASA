import { formatMoney } from '../i18n'

export default function ProductCard({ product, inCart, onChoose, onDetails, t, wide = false }) {
  if (!product) {
    return (
      <div className="product-card-skeleton">
        <div className="product-card-skeleton-image" />
        <div className="product-card-skeleton-lines">
          <div className="product-card-skeleton-line" />
          <div className="product-card-skeleton-line" />
        </div>
      </div>
    )
  }

  const inStock = product.in_stock !== false
  const onSale = typeof product.compare_at_price === 'number' && product.compare_at_price > product.price
  const stockLabel = !inStock ? t.outOfStock : product.stock_level === 'low' ? t.lowStock : t.inStock

  return (
    <div className={`product-card${wide ? ' wide' : ''}${inStock ? '' : ' sold-out'}`}>
      <div className="product-card-image-wrap">
        {product.image ? (
          <img className="product-card-image" src={product.image} alt={product.name} loading="lazy" />
        ) : (
          <div className="product-card-image-placeholder">📦</div>
        )}
        {onSale && <span className="product-card-badge">{t.sale}</span>}
      </div>
      <div className="product-card-body">
        <div className="product-card-name" title={product.name}>{product.name}</div>
        <div className="product-card-price">
          {formatMoney(product.price, product.currency)}
          {onSale && <s className="product-card-was">{formatMoney(product.compare_at_price, product.currency)}</s>}
        </div>
        <div className={`product-card-stock ${inStock ? (product.stock_level === 'low' ? 'low-stock' : 'in-stock') : 'out-of-stock'}`}>
          <span className="product-card-stock-dot" />
          {stockLabel}
          {product.variants?.length > 1 && <span className="product-card-options"> · {t.options(product.variants.length)}</span>}
        </div>
        <div className="product-card-actions">
          <button
            className="product-card-btn"
            disabled={!inStock || inCart || !onChoose}
            onClick={() => onChoose(product)}
          >
            {inCart ? t.inOrder : t.choose}
          </button>
          {onDetails && (
            <button className="product-card-link" onClick={() => onDetails(product)}>
              {t.details}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
