# 🚀 DAKSHA - Agentic Commerce Platform

**Production-Grade AI-Powered Retail System**

---

## 📊 **System Status**

### ✅ **Backend Architecture: 8.5/10**
- **RPC-Only Write Path:** ✅ Compliant (with minor exceptions)
- **Agent Orchestration:** ✅ Excellent (hub-and-spoke model)
- **Human Handoff:** ⚠️ Needs schema fixes
- **Error Handling:** ⚠️ Needs better logging
- **Security:** ✅ Solid RBAC

### ⚠️ **Frontend Architecture: 6/10**
- **API Compliance:** ❌ Direct DB access (needs migration)
- **UI/UX:** ✅ Good foundation
- **Chat Features:** ⚠️ Needs JSON display
- **Theme Consistency:** ✅ Good

**Overall:** Production-ready backend, frontend needs API migration.

---

## 🎯 **Architecture Overview**

### **Core Philosophy:**
> **LLMs suggest → RPCs decide → Humans override**

- **State lives in DB, not in the model**
- **All transactional writes go through Postgres RPCs**
- **Frontend never writes to DB directly**
- **Every action is logged and auditable**

### **Agent Orchestration:**
```
User → Sales Agent (LangGraph) → Tools → DB/RPC/Redis → Sales Agent → User
```

**Single conversational brain:** Sales Agent (Gemini)  
**Everything else:** Deterministic, scoped, auditable

---

## 📁 **Project Structure**

```
DAKSHA/
├── BACKEND/
│   ├── app/
│   │   ├── agents/          # AI Agent orchestration
│   │   ├── core/            # Auth, DB, RPC, Config
│   │   ├── models/          # Database models (all_models.py)
│   │   ├── routers/         # API endpoints
│   │   ├── schemas/         # Request/Response DTOs
│   │   └── services/        # Business logic
│   ├── AUDIT_REPORT.md      # Backend audit findings
│   └── README.md
│
└── FRONTEND/
    ├── src/
    │   ├── pages/           # Main pages
    │   ├── components/      # Reusable components
    │   ├── modules/         # Admin modules
    │   └── lib/             # API client, utils
    ├── AUDIT_REPORT.md      # Frontend audit findings
    └── FRONTEND_IMPROVEMENTS.md  # Migration guide
```

---

## 🔧 **Critical Issues & Fixes**

### **Backend:**

1. **Human Handoff Schema Mismatch** ✅ **FIXED**
   - **Issue:** Used `session_id` instead of `conversation_id`
   - **Fix:** Added mapping logic in `human_handoff_service.py`
   - **Status:** ✅ Fixed

2. **Support Ticket Schema Mismatch** ✅ **FIXED**
   - **Issue:** Used `ticket_status` instead of `status`
   - **Fix:** Updated `support_service.py` to use correct fields
   - **Status:** ✅ Fixed

3. **Missing Support API Endpoints** ✅ **FIXED**
   - **Added:** `GET /support/tickets`, `POST /support/tickets`, etc.
   - **Status:** ✅ Complete

4. **Missing User Profile APIs** ✅ **FIXED**
   - **Added:** `/users/me/addresses`, `/users/me/payment-methods`, etc.
   - **Status:** ✅ Complete

### **Frontend:**

1. **Direct DB Access** ❌ **NEEDS MIGRATION**
   - **Files:** `Support.jsx`, `Profile.jsx`
   - **Fix:** Migrate to API endpoints (see FRONTEND_IMPROVEMENTS.md)
   - **Status:** ⚠️ In Progress

2. **Chat JSON Display** ❌ **NEEDS IMPLEMENTATION**
   - **Issue:** Chat doesn't show JSON payloads
   - **Fix:** Add JSON viewer component
   - **Status:** ⚠️ Pending

---

## 🚀 **Quick Start**

### **Backend:**
```bash
cd BACKEND
python -m venv daksha
source daksha/bin/activate  # Windows: daksha\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### **Frontend:**
```bash
cd FRONTEND
npm install
npm run dev
```

---

## 📚 **Documentation**

- **Backend Audit:** `BACKEND/AUDIT_REPORT.md`
- **Frontend Audit:** `FRONTEND/AUDIT_REPORT.md`
- **Frontend Improvements:** `FRONTEND_IMPROVEMENTS.md`
- **API Documentation:** Available at `/docs` (Swagger UI)

---

## 🎯 **Key Features**

### **Agentic Commerce:**
- ✅ AI-powered product discovery
- ✅ Personalized recommendations
- ✅ Conversational checkout
- ✅ Multi-channel support (web, mobile, kiosk, WhatsApp)

### **Operations:**
- ✅ Human handoff system
- ✅ Support ticket management
- ✅ Inventory management
- ✅ Order fulfillment

### **Architecture:**
- ✅ RPC-only transactional writes
- ✅ Hub-and-spoke agent orchestration
- ✅ Confidence-based escalation
- ✅ Full audit trail

---

## ⚠️ **Known Issues**

1. **Frontend DB Access:** Some pages still use direct Supabase access
2. **Chat JSON Display:** Needs JSON viewer component
3. **Confidence Scoring:** Too simplistic, needs enhancement
4. **Agent Budget:** Soft enforcement only, needs hard limits

---

## 🔒 **Security**

- ✅ JWT authentication
- ✅ RBAC for admin routes
- ✅ RLS policies in database
- ✅ API-only data access (frontend migration in progress)

---

## 📈 **Performance**

- ✅ RPC-based writes (atomic operations)
- ✅ Redis for real-time updates
- ✅ Vector search for recommendations
- ✅ WebSocket for notifications

---

## 🤝 **Contributing**

1. Read `AUDIT_REPORT.md` for architecture guidelines
2. Follow RPC-only write pattern for transactional data
3. Never write to DB directly from frontend
4. All agent tools must be stateless

---

## 📄 **License**

Proprietary - All Rights Reserved

---

**Last Updated:** 2024  
**Version:** v1.0  
**Status:** Production-Ready (with frontend migration pending)
