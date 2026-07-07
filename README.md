# DAKSHA — Agentic Commerce Platform

DAKSHA is a full-stack e-commerce platform built around a multi-agent AI system. Instead of a single chatbot bolted onto a store, DAKSHA routes every part of the shopping journey — browsing, cart, checkout, payments, delivery, loyalty, support, and post-purchase — through a graph of specialized LLM agents that can hand off to one another and to human support when needed.

## What it is

DAKSHA is a monorepo with two parts:

- **BACKEND** — a Python/FastAPI service that exposes the commerce API (products, cart, checkout, orders, payments, loyalty, coupons, stores, kiosk mode) and hosts the agentic AI layer built on LangGraph.
- **daksha-frontend** — a React 19 + Vite single-page app that serves the storefront, user dashboard, kiosk UI, and two separate admin panels (global admin and per-user admin).

The AI layer uses a supervisor/handoff pattern: a router directs each user message to the right specialized agent, agents can call tools against the backend's services, and conversations can be escalated to a human via a WebSocket handoff channel.

## Capabilities

**Agentic AI (LangGraph + Gemini/Groq)**
- Supervisor routing across dedicated agents: cart, checkout, payment, delivery, inventory, loyalty, offers, recommendations, support, and post-purchase.
- A unified agent mode plus per-domain agents, each with their own tool set (checkout tools, inventory tools, loyalty tools, order tools, recommendation tools, support tools, user tools).
- Company policy and business-rule modules (checkout rules, discount rules, inventory rules, support rules) that constrain agent behavior.
- Conversation state, context loading, and message-history management, with Postgres-backed checkpointing (`langgraph-checkpoint-postgres`) so conversations persist across sessions.
- Human handoff over WebSocket when an agent can't resolve a request.
- Telegram bot integration as an additional chat channel.

**Commerce backend**
- Product catalog with semantic search and embeddings (Nomic embeddings, pgvector-style similarity).
- Cart, checkout (multi-step state machine: cart validation → stock reservation → price lock → coupon → payment → delivery scheduling → confirmation), and order management.
- Payments with pluggable gateway configuration, and delivery/pickup fulfillment with courier webhook support and live tracking.
- Personalized recommendations combining content-based, collaborative, trend, and intent-match scoring.
- Loyalty points, coupons, and personalized offers.
- Store locator with Google Maps and Mapbox geocoding, kiosk mode for in-store devices.
- Email notifications (SMTP or Resend) and in-app notifications.
- Admin APIs for global platform administration and per-user administration, including agent-run tracing for debugging AI conversations.
- Session TTL cleanup and Redis-backed caching/session storage.
- Auth via Supabase (JWT-based), with role-based access (user/admin).

**Frontend**
- Public storefront: landing page, shop, product detail, cart, checkout, wishlist, returns, orders, profile, auth.
- Embedded AI chat interface for shopping assistance.
- Kiosk mode with its own routes, layout, and context for in-store terminals.
- Two admin dashboards (admin and admin_user) built with a sidebar layout.
- Store picker with both Google Maps and Mapbox implementations.
- UI built on Tailwind CSS v4, Radix UI / shadcn-style primitives, Ant Design, Framer Motion/GSAP animations, and React Three Fiber for 3D elements.

## Tech stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI (Python 3.11) |
| AI orchestration | LangGraph, LangChain, Gemini (Vertex AI), Groq |
| Database | PostgreSQL via Supabase (SQLAlchemy ORM), Redis for caching/sessions |
| Embeddings | Nomic (text + vision) |
| Task queue | Celery |
| Frontend framework | React 19, Vite 7 |
| Frontend styling | Tailwind CSS v4, Radix UI, Ant Design |
| Maps | Google Maps API, Mapbox GL |
| Auth | Supabase Auth (JWT) |
| Deployment | Render (backend), Vercel (frontend) |

## Repository layout

```
DAKSHA-/
├── BACKEND/
│   ├── app/
│   │   ├── ai/                # LangGraph agents, tools, policy, routing
│   │   │   ├── agents/
│   │   │   ├── tools/
│   │   │   ├── rules/
│   │   │   └── policy/
│   │   ├── api/routers/       # FastAPI route handlers
│   │   ├── services/          # Business logic
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── core/              # Config, auth, database, redis
│   │   ├── integrations/      # Telegram, etc.
│   │   └── main.py            # FastAPI app entrypoint
│   ├── requirements.txt
│   ├── render.yaml            # Render deployment config
│   └── .env.example
└── daksha-frontend/
    ├── src/
    │   ├── pages/              # Storefront pages
    │   ├── admin/               # Global admin panel
    │   ├── admin_user/          # Per-user admin panel
    │   ├── kiosk/                # Kiosk mode
    │   ├── components/         # Shared UI components
    │   ├── layout/               # Page layouts
    │   ├── context/             # React context (auth, etc.)
    │   └── lib/                  # API clients (main, admin, kiosk)
    ├── package.json
    └── .env.example
```

## Installation

### Prerequisites

- Python 3.11
- Node.js 18+ and npm
- A Supabase project (Postgres database + Auth)
- Redis instance
- API keys: Google Gemini/Vertex AI, Groq, Google Maps, Nomic, and optionally Mapbox, Resend/SMTP, Telegram bot token

### Backend setup

```bash
cd BACKEND
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in DATABASE_URL, SUPABASE_*, GEMINI/GROQ keys, REDIS_URL, etc.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`, with a health check at `/health`.

### Frontend setup

```bash
cd daksha-frontend
npm install
cp .env.example .env             # set VITE_API_URL, VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_GOOGLE_MAPS_API_KEY
npm run dev
```

The app will be available at `http://localhost:5173` (Vite default) and is configured to talk to the backend at `VITE_API_URL`.

### Environment variables

Both `BACKEND/.env.example` and `daksha-frontend/.env.example` list every variable required. At minimum you'll need:

- `DATABASE_URL` / `LANGGRAPH_DB_URL` — Supabase Postgres connection strings (pooled, transaction and session mode respectively)
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`
- `GEMINI_VERTEX_API_KEY` / `VERTEX_API_KEY`, `VERTEX_AI_LOCATION` — for the primary LLM
- `GROQ_API_KEY` — secondary/fallback LLM provider
- `GOOGLE_MAPS_API_KEY` — store locator and delivery
- `REDIS_URL` — caching and session storage
- `NOMIC_API_KEY` — embeddings for search/recommendations

### Deployment

- The backend ships with a `render.yaml` for one-click deployment to Render (`uvicorn` behind a health check at `/health`).
- The frontend includes a `vercel.json` for deployment to Vercel.

## License

See [LICENSE](./LICENSE).
