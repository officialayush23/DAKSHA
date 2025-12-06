app/
├── __init__.py
├── config.py            # Settings
├── database.py          # Supabase & Redis Setup
├── auth.py              # JWT Security
├── main.py              # Entry Point
├── models/              # Pydantic Schemas
│   ├── __init__.py
│   ├── auth.py
│   ├── user.py
│   ├── commerce.py
│   ├── support.py
│   ├── analytics.py
│   └── channels.py
├── services/            # Business Logic
│   ├── __init__.py
│   ├── ai_service.py
│   ├── user_service.py
│   ├── commerce_service.py
│   ├── support_service.py
│   └── analytics_service.py
├── agents/              # LangGraph AI
│   ├── __init__.py
│   ├── tools.py
│   └── graph.py
└── routers/             # API Endpoints
    ├── __init__.py
    ├── auth.py
    ├── users.py
    ├── profile.py
    ├── commerce.py      # Catalog + Cart + Orders
    ├── support.py
    ├── analytics.py
    ├── feedback.py
    ├── realtime.py      # WebSockets
    └── channels.py      # Omnichannel Agent Entry