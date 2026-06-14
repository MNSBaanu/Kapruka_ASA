# Kapruka MCP Server

Plug any LLM into Sri Lanka's largest local e-commerce enterprise.

A free public MCP server for Kapruka.com. Search products, browse categories, quote delivery, create guest-checkout orders with click-to-pay links, and track existing orders — from Claude, ChatGPT, Cursor, or any MCP-aware client.

## MCP endpoint

```
https://mcp.kapruka.com/mcp
```

- **Transport:** Streamable HTTP
- **Auth:** No auth required
- **Rate limits:** 60 requests / min per IP · 30 orders / hour per IP

## Quick start

Drop one snippet into your client, restart, done.

Supported clients: Claude Desktop · Cursor · ChatGPT · MCP Inspector

```json
{
  "mcpServers": {
    "kapruka": {
      "url": "https://mcp.kapruka.com/mcp"
    }
  }
}
```

**Cursor:** Settings → MCP → Add new server, or paste into `~/.cursor/mcp.json`.

## Available tools

Seven tools for product discovery, delivery quoting, guest checkout, and order tracking — all return structured results in markdown or JSON.

### 🔍 kapruka_search_products

Search the catalog by keyword with category, price range, stock, and sort filters. Pagination capped at 3 pages.

| Parameter | |
|-----------|---|
| `q` | |
| `category` | |
| `min_price` | |
| `max_price` | |
| `in_stock_only` | |
| `sort` | |
| `limit` | |
| `cursor` | |
| `currency` | |

### 📦 kapruka_get_product

Full details for any product by ID — name, price, stock, variants, images, shipping, and a direct URL.

| Parameter | |
|-----------|---|
| `product_id` | |
| `currency` | |

### 🗂️ kapruka_list_categories

Top-level category names with browse URLs — pass any name as the category filter to search.

| Parameter | |
|-----------|---|
| `depth` | |

### 📍 kapruka_list_delivery_cities

Search Kapruka's delivery network by canonical name or vernacular alias. Returns up to 50 matches per query.

| Parameter | |
|-----------|---|
| `query` | |
| `limit` | |

### 🚚 kapruka_check_delivery

Check whether an order can be delivered to a city on a given date, with the flat LKR rate and a perishable warning when the product code is a cake / flower / combo.

| Parameter | |
|-----------|---|
| `city` | |
| `delivery_date` | |
| `product_id` | |

### 🛒 kapruka_create_order

Create a guest-checkout order and return a click-to-pay URL — no Kapruka account required. Prices are locked for 60 minutes, multi-currency, capped at 30 orders/hr per IP.

| Parameter | |
|-----------|---|
| `cart` | |
| `recipient` | |
| `delivery` | |
| `sender` | |
| `gift_message` | |
| `currency` | |

### 📦 kapruka_track_order

Look up status, recipient, items, and timestamped delivery progress for any Kapruka order. Customer reads the order number off their confirmation email or order complete page.

| Parameter | |
|-----------|---|
| `order_number` | |

## Free tier limits

- **60 requests per minute** per client IP across all tools. Standard `RateLimit-*` headers on every response.
- **30 `kapruka_create_order` calls per hour** per client IP, on top of the per-minute cap.
- **Guest checkout** — orders create a 60-minute click-to-pay link with locked prices. Customer pays in the browser without logging in.
- **Server-side cache** of up to 30 minutes for product / category reads — write endpoints are never cached.

Need higher limits, agent partnerships, or commercial integrations? Reach out at **hello@kapruka.com**.

## Source code

- **GitHub:** [github.com/kapruka/mcp](https://github.com/kapruka/mcp)
- **Clone:** `https://github.com/kapruka/mcp.git`
