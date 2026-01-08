# Backend Refactoring Plan - Agentic Commerce Platform

## 🎯 Goal
Transform the backend into a production-grade Agentic Commerce Platform with:
- Unified models/schemas matching the complete DB schema
- Clean architecture: `app -> (core, models, services, schemas, agents, workers)`
- Multi-agent orchestration support
- UI-friendly APIs
- Zero breaking changes to functionality

## 📋 Current State Analysis

### Existing Structure
```
BACKEND/app/
├── auth.py (re-export, to be removed)
├── config.py (move to core/)
├── database.py (move to core/)
├── core/
│   ├── auth.py ✓
│   ├── rbac.py ✓
│   └── redis_bus.py ✓
├── models/ (13 files - consolidate to all_models.py)
├── domains/ (DELETE - migrate to services/routers)
├── services/ (25 files - keep, update imports)
├── routers/ (keep, update imports)
├── agents/ (keep, update imports)
└── workers/ (keep, update imports)
```

### Issues Identified
1. ❌ Models scattered across 13 files
2. ❌ No schemas folder (request/response models mixed with DB models)
3. ❌ `domains/` folder duplicates `services/` and `routers/`
4. ❌ `auth.py`, `config.py`, `database.py` not in `core/`
5. ❌ Models don't fully match the comprehensive DB schema provided
6. ❌ Missing models for Phase 1-6 (identity, presence, conversations, agents, etc.)

## 🔄 Refactoring Steps

### Phase 1: Create Consolidated Models & Schemas
1. **Create `app/models/all_models.py`**
   - Consolidate all existing models
   - Add missing models matching DB schema:
     - Phase 1: Users, Identities, Presence, Conversations, Behavioral Events, User Facts, Embeddings
     - Phase 2: Fulfillment Locations, Stores, Warehouses, Zones, Bins, Products, Variants, Inventory
     - Phase 3: Carts, Orders, Order Items, Fulfillments, Returns
     - Phase 4: Payments, Wallets, Ledger Entries, Refunds
     - Phase 5: Ops Users, Support Tickets, Handoffs, Overrides
     - Phase 6: Agents, Agent Runs, Proposals, Orchestration, Commits

2. **Create `app/schemas/schemas.py`**
   - Request models (AddToCartRequest, CheckoutRequest, etc.)
   - Response models (UserProfileResponse, OrderResponse, etc.)
   - UI-friendly DTOs

### Phase 2: Move Core Files
1. Move `config.py` → `core/config.py`
2. Move `database.py` → `core/database.py`
3. Delete `auth.py` (re-export, not needed)
4. Update all imports

### Phase 3: Migrate & Delete Domains
1. Review `domains/` code
2. Migrate unique logic to `services/`
3. Ensure routers use services (not domain repos)
4. Delete `domains/` folder

### Phase 4: Update All Imports
1. Update all `from app.models.*` → `from app.models.all_models`
2. Update all `from app.config` → `from app.core.config`
3. Update all `from app.database` → `from app.core.database`
4. Update all `from app.auth` → `from app.core.auth`
5. Add `from app.schemas.schemas import *` where needed

### Phase 5: Add UI-Friendly APIs
1. Add pagination helpers
2. Add filtering/sorting utilities
3. Add response wrappers (success/error)
4. Add batch operations where needed

### Phase 6: Verify DB Schema Alignment
1. Ensure all enums match DB enums
2. Ensure all table models match DB tables
3. Ensure all relationships match DB foreign keys
4. Add missing indexes/constraints documentation

## 📁 Target Structure

```
BACKEND/app/
├── __init__.py
├── main.py
├── core/
│   ├── __init__.py
│   ├── auth.py (JWT, user extraction)
│   ├── auth_optional.py
│   ├── config.py (Settings from .env)
│   ├── database.py (Supabase client, Redis)
│   ├── rbac.py (Role-based access control)
│   └── redis_bus.py (Event bus)
├── models/
│   ├── __init__.py
│   └── all_models.py (ALL database models matching schema)
├── schemas/
│   ├── __init__.py
│   └── schemas.py (Request/Response DTOs)
├── services/
│   └── [25 service files - keep as-is, update imports]
├── routers/
│   └── [all router files - keep as-is, update imports]
├── agents/
│   ├── graph.py
│   └── tools.py
└── workers/
    └── reservation_cleanup.py
```

## ✅ Success Criteria

1. ✅ All models consolidated in `all_models.py`
2. ✅ All schemas in `schemas/schemas.py`
3. ✅ Core files in `core/`
4. ✅ `domains/` folder deleted
5. ✅ All imports updated
6. ✅ All models match DB schema
7. ✅ No functionality broken
8. ✅ APIs are UI-friendly
9. ✅ Frontend connectivity verified

## 🚨 Critical Rules

1. **Never break existing functionality**
2. **All DB models must match provided schema exactly**
3. **All enums must match DB enums**
4. **No demo code - production-grade only**
5. **Preserve all existing business logic**
6. **Update tests if they exist**

## 📝 Next Steps After Refactoring

1. Add missing RPC functions matching DB schema
2. Implement agent orchestration layer
3. Add comprehensive error handling
4. Add monitoring/logging
5. Add API documentation (OpenAPI)
