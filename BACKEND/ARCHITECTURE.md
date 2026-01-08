# Backend Architecture - Agentic Commerce Platform

## Structure

```
app/
├── core/           # Core infrastructure (auth, config, database, rbac)
├── models/        # Database models (all_models.py only)
├── schemas/       # Request/Response DTOs (schemas.py)
├── services/      # Business logic services
├── routers/       # FastAPI route handlers
├── agents/        # LangGraph agent implementation
└── workers/       # Background workers
```

## Key Principles

1. **Separation of Concerns**
   - Models = Database structure (all_models.py)
   - Schemas = API contracts (schemas.py)
   - Services = Business logic
   - Routers = HTTP endpoints

2. **Single Source of Truth**
   - All DB models in `all_models.py`
   - All request/response schemas in `schemas.py`
   - No duplicate models

3. **Core Infrastructure**
   - `core/config.py` - Environment settings
   - `core/database.py` - Supabase & Redis clients
   - `core/auth.py` - JWT authentication
   - `core/rbac.py` - Role-based access control

## Commerce Flow

```
User Request → Router → Service → Database
                ↓
            Agent (if needed)
                ↓
            Tools → Services
```

## Agent Architecture

- **Sales Agent** (`agents/graph.py`) - Main conversational agent
- **Tools** (`agents/tools.py`) - Agent capabilities
  - Search products
  - Recommendations
  - Cart operations
  - Checkout
  - Order tracking
  - Support

## Services

- `commerce_service.py` - Cart, checkout, pricing, allocation
- `user_service.py` - User profile management
- `inventory_service.py` - Inventory operations
- `catalog_service.py` - Product catalog
- `recommendation_service.py` - AI recommendations
- And 20+ more specialized services

## Database Models (Phase 1-6)

All models match the comprehensive DB schema:
- **Phase 1**: Identity, Presence, Conversations
- **Phase 2**: Stores, Warehouses, Inventory
- **Phase 3**: Carts, Orders, Fulfillments
- **Phase 4**: Payments, Wallets, Ledger
- **Phase 5**: Support, Handoffs, Ops
- **Phase 6**: Agents, Recommendations, Promotions

## API Endpoints

### User-Facing
- `/auth/*` - Authentication
- `/users/*` - User profile
- `/cart/*` - Shopping cart
- `/orders/*` - Order management
- `/catalog/*` - Product catalog
- `/channels/message` - Agent chat

### Admin
- `/admin/catalog/*` - Catalog management
- `/admin/inventory/*` - Inventory management
- `/admin/support/*` - Support tickets
- `/admin/warehouse/*` - Warehouse operations

## Next Steps

See `MISSING_FEATURES.md` for implementation gaps.
