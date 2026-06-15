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

## Project docs

**Implementation rule:** Before building or changing features, always read the relevant files in [`Docs/`](Docs/). Cursor enforces this via `.cursor/rules/read-docs-before-implementation.mdc`.

Local reference material in [`Docs/`](Docs/):

| File | Contents |
|------|----------|
| [`Note.md`](Docs/Note.md) | Seed notes — vision, agent design, Dulith interview takeaways |
| [`AgentChallenge.md`](Docs/AgentChallenge.md) | Challenge brief, rubric, timeline, FAQ |
| [`MCPServer.md`](Docs/MCPServer.md) | MCP endpoint, tools, rate limits |
| [`GitHubSource.md`](Docs/GitHubSource.md) | Official MCP server repo — clone, run, test |
| [`Approval.md`](Docs/Approval.md) | Challenge approval and getting-started notes |

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
