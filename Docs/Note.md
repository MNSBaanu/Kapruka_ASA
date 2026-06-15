# Seed Notes — Kapruka Gift-Concierge Agent

Notes from the Dulith Herath / Zuu Crew × Kapruka post, the AEE Bootcamp slide (**Mini Project 03: Gift-Concierge Agent**), and the **Rasal × Dulith Herath** interview on the Kapruka Agent Challenge. For planning only — no build yet.

---

## 1. Source inspiration

| Source | Key idea |
|--------|----------|
| **Zuu Crew × Kapruka post** | Production-grade multi-agent concierges for e-commerce personalization in Sri Lanka |
| **AEE Bootcamp slide** | Focused **Gift-Concierge** agent using **agentic design patterns** + **cognitive memory** |
| **Rasal × Dulith Herath interview** | Founder vision for MCP-powered agents — personality, zero-friction ordering, local languages, future Global Shop |
| **Kapruka ASA (this project)** | Challenge entry: full-screen chat shopping agent on live Kapruka MCP |

These align: the post describes the *architecture vision*; the slide names a *concrete agent type*; the interview states *what Kapruka actually values*; the challenge brief is the *delivery target*.

---

## 2. Dulith Herath interview — challenge takeaways

Full Q&A between **Rasal** and **Dulith Herath** (Founder, Kapruka) on the Kapruka Agent Challenge.

### Origin story

- Dulith saw someone on **LinkedIn** build a Kapruka shopping agent **without official MCP** — that seeded the idea.
- Kapruka was already planning MCP for internal/LLM use; opening it to developers was inspired by community creativity.
- Motivation: have fun, show the power of **skipping order forms** and going fully **agentic** on e-commerce.
- ~**1,000 applications** within the first 48 hours of launch.

### Prize & competition rules

- Grand prize: **Apple M4 Mac Mini** (geek-friendly over cash).
- Possible future option: winner may choose **Mac Mini or Nvidia RTX** by competition end.
- **One person = one entry** — no duplicate submissions (easy to spin variants with AI; unfair).
- Submit a **live public URL on your domain** — not source code. You **retain full code ownership**.
- Kapruka may **offer to acquire/adopt** a standout build later — optional, not default.

### Goal of the challenge

- Kapruka opened its **MCP** so developers build **AI shopping agents**.
- Target: ordering that is **faster, more human-like, and more intuitive** than website checkout.
- **Gold standard:** after one successful order via agent, users **never go back to kapruka.com** — discovery, history, and checkout all live in the agent. If users revert to the website, the agent failed.
- Analogy Dulith uses: **EV car** — once you experience it, you don't want gasoline again.

### What a winning agent looks like

**Personality (most important)**

- Real **human personality** — like talking to your **best buddy**, not a shopping bot.
- Example scenario: user says *"I messed up, wife is angry, need flowers."*
  - **Weak agent:** suggests flower products.
  - **Strong agent:** *"Bro, don't send her flowers — get them yourself and give them to her. That's how you fix this."*
- Personality does **not** come from plugging in the latest model alone — it requires deliberate design.
- Should feel like **good service**, not upselling noise — but thoughtful upselling is still part of commerce.

**Speed & friction**

- Current Kapruka website: ~**7 minutes** average to place an order (new users: 6–7 form steps, addresses, payment).
- Agent target: ~**2 minutes** through conversation.
- Must also be **instant** in responses — users won't tolerate slow AI (like refusing 7-second page loads).
- **Don't rush at the cost of basket value** — fast-track only when it still sells what the customer actually wants.

**UX surface**

- **Full-screen** experience — not a side widget (reference: TouchP-style immersive chat).
- MCP returns **image links** — showcase products visually; avoid walls of text.
- Primary experiences: warm conversation + rich product presentation + frictionless checkout.

**Scope of catalog**

- Kapruka is **gift-heavy** but has **~120,000 products** — clothing, shoes, electronics, marketplace sellers, etc.
- Don't narrow the agent to gifts only; support **broad ordering** while gift scenarios remain a strong wedge.

### What wins (judge priorities)

- **Mix of technical depth + genuine user delight** — engineering taste alone isn't enough.
- Dulith will also test with **friends & family** for a human-usability score component.
- If entries are close: possible **shortlist of ~10**, public demo/voting, LLM credits — still TBD.
- **Innovation over stack** — any LLM/framework; judges don't score by model brand.
- **Local languages** — Sinhala, Tamil, Singlish, Tanglish = major bonus differentiator.

### Local language — why it matters (data-backed)

- Kapruka call center: **60–70%** of callers choose **Sinhala**; significant **Tamil** volume too.
- Website is English-only, but customers need to discuss orders in local language.
- Many users don't recognize words like **"checkout"** — renaming to **"continue to delivery"** improved conversion **~7%**.
- Tanglish/Singlish speakers should place complex orders without decoding English UI jargon.
- Proof point from interview: Tanglish query *"mama box"* correctly resolved to **onions** (not salt) via MCP search — context matters.

