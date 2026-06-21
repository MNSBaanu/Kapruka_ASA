export default function ProductCard({ product }) {
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

  const hasImage = product.image && product.image !== ''
  const inStock = product.stock !== false && product.stock !== 'Out of Stock'
  const price = product.price
    ? `LKR ${Number(product.price).toLocaleString('en-LK')}`
    : ''

  return (
    <div className="product-card">
      {hasImage ? (
        <img
          className="product-card-image"
          src={product.image}
          alt={product.name}
          loading="lazy"
        />
      ) : (
        <div className="product-card-image-placeholder">📦</div>
      )}
      <div className="product-card-info">
        <div className="product-card-name">{product.name}</div>
        {price && <div className="product-card-price">{price}</div>}
        <div className={`product-card-stock ${inStock ? 'in-stock' : 'out-of-stock'}`}>
          {inStock ? '✅ In Stock' : '❌ Out of Stock'}
        </div>
        {product.url && (
          <a
            className="product-card-link"
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            🔗 View on Kapruka
          </a>
        )}
      </div>
    </div>
  )
}
