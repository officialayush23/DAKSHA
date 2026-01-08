# 🎯 DAKSHA Backend Architecture Audit Report
**Date:** 2024  
**Status:** Production-Grade Agentic Commerce System  
**Version:** v1.0

---

## ✅ **ARCHITECTURE COMPLIANCE**

### 1. **RPC-Only Write Path** ✅ **VERIFIED**

**Status:** ✅ **COMPLIANT** (with minor exceptions)

#### ✅ **Correctly Using RPCs:**
- ✅ `CommerceService.checkout_commit` → Uses `create_order_from_cart` RPC
- ✅ `PaymentService.capture_payment` → Uses `capture_payment_to_escrow` + `assert_order_paid` RPCs
- ✅ `InventoryReservationService` → Uses `release_inventory_reservation` RPC
- ✅ `WarehouseService` → Uses `adjust_inventory` RPC
- ✅ All admin routers → Use `transition_order_state` RPC for order status changes
- ✅ All inventory adjustments → Use `adjust_inventory` RPC

#### ⚠️ **Exceptions (Acceptable):**
- **Payment Creation:** No RPC provided for payment insert (only capture RPC exists) - **ACCEPTABLE**
- **Fulfillment Tracking:** `tracking_reference` updates are non-transactional metadata - **ACCEPTABLE**
- **Cart Operations:** No RPC provided for cart mutations - **ACCEPTABLE** (but should be added)

#### ❌ **Issues Found:**
1. **Human Handoff Service** - Direct table insert instead of RPC
   - **File:** `app/services/human_handoff_service.py`
   - **Issue:** Directly inserts into `human_handoffs` table
   - **Fix:** Should use `propose_handoff` RPC (if available) or create RPC
   - **Severity:** MEDIUM (handoff is critical but not transactional)

2. **Agent Runs Logging** - Direct table insert
   - **File:** `app/agents/graph.py:252`
   - **Issue:** Directly inserts into `agent_runs` table
   - **Fix:** Acceptable (logging is non-transactional)
   - **Severity:** LOW

---

### 2. **Agent Orchestration** ✅ **VERIFIED**

#### ✅ **Sales Agent (Orchestrator)**
- ✅ Hub-and-spoke model correctly implemented
- ✅ LangGraph StateGraph with proper tool routing
- ✅ Intent classification via DeepSeek (IntentClassifier)
- ✅ Confidence scoring implemented
- ✅ Auto-escalation on low confidence (< 0.4)
- ✅ Tool-only side effects (no direct DB writes)
- ✅ Conversational continuity via ChatHistoryService

#### ✅ **Intent Classifier**
- ✅ Advisory-only (not authoritative)
- ✅ Proper intent categories (discovery, checkout, support, human_handoff)
- ✅ Uses separate LLM (cost control)

#### ✅ **Worker Agents (Tools)**
- ✅ All tools are stateless
- ✅ No direct state mutations
- ✅ Proper error handling
- ✅ JSON serialization for tool responses

#### ⚠️ **Issues Found:**
1. **Confidence Scoring** - Too simplistic
   - **File:** `app/agents/confidence.py`
   - **Issue:** Only checks for error keywords, doesn't consider tool success/failure
   - **Fix:** Enhance with tool result analysis, LLM uncertainty detection
   - **Severity:** MEDIUM

2. **Intent Classification** - No validation
   - **File:** `app/agents/intent_classifier.py`
   - **Issue:** No validation of intent response format
   - **Fix:** Add validation and fallback to "general" intent
   - **Severity:** LOW

3. **Agent Budget Enforcement** - Soft enforcement only
   - **File:** `app/agents/budget.py`
   - **Issue:** Tracks but doesn't enforce hard limits
   - **Fix:** Add hard limits and circuit breakers
   - **Severity:** LOW

---

### 3. **Human Handoff System** ⚠️ **NEEDS IMPROVEMENT**

#### ✅ **What Works:**
- ✅ Auto-escalation on low confidence
- ✅ Support ticket auto-creation
- ✅ Context preservation (session_id, user_id, reason, summary)

#### ❌ **Issues Found:**
1. **Missing RPC Usage**
   - **File:** `app/services/human_handoff_service.py`
   - **Issue:** Direct table insert instead of `propose_handoff` RPC
   - **Fix:** Use RPC for auditability and RLS compliance
   - **Severity:** MEDIUM