### MCP — practical builder notes

- MCP is **basic and straightforward** — essential catalog, delivery, checkout tools; nothing magical.
- **Cache aggressively** to stay under rate limits (60 req/min per IP).
- Need higher limits for complex builds: **reply to your registration email thread** with application number — automated backend can increase limits.
- **During competition (frozen scope):**
  - ✅ `track_order` — detailed delivery progress (vehicle left warehouse, etc.)
  - ❌ Order **edit** — not in MCP until competition ends (no mid-competition feature drops)
- **Security architecture:** public MCP is **layered** — MCP → internal MCP → API → core systems (not direct wire to production DB).
- **Failure modes to guard against:** hallucinated product info, wrong delivery promises, bad substitutions, **privacy leaks**, unauthorized purchases. **Privacy/security = top concern.**

### LLM & architecture strategy

- **Don't assume** latest model (e.g. Opus 4.x) = win.
- Valid approaches:
  - Multiple models on different tasks
  - **"Ministry of agents"** — e.g. open-source workers + superior "boss" orchestrator model
  - Mix cheap/fast models for routing + premium model for personality/checkout
- Rasal's competing entry **"Nana"** (disclosed in interview): text + **voice** (ElevenLabs), friend-like persona — reference only, not our design.

### Reordering — underrated opportunity

- Dulith's pick for biggest AI-solvable shopping problem in Sri Lanka: **easy reordering**.
- Real-world pattern: coffee shop customers order the **same 2 items** daily despite 30 options; e-commerce has same habit (detergent, groceries, repeat gifts).
- Build: *"Same as last time"* via order number + `track_order` + session memory.
- Post-sale experience matters — tracking, status questions, delivery visualization.

### Future vision (post-competition)

- **Global Shop in MCP** — order from Amazon/eBay through Kapruka agent, duty/import handled, delivered locally.
- **Agent-to-agent commerce** — user's personal agent talks to Kapruka's agent to place orders autonomously.
- Design shell/architecture to absorb global catalog later without rewrite.

### Kapruka internal lesson (for our agent design)

- Dulith runs internal work via **agent loops**, not one-off prompts — scheduled check-ins, auto-approved permissions, ~**90% success / 5–10% blunders** acceptable vs human assistant.
- Implication for us: prefer **persistent loops** (reflect → validate → act) over single-shot prompting.

### Three tips for limited-time builders

1. **Replace the website experience** — agent should obviously be the better way to order.
2. **Create "never go back" moments** — EV-car-level switch in UX quality.
3. **Invest in personality and speed together** — not just tools wired to an LLM.

### Practical implications for Kapruka ASA

| Interview signal | Action for our build |
|------------------|----------------------|
| Best-buddy personality | Opinions, humour, situational advice — not product-list bot |
| 7 min → ~2 min | Minimize turns; prefetch delivery/categories; smart defaults |
| Full-screen + visuals | Immersive UI with product cards/carousels from MCP image URLs |
| Broad catalog | Gift-Concierge as hero flow, not only gift SKUs |
| Local languages | Sinhala/Tamil/Tanglish; avoid jargon like "checkout" |
| Cache MCP responses | Server-side cache layer to protect rate limits |
| Reordering | `track_order` + "order again" flow |
| Security & privacy | Confirm before pay; no storing sensitive data unnecessarily |
| Ministry of agents | Small multi-agent split OK; boss + workers pattern |
| MCP scope frozen | No order edit; rich tracking only |
| Domain submission | Deploy public demo URL; we keep all code |

---

## 3. Core concepts from the post (architecture seeds)

### Multi-agent concierges (100+ in production vision)

- Not one monolithic chatbot — specialized agents (search, gift-matching, delivery, checkout, tone/localization).
- For our scope: start with a **small orchestrator + 3–5 specialists**, not 100.

### Live inventory training / grounding

- Agents reason over **real catalog data**, not static prompts.
- Maps directly to Kapruka MCP: `search_products`, `get_product`, `list_categories`.

### Custom agentic orchestration (not drag-and-drop frameworks)

- Hand-rolled routing, state machine, or lightweight orchestrator.
- Fits FastAPI backend + explicit control flow.

### 3-tier cognitive memory

Likely layers (to define when building):

| Tier | Role | Gift-Concierge use |
|------|------|-------------------|
| **Working** | Current turn / session context | "Budget 5k, birthday, Colombo, sister likes flowers" |
| **Episodic** | This conversation history | Prior suggestions rejected, tone preferences |
| **Semantic / long-term** | Stable facts & patterns | Occasion rules, category heuristics, Sri Lankan gift norms |

### Semantic routing

