# Kapruka ASA — Frontend Design Spec for Stitch

## Overview

Full-screen AI shopping assistant for Kapruka.com. Single-page chat interface where users can ask for product recommendations, search items, and place orders — all through natural conversation.

---

## 1. Brand Colors (from Kapruka.com)

```css
/* Primary palette */
--green:    #1f6b0c;  /* Primary brand green */
--purple:   #402970;  /* Secondary brand — menus, hover, badges */
--gold:     #f8da08;  /* Accent — search btn, highlights */
--red:      #EC1C24;  /* Sale/price accent */

/* Surfaces */
--bg-page:        #ffffff;
--bg-light:       #F5F0FF;  /* Light purple tint */
--bg-surface:     #ffffff;
--bg-hover:       #f0f0f0;
--bg-chat-user:   #1f6b0c;  /* User bubble */
--bg-chat-bot:    #F5F0FF;  /* Assistant bubble */

/* Text */
--text-primary:   #1a1a1a;
--text-secondary: #5f5f5f;
--text-on-green:  #ffffff;
--text-on-gold:   #1a1a1a;

/* Borders */
--border-light:   #e5e5e5;
--border-med:     #d0d0d0;
```

---

## 2. Layout

Full screen, no header/nav. Just the chat interface.

```
┌──────────────────────────────────────┐
│                                        │
│   Kapruka Logo (top center, small)     │
│                                        │
│   ┌────────────────────────────────┐   │
│   │                                │   │
│   │   MessageList                  │   │
│   │   (flex-1, scrollable,         │   │
│   │    padded 16px sides)          │   │
│   │                                │   │
│   │   - Welcome message (bot)      │   │
│   │   - User bubble (right)        │   │
│   │   - Bot bubble (left)          │   │
│   │   - Product cards (inline)     │   │
│   │   - Tool indicator (subtle)    │   │
│   │   - Order confirmation card    │   │
│   │   - Typing indicator           │   │
│   │                                │   │
│   └────────────────────────────────┘   │
│                                        │
│   ┌────────────────────────────────┐   │
│   │   ChatInput                    │   │
│   │   [  Type a message... ] [➤]  │   │
│   └────────────────────────────────┘   │
│                                        │
└──────────────────────────────────────┘
```

- **Width:** 100vw × 100vh
- **Max chat width:** 720px centered
- **Logo:** 95px wide, centered, 12px margin-bottom
- **MessageList:** fills all space above ChatInput
- **ChatInput:** fixed at bottom, 16px padding all sides

---

## 3. Component Specs

### 3A. ChatInput

| Prop | Type | Description |
|------|------|-------------|
| `onSend` | `(text: string) => void` | Called when user sends |
| `disabled` | `boolean` | Disabled while loading |

**States:**
- **Idle:** input placeholder "ඔබට අවශ්‍ය කුමක්ද? / What do you need?" — send button is green `#1f6b0c`
- **Disabled:** input greyed out, send button grey `#d0d0d0` with "..." text
- **Empty:** send button hidden or opacity 0.3

| State | Input | Send Btn |
|-------|-------|----------|
| Empty | Border `#e5e5e5` | Opaque 0.3 |
| Typing | Border `#1f6b0c` | Full opacity, bg `#1f6b0c` |
| Loading | Grey bg, cursor not-allowed | Grey bg, shows "..." |
| Error | Border `#EC1C24` | Enabled |

**Styling:**
- Input: 16px radius, 48px height, 16px horizontal padding
- Button: 40×40px circle, right side of input, flex centered

### 3B. Message — User Bubble

| State | Content |
|-------|---------|
| Normal | White text on `#1f6b0c` bg, right-aligned, 12px radius |
| Long text | Multi-line, wraps, max-width 80% of container |

**Design:** 
- Background `#1f6b0c`, text `#ffffff`
- Border-radius: 16px 16px 4px 16px (asymmetric — points toward user)
- Margin-bottom: 8px
- Padding: 12px 16px
- Font: 15px, regular weight

### 3C. Message — Assistant Bubble

| State | Content |
|-------|---------|
| Normal | Dark text on `#F5F0FF` bg, left-aligned |
| With markdown | Renders links, bold, bullet lists inline |

**Design:**
- Background `#F5F0FF`, text `#1a1a1a`
- Border-radius: 16px 16px 16px 4px (asymmetric — points toward bot)
- Margin-bottom: 8px
- Padding: 12px 16px
- Font: 15px, regular weight
- **Product links** within text should be styled as underlined green `#1f6b0c`

### 3D. Product Card

```
┌──────────────────────────────┐
│ ┌────┐  Product Name         │
│ │img │  LKR 2,500.00         │
│ └────┘  ✅ In Stock          │
│         🔗 View on Kapruka   │
└──────────────────────────────┘
```

**States:**

| State | What shows |
|-------|-----------|
| Normal | Image (64×64, rounded 8px), name (bold), price (green), stock badge, link |
| No image | Grey placeholder `#f0f0f0` with 📦 icon |
| Out of stock | "Out of Stock" in red `#EC1C24` instead of green badge |
| Loading skeleton | Pulsing grey blocks for image + 2 text lines |