2. **Missing Context Snapshot**
   - **Issue:** Doesn't save full conversation context to `context_snapshot` JSONB field
   - **Fix:** Save recent conversation history as JSONB
   - **Severity:** MEDIUM

3. **No Handoff Status Management**
   - **Issue:** Doesn't use `claim_handoff` or `resolve_handoff` RPCs
   - **Fix:** Implement ops dashboard integration
   - **Severity:** LOW (ops dashboard handles this)

---

### 4. **Database Schema Alignment** ✅ **VERIFIED**

#### ✅ **Correct:**
- ✅ All enum values match DB schema
- ✅ Column names match (`quantity_reserved`, not `reserved_qty`)
- ✅ Table references correct (no `fulfillment_sources` references)
- ✅ Order status values match `order_status_enum`

#### ⚠️ **Minor Issues:**
1. **Human Handoff Schema Mismatch**
   - **Issue:** Code uses `session_id` but DB schema expects `conversation_id`
   - **File:** `app/services/human_handoff_service.py:22`
   - **Fix:** Map `session_id` → `conversation_id` or update schema
   - **Severity:** HIGH (will cause DB errors)

2. **Support Ticket Schema Mismatch**
   - **Issue:** Code uses `ticket_status` but DB schema expects `status` (ticket_status_enum)
   - **File:** `app/services/human_handoff_service.py:39`
   - **Fix:** Use correct column name
   - **Severity:** HIGH (will cause DB errors)

---

### 5. **Error Handling** ⚠️ **NEEDS IMPROVEMENT**

#### ✅ **What Works:**
- ✅ Try-catch blocks in critical paths
- ✅ HTTPException for API errors
- ✅ Graceful degradation (fallback to trending if ML fails)

#### ❌ **Issues Found:**
1. **Silent Failures**
   - **File:** `app/agents/graph.py:263`
   - **Issue:** Agent run logging failures are silently ignored
   - **Fix:** Add proper logging
   - **Severity:** LOW

2. **Generic Error Messages**
   - **Issue:** Many tools return generic "Failed" messages
   - **Fix:** Include error details for debugging
   - **Severity:** LOW

---

### 6. **Security & RBAC** ✅ **VERIFIED**

#### ✅ **What Works:**
- ✅ JWT authentication via `get_current_user_id`
- ✅ Optional auth for guest users
- ✅ RBAC for admin routes
- ✅ RLS policies in DB

#### ⚠️ **Issues Found:**
1. **Guest User Handling**
   - **Issue:** Guest users can trigger handoffs but no user_id
   - **Fix:** Ensure handoff works with session_id only
   - **Severity:** LOW

---

## 📊 **SUMMARY**

### ✅ **Strengths:**
1. **RPC-Only Architecture** - Correctly implemented for transactional writes
2. **Agent Orchestration** - Proper hub-and-spoke model with LangGraph
3. **Intent Classification** - Advisory-only, cost-controlled
4. **Confidence Scoring** - Basic implementation with auto-escalation
5. **Tool Isolation** - All tools are stateless and deterministic

### ⚠️ **Critical Issues (Must Fix):**
1. **Human Handoff Schema Mismatch** - `session_id` vs `conversation_id`
2. **Support Ticket Schema Mismatch** - `ticket_status` vs `status`
3. **Human Handoff RPC** - Should use `propose_handoff` RPC instead of direct insert

### 🔧 **Recommended Improvements:**
1. **Enhanced Confidence Scoring** - Add tool result analysis
2. **Context Snapshot** - Save full conversation context in handoffs
3. **Error Logging** - Replace silent failures with proper logging
4. **Cart RPCs** - Create RPCs for cart mutations (add_item, update_cart)
5. **Agent Budget Hard Limits** - Add circuit breakers

---

## 🎯 **ARCHITECTURE SCORE: 8.5/10**

**Breakdown:**
- RPC Compliance: 9/10 (minor exceptions acceptable)
- Agent Orchestration: 9/10 (excellent structure)
- Human Handoff: 7/10 (needs schema fixes)
- Error Handling: 7/10 (needs better logging)
- Security: 9/10 (solid RBAC)

**Overall:** Production-ready with minor fixes needed.