- Route user intent to the right agent/tool by **meaning**, not keywords.
- Examples: "something sweet for amma" → gift agent + cakes category; "when can it arrive?" → delivery agent.

### Self-reflecting safety loops

- Agent checks its own output before acting: price/stock validation, delivery feasibility, order sanity, respectful tone.
- Critical before `create_order` — real money, real orders.

---

## 4. Gift-Concierge agent — product definition

**Primary job:** Turn vague gift intent → confident product + delivery + checkout.

**Typical flow:**

1. Occasion & recipient (birthday, wedding, sympathy, corporate)
2. Constraints (budget, date, city, dietary/perishable)
3. Curate 3–5 options with visuals
4. Refine via conversation
5. Delivery quote + gift message
6. Guest checkout via MCP

**Bonus alignment (challenge rubric):** gift messaging, delivery dates, multi-item carts, Sinhala/Tanglish — all natural for a concierge, not a search box.

**Dulith nuance:** gift scenarios are a great personality showcase, but agent must handle **general shopping** across Kapruka's full catalog (~120k SKUs).

---

## 5. Agent roles (candidate split)

| Agent | Responsibility | MCP tools |
|-------|----------------|-----------|
| **Orchestrator** | Intent, routing, session state | — |
| **Discovery** | Search, categories, compare | `search_products`, `list_categories`, `get_product` |
| **Gift advisor** | Occasion logic, narrowing, personality | Uses discovery output |
| **Delivery** | Cities, dates, perishables | `list_delivery_cities`, `check_delivery` |
| **Checkout** | Cart, recipient, pay link | `create_order` |
| **Critic / safety** | Reflect loop before order | Read-only validation |

---

## 6. Design patterns to study (from slide title)

- **ReAct** — reason → tool call → observe → repeat
- **Plan-and-execute** — plan gift search, then run tools
- **Router** — semantic intent → specialist
- **Memory write-back** — persist constraints after each turn
- **Human-in-the-loop** — confirm before order (UX + safety)

---

## 7. Mapping to existing stack

**Already have:**

- Kapruka MCP (live catalog, delivery, checkout)
- Challenge brief (UI, personality, E2E, hosted demo)
- Backend skeleton (FastAPI)

**Still to decide:**

- Frontend (full-screen immersive chat + product cards — not side widget)
- LLM provider & model (multi-model / ministry-of-agents vs single model)
- MCP response caching layer (rate limit protection)
- Memory store (in-memory session vs Redis/DB)
- Orchestration style (single LLM with tools vs multi-agent)
- Sinhala / Tamil / Tanglish strategy
- Voice interface (optional — competitor "Nana" uses ElevenLabs)

---

## 8. Differentiation angles (creativity + usefulness)

- **Occasion-aware gift playbooks** (Avurudu, birthdays, anniversaries, corporate hampers)
- **Constraint-first UX** ("When do you need it?" before "What do they like?")
- **Visual curation** — carousel of 3 gifts, not a text list
- **Local voice** — warm, witty; Sinhala, Tamil, Singlish, Tanglish without feeling translated (Dulith: major stand-out)
- **Pre-checkout reflection** — "Here's what I'm about to order — correct?" (security + trust)
- **Situational personality** — drunk-husband-flowers scenario: advise like a friend, not a catalog
- **Plain-language checkout** — say "continue to delivery", not "checkout"
- **Instant responses** — sub-second feel where possible; ~2 min total order time target
- **Reorder in one message** — "Same as last time" via `track_order` (Dulith: #1 underrated commerce lever)

---

## 9. Non-goals (for v1)

- 100 agents / full Zuu Crew scale
- Custom inventory training pipeline (MCP is enough)
- No-code orchestration platforms
- Account login / full order history (but **reorder via order number** is in scope)
- Global Shop / Amazon-eBay orders (future MCP — note for v2)
- Order edit/cancel via MCP (not available during competition)
- Voice UI (optional v2 — not required for win)

---

## 10. Open questions (resolve before build)

1. Single conversational agent with tools, or explicit multi-agent orchestrator ("ministry of agents")?
2. Where does 3-tier memory live (session only vs persisted)?
3. How much occasion logic is **rules** vs **LLM**?
4. Language scope: Sinhala only, Tamil too, or full Singlish/Tanglish mix?
5. Hosted demo: server-side MCP proxy vs client-side MCP?
6. How deep should **reorder flow** go in v1 (order number only vs saved session preferences)?
7. Server-side MCP cache strategy (TTL, which tools to cache)?
8. Multi-model split: which tasks go to cheap vs premium models?

---

## 11. One-line north star

> **A Gift-Concierge that feels like your Kapruka buddy** — grounded in live inventory, speaks your language, remembers what you said, gets you from "I messed up" to paid order in ~2 minutes, and makes the website feel obsolete.
