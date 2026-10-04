# DAKSHA — Agentic Commerce Platform

DAKSHA is a full-stack e-commerce platform built around a multi-agent AI system. Instead of a single chatbot bolted onto a store, DAKSHA routes every part of the shopping journey — browsing, cart, checkout, payments, delivery, loyalty, support, and post-purchase — through a graph of specialized LLM agents that can hand off to one another and to human support when needed.

## What it is

DAKSHA is a monorepo with two parts:

- **BACKEND** — a Python/FastAPI service that exposes the commerce API (products, cart, checkout, orders, payments, loyalty, coupons, stores, kiosk mode) and hosts the agentic AI layer built on LangGraph.
- **daksha-frontend** — a React 19 + Vite single-page app that serves the storefront, user dashboard, kiosk UI, and two separate admin panels (global admin and per-user admin).

The AI layer uses a supervisor/handoff pattern: a router directs each user message to the right specialized agent, agents can call tools against the backend's services, and conversations can be escalated to a human via a WebSocket handoff channel.

## Capabilities

**Agentic orchestration (LangGraph, `BACKEND/app/agentic/`)**

A cyclic LangGraph `StateGraph` in which a planner splits each request into steps,
specialist agents reason and act in a loop, a policy gate checks every action before
it runs, and a human can approve or reject anything risky:

```
START → ingest → guard ─┬─ handoff ─────────────────────────────┐
                        └─ planner → dispatch ─┬─ synthesize → remember → END
                                     ▲          │
                                  reflect ◄── agent_<name> ⇄ policy_gate ⇄ human_approval (interrupt)
                                     ▲          │                 │
                                     └──────────┴──── execute ◄───┘
```

- **8 specialist agents** (discovery, cart, checkout, offers, fulfillment, post-purchase,
  support, engagement), each with its own scoped tools and its **own long-term memory**
  (`agent_memories`, one namespace per agent and customer).
- **Unified customer context** rebuilt every turn from the database (profile, tier, points,
  the single shared cart, open checkout, orders, returns, offers, addresses, kiosk store,
  open handoff), so web/PWA, kiosk and Telegram see the same customer.
- **Policy gate + HITL**: rules from `company_policy.py` run as code before a tool executes
  (deny, allow, or ask the customer / staff). Paused runs are checkpointed in Postgres and
  resume when someone decides (`/chat/approvals/{id}`, `/admin/agentic/approvals`).
- **Identity binding**: tools never take a user id from the model; the engine injects it.
  Money is never a tool argument; discounts and totals are computed server-side.
- **Proactive automation**: abandoned carts, wishlist nudges, post-delivery feedback and pickup
  reminders run through the same graph in proactive mode; marketing messages need staff approval.
- **Domain-agnostic engine**: `agentic/core` knows nothing about shopping. A domain is a pack of
  agents + tools + policies + a context loader (`agentic/commerce/pack.py`).
- **Model gateway**: Gemini 3.5 Flash with fallback models on rate limits, optional Bedrock (xAI
  Grok) fallback, schema-validated JSON output with one self-correction retry.

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
| AI orchestration | LangGraph (cyclic graph, Postgres checkpoints), Gemini 3.5 Flash, optional Bedrock xAI |
| Database | PostgreSQL via Supabase (SQLAlchemy ORM, pgvector, PostGIS); Redis optional |
| Embeddings | Nomic (text + vision) |
| Task queue | Celery |
| Frontend framework | React 19, Vite 7 |
| Frontend styling | Tailwind CSS v4, Radix UI, Ant Design |
| Maps | Mapbox (GL JS + Geocoding/Search Box) |
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

### Database migrations and checks

```bash
cd BACKEND
python migrations/apply_migrations.py          # all, idempotent (v7 = agentic core, v8 = schema drift fixes)
python scripts/check_schema_drift.py           # models.py vs live database
python scripts/smoke_keys.py                   # every external key/service, no secrets printed
python scripts/e2e_live.py                     # full customer journey against the real stack
python -m pytest tests                         # engine tests (scripted model, no network)
```

### Deployment

- The backend ships with a `render.yaml` for one-click deployment to Render (`uvicorn` behind a health check at `/health`).
- The frontend includes a `vercel.json` for deployment to Vercel.

## License

See [LICENSE](./LICENSE).
