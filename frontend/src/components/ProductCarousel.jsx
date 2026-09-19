import ProductCard from './ProductCard'

export default function ProductCarousel({ items, cart, onChoose, onDetails, onMore, t, skeleton = 0 }) {
  const inCart = new Set((cart?.items || []).map((line) => line.product_id.toLowerCase()))
  const cards = skeleton ? Array.from({ length: skeleton }, () => null) : items

  return (
    <div className={`product-grid${cards.length > 1 ? ' carousel' : ''}`}>
      {cards.map((product, i) => (
        <ProductCard
          key={product?.id || i}
          product={product}
          wide={cards.length === 1}
          inCart={product ? inCart.has(product.id.toLowerCase()) : false}
          onChoose={onChoose}
          onDetails={onDetails}
          t={t}
        />
      ))}
      {onMore && cards.length > 1 && (
        <button className="product-more" onClick={onMore}>{t.moreOptions}</button>
      )}
    </div>
  )
}
