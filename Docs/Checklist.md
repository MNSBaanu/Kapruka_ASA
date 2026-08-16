# Implementation Checklist

Audit of the current build against `Docs/AgentChallenge.md`, `Docs/Note.md`, `Docs/MCPServer.md`, `Docs/FrontendInterfaces.md`, and `Docs/Approval.md`.

**Legend:** `FAIL` = broken or unsafe · `GAP` = required / bonus not built · `SHARPEN` = exists but too weak to win.

---

## Status snapshot

| Area | State |
|------|--------|
| Full-screen chat shell | Partial — layout exists, still generic |
| MCP tools wired | All 7 tools callable |
| MCP read cache | Yes — 120s TTL, reads only |
| Guest checkout | Tool exists; confirmation gate is prompt-only |
| Product visuals | Fragile markdown scrape — often no images |
| Personality | Prompt-only; no critic loop, no occasion playbooks |
| Local languages | Prompt instruction only; UI is English |
| Multi-agent / 3-tier memory | Not built (`Session.context` unused) |
| Public hosted demo | Not live |
| Tests | None |

---

## P0 — Failures to fix

These can break a judge demo or create real orders incorrectly.

- [ ] **FAIL — Duplicate user message each turn.** `session.add_message("user", …)` then `_build_history()` includes that message, then `chat.send_message(message)` sends it again. Gemini sees the same user line twice.
- [ ] **FAIL — Tool results not stored in session.** History only keeps user/assistant text. Next turn the model has no product IDs, prices, or images unless they were copied into prose. Reuse / reorder / “the second one” will hallucinate or re-search.
- [ ] **FAIL — Only the first response part is handled.** `candidate.content.parts[0]` drops extra function calls and any text+tool combo. Multi-item carts and parallel tools fail silently.
- [ ] **FAIL — `create_order` validation abort does not loop back to the model.** Issues are dumped to the user and the turn ends. No function-response, no retry, no buddy phrasing.
- [ ] **FAIL — Successful `create_order` skips the assistant reply.** Yields `order_confirmation` and returns. No “here’s your pay link, prices lock 60 min” message; no order number in chat history for reorder.
- [ ] **FAIL — Confirmation is not enforced in code.** Prompt says “confirm first”; nothing in session flags `user_confirmed=true`. Model can still call `create_order` on the first turn.
- [ ] **FAIL — Shared MCP client is not concurrency-safe.** One global `_session_id` and `_request_id` for all users. Parallel chats will collide JSON-RPC ids / MCP session.
- [ ] **FAIL — MCP `tools/call` result likely wrapped.** MCP returns `{content:[{type:text,text:…}]}`. Agent `json.dumps` that blob. Model may not see clean product JSON (ids, images, stock).
- [ ] **FAIL — Product cards depend on markdown scraping.** `parseProductsFromText` needs `**Name**`, `LKR`, stock emoji, optional `![](url)`. Live MCP images almost never reach the UI. Visual richness (20 pts) is at risk.
- [ ] **FAIL — Error banner lies.** Shows “Connection lost. Retrying…” with **no retry**.
- [ ] **FAIL — CORS `allow_origins=["*"]` + `allow_credentials=True`.** Invalid combo; browsers may block.
- [ ] **FAIL — Gemini is not streamed.** Full `send_message` wait → UI sits on typing dots. Conflicts with Dulith “instant” bar.
- [ ] **FAIL — No rate-limit handling.** 60 req/min and 30 orders/hr can 429 with no backoff, no user-facing “slow down”, no queue.
- [ ] **FAIL — `check_delivery` not required before order.** Prompt says never promise delivery without the tool; code does not check.

---

## P1 — Challenge requirements (must-have)

From `Docs/AgentChallenge.md` + `Docs/Approval.md`.

### Experience & polish (30)

- [ ] **GAP — Real Kapruka logo.** Header is SVG text “Kapruka”, not brand mark.
- [ ] **GAP — Initial loading screen.** Spec: full-screen green spinner “Connecting…”. Not implemented.
- [ ] **SHARPEN — Welcome copy is generic.** “I'm your Kapruka assistant!” + three English bullets. Should feel like a buddy (Sinhala/Tanglish greeting, occasion chips).
- [ ] **SHARPEN — Welcome suggestions are not styled as chips.** Spec + `WelcomeScreen` use a bullet list with inline button styles.
- [ ] **GAP — No new-chat / clear session control.** `clearMessages` exists, unused; server session never reset from UI.
- [ ] **GAP — Empty / error input state.** Spec: error border `#EC1C24`. `has-error` CSS exists, never applied.
- [ ] **SHARPEN — Header vs spec.** Spec: no nav, small centered logo only. Current header is fine-ish but not polished.

### Visual richness (20)

