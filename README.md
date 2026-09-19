# Kapruka ASA

AI shopping agent for the [Kapruka Agent Challenge 2026](https://mcp.kapruka.com) — a full-screen, conversational commerce experience built on Sri Lanka's largest e-commerce platform.

**Applicant:** PSFW7 · **Submission deadline:** 30 June 2026

## Overview

Kapruka ASA is a hosted shopping agent that helps customers discover products, check delivery, and complete guest checkout through natural conversation. The goal is not a search box in chat form — it should feel human, helpful, and visually rich, with real personality and local flavour.

Built on the free, public Kapruka MCP — live products, live delivery quotes, and live guest checkout. No API key required.

## Quick start

### MCP endpoint

```
https://mcp.kapruka.com/mcp
```

Add to Cursor (`Settings → MCP → Add new server`, or `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "kapruka": {
      "url": "https://mcp.kapruka.com/mcp"
    }
  }
}
```

### Resources

| Resource | Link |
|----------|------|
| MCP docs & tools | [mcp.kapruka.com](https://mcp.kapruka.com) |
| MCP source code | [github.com/kapruka/mcp](https://github.com/kapruka/mcp) |
| Kapruka store | [kapruka.com](https://kapruka.com) |

## MCP tools

| Tool | Purpose |
|------|---------|
| `kapruka_search_products` | Search catalog by keyword, category, price, stock |
| `kapruka_get_product` | Full product details by ID |
| `kapruka_list_categories` | Browse top-level categories |
| `kapruka_list_delivery_cities` | Search delivery network by city or alias |
| `kapruka_check_delivery` | Quote delivery date, rate, and perishable warnings |
| `kapruka_create_order` | Guest checkout with click-to-pay link |
| `kapruka_track_order` | Order status and delivery progress |

Rate limits: 60 requests/min per IP · 30 orders/hour per IP.

## What we're building

- Full-screen chat UI — polished, immersive, not a corner widget
- Visual product cards — images, carousels, rich results
- Personality — warm, witty, opinionated; Sinhala / Tanglish support
- End-to-end flow — discovery through delivery details to checkout
- Public hosted demo — reliable URL for judges and users

**Bonus targets:** multi-item carts, delivery-date handling, gift messaging, Sinhala language support.

## Run it

**Backend** (Python 3.11+):

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # then set GEMINI_API_KEY
python -m app.main          # http://localhost:8000 (APP_PORT)
```

**Frontend** (Node 20+), in a second terminal:

```bash
cd frontend
npm install
npm run dev                 # proxies /api and /health to :8000
```

**Production / hosting:** `bash run.sh` installs deps, builds `frontend/dist`, and serves everything from FastAPI on `$PORT` (default 8080, which `replit.toml` maps). Set `GEMINI_API_KEY` in the host's secrets panel, not in a committed file. `/health` pings both the Kapruka MCP and Gemini.

**Tests:** `cd backend && python -m unittest discover -s tests -t .`

> The Gemini free tier allows only a few requests per minute and each chat turn uses 2-4 model calls. Use a billed key for a public demo.

## How it works

| Piece | Where | What it does |
|-------|-------|--------------|
| Router | `backend/app/core/router.py` | Detects language (Sinhala, Tamil, Singlish, Tanglish, English), intent and occasion; picks the lead specialist and playbook |
| Specialists & playbooks | `backend/app/prompts/` | Shopper, gift concierge, logistics, checkout and support instructions; occasion knowledge (semantic memory) |
| Agent loop | `backend/app/core/agent.py` | Streaming Gemini tool loop with parallel tool calls and full tool history (episodic memory) |
| Tools | `backend/app/core/actions.py` | Kapruka MCP tools plus `remember` (working memory), `update_cart`, `prepare_order`, `place_order`, `reorder` |
| Critic | `backend/app/core/critic.py` | Checks every reply for invented prices, unknown products, unmentioned stock-outs, unchecked delivery promises and phone numbers; rewrites or re-runs tools when needed |
| MCP client | `backend/app/mcp/` | Streamable HTTP client (`params`-wrapped arguments, JSON responses), rate-limit aware, cached reads |
| Chat UI | `frontend/src/` | Product cards and carousels, cart bar, order summary with one-tap confirm, pay card, delivery and tracking cards, EN / සිං / தமிழ் UI |

Orders are safe by construction: only products Kapruka returned can go in the cart, `prepare_order` re-checks stock, price and delivery for every item, and `place_order` only runs after the customer confirms the summary in a later message or taps **Yes, place order**.


## Scoring rubric (100 pts)

| Category | Points |
|----------|--------|
| Experience & polish | 30 |
| Visual richness | 20 |
| Personality | 15 |
| Usefulness | 15 |
| End-to-end completeness | 15 |
| Creativity | 5 |

---

© 2026 Kapruka Agent Challenge · [MCP docs](https://mcp.kapruka.com) · [GitHub](https://github.com/kapruka/mcp)