**Design:**
- Background `#ffffff`, 1px border `#e5e5e5`, 12px radius
- Padding: 12px
- Margin-bottom: 8px
- Max-width: 100%
- Image: 64×64px, object-fit cover, 8px radius
- Price: `#1f6b0c`, bold
- Link: `#402970`, underline on hover

### 3E. Order Confirmation Card

```
┌──────────────────────────────┐
│   🛒 Order Confirmation      │
│                              │
│   Your order is ready!       │
│                              │
│   ┌────────────────────────┐ │
│   │   Pay via Kapruka Pay  │ │
│   └────────────────────────┘ │
│                              │
│   (link: pay.kapruka.com/…)  │
└──────────────────────────────┘
```

**States:**

| State | Content |
|-------|---------|
| Pending | Grey card, "Preparing order..." spinner |
| Ready | Green card with pay button |
| Paid/Done | Faded green, "✓ Order placed" |

**Design:**
- Background `#ebfae5` (light green), 1px `#1f6b0c` border
- 12px radius, padding 16px
- Button: `#f8da08` gold background, `#1a1a1a` text, bold, full-width, 48px height, 12px radius
- Secondary link: `#402970`, 12px font, centered below button

### 3F. Tool Indicator (while agent searches)

```
🔍 searching products...
```

- Single line, italic, `#5f5f5f`, 13px
- Margin-bottom: 4px
- Animates in with fade

### 3G. Typing Indicator

```
● ● ●
```

- Three dots, bouncing animation
- Color `#1f6b0c`
- Inside assistant bubble style (bg `#F5F0FF`)
- Each dot animates up/down with 0.3s delay stagger

### 3H. Welcome / Empty State

On first load (no messages), show:

```
┌──────────────────────────────┐
│                              │
│     🛍️                       │
│                              │
│  I'm your Kapruka assistant! │
│                              │
│  Try asking:                 │
│  • "I need a birthday gift"  │
│  • "Find me flowers"         │
│  • "What chocolates do       │
│     you have?"               │
│                              │
└──────────────────────────────┘
```

- Centered vertically in MessageList
- Icon: 64px emoji or SVG
- Heading: 18px bold
- Suggestions: 14px, `#5f5f5f`, bullet list

---

## 4. States Per Screen

| State | What renders |
|-------|-------------|
| **Loading (initial)** | Full-screen centered spinner (green `#1f6b0c`) — "Connecting..." |
| **Empty / Welcome** | Welcome card with suggestion list (3H above) |
| **Chatting** | Normal message list + input |
| **Agent searching** | Normal messages + ToolIndicator |
| **Awaiting confirmation** | Messages + OrderConfirmation card |
| **Error (API down)** | Red banner at top: "⚠️ Connection lost. Retrying..." + auto-retry |
| **Error (bad request)** | Inline red text: "Something went wrong. Please try again." |

---

## 5. useChat Hook (for reference)

```js
const { messages, sendMessage, isLoading, clearMessages } = useChat(sessionId?)

// messages: Array<{ role: "user"|"assistant"|"tool", content, tool?, args? }>
// sendMessage(text) → void (fires SSE stream)
// isLoading: boolean
// clearMessages() → void
```

The hook is already built — consume it directly.

---

## 6. Example Conversation Flow

```
User: "I need flowers for my wife's birthday"

1. [ToolIndicator] 🔍 Searching products...
2. [Bot Bubble]  "Aiyo happy birthday to her! 🎂 
                  Here are some flowers I'd recommend:

                  🌹 Red Rose Bouquet — LKR 3,500
                  View on Kapruka

                  🌷 Mixed Tulips — LKR 4,200
                  View on Kapruka

                  Would you like me to order any of these?"

3. User: "Yes, the rose bouquet"

4. [ToolIndicator] 🔍 Checking delivery...
5. [Bot Bubble]  "Great choice! Let me check if we 
                  can deliver to your area..."

6. [Order Confirmation Card]
   ┌──────────────────────────┐
   │   🛒 Order Confirmation  │
   │                          │
   │   [  Pay via Kapruka  ]  │
   └──────────────────────────┘
```

---

## 7. Responsive Breakpoints

| Breakpoint | Layout |
|------------|--------|
| ≥ 768px | Chat max-width 720px, centered |
| < 768px | Full width, 12px padding |
| < 400px | Smaller bubbles, 14px font |

---

## 8. Files to Create/Modify

| File | Purpose |
|------|---------|
| `src/App.jsx` | Shell — MessageList + ChatInput |
| `src/App.css` | All styles (or CSS modules) |
| `src/components/MessageList.jsx` | Scrollable message container |
| `src/components/ChatInput.jsx` | Text input + send button |
| `src/components/UserBubble.jsx` | User message bubble |
| `src/components/AssistantBubble.jsx` | Bot message bubble |
| `src/components/ProductCard.jsx` | Product display card |
| `src/components/OrderCard.jsx` | Order confirmation card |
| `src/components/ToolIndicator.jsx` | "searching..." indicator |
| `src/components/TypingIndicator.jsx` | Animated dots |
| `src/components/WelcomeScreen.jsx` | Initial empty state |
| `src/hooks/useChat.js` | Already exists — no change needed |

The `useChat` hook is already implemented. Import and use it.