- [ ] **GAP — Structured product events from backend.** Yield `products` (id, name, price, image, stock, url) from `search_products` / `get_product` — do not scrape chat text.
- [ ] **GAP — Cards are not selectable.** “View on Kapruka” sends users **to the website** — opposite of gold standard. Need “This one” / add-to-order in-chat.
- [ ] **GAP — No delivery / tracking visualization.** `track_order` is text-only; Dulith called out timestamped vehicle progress.
- [ ] **GAP — Order card does not show cart, recipient, date, total.** Pay button with unknown MCP payload shape (`pay_url` / `payment_url` / `url`).
- [ ] **SHARPEN — Carousel only if ≥3 parsed products.** 1–2 stay stacked; images often missing so carousel never fires.
- [ ] **GAP — Product skeleton during search.** CSS exists; never shown while `search_products` runs.

### Personality (15)

- [ ] **SHARPEN — Personality is system prompt only.** No few-shot of the “don’t courier the flowers — hand them over” beat. Easy to regress to catalog bot.
- [ ] **GAP — No critic / self-reflect loop** before user-facing text (tone, honesty, no invented prices).
- [ ] **GAP — No occasion playbooks** (Avurudu, birthday, apology, corporate, grocery reorder).
- [ ] **GAP — Tamil not in prompt or UI** (Approval + interview: significant call-center volume).

### Usefulness (15)

- [ ] **GAP — Constraint-first flow not coded.** Budget / date / city not extracted into `Session.context`.
- [ ] **GAP — City alias → canonical city.** `list_delivery_cities` exists but no dedicated resolve step before `check_delivery`.
- [ ] **GAP — Perishable warnings** (cake / flower / combo) not surfaced as a first-class UI warning.
- [ ] **GAP — Variants / icing_text** in tool schema, no UI or structured collection.
- [ ] **GAP — Reorder flow.** Dulith: #1 underrated lever. No “same as last time”, no saved last `order_number`.

### End-to-end completeness (15)

- [ ] **GAP — Multi-item cart as session object.** Cart lives only inside LLM text; no add/remove UI.
- [ ] **GAP — Delivery-date picker / constraint UX.** Date is free text in chat.
- [ ] **GAP — Gift message capture** as a dedicated step (MCP supports `gift_message` max 300).
- [ ] **GAP — Pre-checkout summary card** (items, city, date, rate, sender, gift note) **before** `create_order` — separate from pay card.
- [ ] **GAP — Post-order: show order number + track.** After pay link, no “track this” affordance.
- [ ] **GAP — Guest checkout field completeness.** Phone format, location_type, instructions optional but unguided.

### Live public URL

- [ ] **GAP — Hosted demo on a domain/subdomain.** `replit.toml` + `run.sh` exist; no public URL in docs. Judges cannot score if it is down.
- [ ] **GAP — Health is `{status:ok}` only.** Does not ping MCP or Gemini. Deploy can be “up” and still dead.
- [ ] **GAP — Frontend `dist` not guaranteed in git.** Production depends on `run.sh` build; local `main.py` 404s `/` if dist missing.

### Creativity (5)

- [ ] **GAP — Nothing unexpected yet.** No ministry-of-agents, no memory tiers, no tracking timeline, no situational gift advisor beyond a prompt.

---

## P1 — Bonus targets (challenge + Approval)

- [ ] **GAP — Multi-item carts** (session cart + MCP `cart[]` 1–30).
- [ ] **GAP — Delivery-date constraints** (quote, next available, perishable).
- [ ] **GAP — Gift messaging** (prompt + confirm + pass through).
- [ ] **GAP — Tanglish conversation** (examples + eval; not just “match the user”).
- [ ] **GAP — Sinhala** (welcome, chips, order summary, errors — not English UI with Sinhala placeholder only).
- [ ] **GAP — Tamil** (at least detect + reply; bonus beyond listed items).

---

## P1 — Architecture vs `Docs/Note.md`

- [ ] **GAP — Orchestrator + specialists.** Single Gemini ReAct loop. Note: 3–5 agents (discovery, gift, delivery, checkout, critic).
- [ ] **GAP — 3-tier cognitive memory.**
  - Working: current constraints (budget, city, date, recipient) — `Session.context` unused.
  - Episodic: this chat — truncated text only, no tools.
  - Semantic: occasion rules / gift norms — missing.
- [ ] **GAP — Semantic routing.** No intent router (gift vs grocery vs track vs reorder).
- [ ] **GAP — Self-reflecting safety loop.** No second pass for stock, delivery, tone, PII.
- [ ] **SHARPEN — Cache TTL 120s vs MCP 30 min reads.** Cache more aggressively; never cache `create_order` / `track_order` (already excluded). Consider short TTL for `check_delivery`.
- [ ] **GAP — Memory write-back** after each turn (rejected SKUs, preferred language).
- [ ] **GAP — Human-in-the-loop confirm UI** (Yes / Edit buttons), not only chat “yes”.
- [ ] **GAP — Broad catalog, not gifts-only.** Welcome + prompt still gift-leaning; add grocery/electronics chips.
- [ ] **OUT OF SCOPE (v1, keep listed):** 100 agents, Global Shop, order edit, voice, account login.

---

## P1 — MCP correctness (`Docs/MCPServer.md`)

- [ ] **SHARPEN — Send `notifications/initialized` after MCP initialize** if the public server requires it.
- [ ] **GAP — Parse MCP content blocks** into JSON/markdown; strip wrappers before the model and UI.
- [ ] **GAP — Respect `RateLimit-*` headers.** Slow down / reuse cache when remaining is low.
- [ ] **GAP — Search pagination.** `cursor` is in schema; no “show more” in UI (cap 3 pages).
- [ ] **GAP — Currency.** Schema supports LKR/USD/…; UI hardcodes `LKR` in `ProductCard`.
- [ ] **GAP — `in_stock_only` default true** for recommendations unless user asks otherwise.
- [ ] **SHARPEN — Do not cache empty/error MCP payloads.** Failed searches currently get cached like hits.

---

## P2 — Frontend spec leftovers (`Docs/FrontendInterfaces.md`)

- [ ] **GAP — Suggestion chips clickable with brand styling** (not unstyled `<button>`).
- [ ] **GAP — Assistant markdown:** lists/links partially handled; images in text not rendered as `<img>`.
- [ ] **GAP — XSS:** `AssistantBubble` uses `dangerouslySetInnerHTML` without sanitizing model output.
- [ ] **GAP — Order pending card** never shown (`orderStatus === 'pending'` never set).
- [ ] **GAP — Order `done` state** after user opens pay link (no callback; at least a “I’ve paid” / fade).
- [ ] **GAP — `html lang="en"` only** — should follow detected language.
- [ ] **SHARPEN — Logo size.** Spec 95px wide; current header text is ~32px tall.
- [ ] **GAP — Auto-retry on API down** (spec).

---

## P2 — Sharpen the system (quality, not new features)

### Agent loop

- [ ] **SHARPEN — Stream tokens** (`generate_content_stream` / chat streaming) so first words appear in <1s.
- [ ] **SHARPEN — Cap tool iterations with a user-visible “still looking”** instead of silent 10-loop then generic sorry.
- [ ] **SHARPEN — Prefer `get_product` after search** so cards have real images/variants.
- [ ] **SHARPEN — Prefetch `list_categories` + common cities** at session start (speed + rate-limit).
- [ ] **SHARPEN — Batch tools** when the API allows (search + city in one turn).
- [ ] **SHARPEN — Model choice.** Default `gemini-1.5-flash-latest` is weak for buddy personality. Consider Flash for routing/tools, stronger model for final reply (Note: ministry of agents / multi-model).
- [ ] **SHARPEN — Few-shot Sinhala/Tanglish** in the system prompt (call-center 60–70% Sinhala).
- [ ] **SHARPEN — Plain language table is in the prompt; UI still says “Pay via Kapruka Pay” / “Order Confirmation”.** Align copy: “continue to delivery”, “ready to pay?”.

### Memory & state

- [ ] **SHARPEN — Persist last order_number in session** after create.
- [ ] **SHARPEN — Persist language preference** after first user message.
- [ ] **SHARPEN — Bound in-memory session store** (TTL + max sessions) or Replit restart wipes all chats (OK) but unbounded dict will leak.
- [ ] **SHARPEN — TTL cache eviction** of expired keys (currently only on `get`).

### UX speed (7 min → ~2 min)

- [ ] **SHARPEN — Batch questions** is prompt-only; add a compact constraint form (who / budget / when / city) as optional chips.
- [ ] **SHARPEN — Smart defaults** (today+1, Colombo if mentioned, qty 1).
- [ ] **SHARPEN — One-tap confirm** on summary card.

### Safety / privacy (Dulith top concern)

- [ ] **SHARPEN — Redact phone/address from logs and client analytics.**
- [ ] **SHARPEN — Do not echo full address in later turns more than needed.**
- [ ] **SHARPEN — Block `create_order` if cart product_ids were never returned by MCP this session.**
- [ ] **SHARPEN — Stock re-check `get_product` immediately before order.**
- [ ] **SHARPEN — Never invent substitutions** (explicit failure mode in interview).

### Ops

- [ ] **GAP — `.env.example` documents GEMINI key; production secret handling on host.**
- [ ] **GAP — `run.sh` uses port 8080; config default 8000.** Document the split (Replit vs local).
- [ ] **GAP — Vite proxy only `/api`; `/health` not proxied in frontend-dev.**
- [ ] **GAP — No tests** (agent order gate, MCP parse, product event shape, cache TTL).
- [ ] **GAP — README Project docs table dropped** (`Note.md`, this checklist). Restore when convenient.

---

## Suggested build order

1. Fix the agent loop (history, parts, MCP parse, persist tool results).
2. Structured product + order events → real cards with images; tap to choose.
3. Hard confirm gate + summary card + `check_delivery` before `create_order`.
4. Session working memory (city, date, budget, cart, language, last order).
5. Sinhala/Tanglish UI + chips; Tamil reply.
6. Reorder via `track_order` + last order number.
7. Critic loop + occasion playbooks (personality that judges will actually feel).
8. Stream tokens, cache/rate-limit, health that pings MCP.
9. Deploy public URL; friend-and-family pass on the apology-flowers scenario.

---

## Out of scope for v1 (do not block submit)

- Voice (Nana / ElevenLabs)
- Global Shop / Amazon–eBay
- Order edit MCP
- Account login / full order history
- 100-agent production mesh
- Public voting / shortlist campaign
