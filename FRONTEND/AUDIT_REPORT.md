# 🎨 DAKSHA Frontend Architecture Audit Report
**Date:** 2024  
**Status:** Needs API Migration  
**Version:** v1.0

---

## ❌ **CRITICAL ISSUE: DIRECT DATABASE ACCESS**

### **Problem:**
Frontend is directly accessing Supabase tables, bypassing the backend API layer. This violates the architecture principle: **"Frontend never writes to DB directly, only through APIs"**.

---

## 🔍 **FILES WITH DIRECT DB ACCESS**

### 1. **Support Page** ❌
**File:** `src/pages/Support.jsx`

**Issues:**
- Line 51-55: Direct read from `support_tickets` table
- Line 61-66: Direct read from `orders` table
- Line 103-107: **Direct INSERT into `support_tickets` table** ❌

**Fix Required:**
```javascript
// ❌ OLD (Direct DB)
const { data } = await supabase.from('support_tickets').insert(payload);

// ✅ NEW (API)
const { data } = await api.post('/support/tickets', payload);
```

**Severity:** 🔴 **CRITICAL** (Writes to DB)

---

### 2. **Profile Page** ❌
**File:** `src/pages/Profile.jsx`

**Issues:**
- Line 76: Direct read from `users` table
- Line 79: Direct read from `user_style_profile` table
- Line 82: Direct read from `user_addresses` table
- Line 85: Direct read from `user_payment_methods` table
- Line 88: Direct read from `user_notifications` table

**Fix Required:**
```javascript
// ❌ OLD (Direct DB)
const { data } = await supabase.from('users').select('*').eq('id', user.id).single();

// ✅ NEW (API)
const { data } = await api.get('/users/me');
```

**Severity:** 🟡 **MEDIUM** (Read-only, but should use API)

---

### 3. **Auth Context** ⚠️
**File:** `src/context/AuthContext.jsx`

**Status:** ✅ **ACCEPTABLE**
- Uses Supabase Auth (correct - auth is separate from data)
- Syncs with backend via `/auth/sync` API ✅

**No changes needed.**

---

### 4. **Notification Socket** ⚠️
**File:** `src/hooks/useNotificationSocket.js`

**Status:** ✅ **ACCEPTABLE**
- Uses Supabase Auth for user ID (correct)
- WebSocket connection to backend (correct)

**No changes needed.**

---

## 🎯 **REQUIRED API ENDPOINTS**

### **Missing Backend APIs:**

1. **Support Tickets API**
   - `GET /support/tickets` - List user tickets
   - `POST /support/tickets` - Create ticket
   - `GET /support/tickets/{id}` - Get ticket details
   - `PATCH /support/tickets/{id}` - Update ticket

2. **Profile Data API** (Partially exists)
   - `GET /users/me` - ✅ Exists
   - `GET /users/me/addresses` - ❌ Missing
   - `GET /users/me/payment-methods` - ❌ Missing
   - `GET /users/me/notifications` - ❌ Missing
   - `POST /users/me/addresses` - ❌ Missing
   - `POST /users/me/payment-methods` - ❌ Missing

---

## 🐛 **CHAT IMPROVEMENTS NEEDED**

### **Current Issues:**

1. **JSON Payload Display** ❌
   - **File:** `src/pages/Chat.jsx`
   - **Issue:** Chat doesn't properly display JSON payloads from agent
   - **Current:** Only shows product carousels, order history shows generic message
   - **Fix:** Add JSON viewer component for debugging

2. **Payload Type Handling** ⚠️
   - **Issue:** Only handles `products` and `order_history` payloads
   - **Fix:** Add handlers for all payload types (recommendations, cart, etc.)

---

## 🎨 **UI/UX IMPROVEMENTS**

### **Kiosk Interface:**
1. **Better Product Display** - Larger cards, better touch targets
2. **Voice Input** - Already implemented ✅
3. **Store Guide** - Needs better navigation
4. **Theme Consistency** - Ensure matches main app theme

### **Chat Interface:**
1. **JSON Viewer** - Add collapsible JSON display for debugging
2. **Payload Visualization** - Better rendering of agent responses
3. **Confidence Indicator** - Show agent confidence score (optional)
4. **Handoff Status** - Show when conversation is escalated

---

## 📋 **MIGRATION PLAN**

### **Phase 1: Critical Fixes (Immediate)**
1. ✅ Create `/support/tickets` API endpoints
2. ✅ Migrate Support page to use API
3. ✅ Fix human handoff schema issues in backend

### **Phase 2: Profile API (High Priority)**
1. ✅ Create `/users/me/addresses` API
2. ✅ Create `/users/me/payment-methods` API
3. ✅ Create `/users/me/notifications` API
4. ✅ Migrate Profile page to use APIs

### **Phase 3: Chat Enhancements (Medium Priority)**
1. ✅ Add JSON viewer component
2. ✅ Enhance payload rendering
3. ✅ Add confidence indicators

### **Phase 4: UI Polish (Low Priority)**
1. ✅ Improve Kiosk interface
2. ✅ Theme consistency
3. ✅ Better error messages

---

## 🎯 **FRONTEND SCORE: 6/10**

**Breakdown:**
- API Compliance: 4/10 (Direct DB access)
- UI/UX: 7/10 (Good but needs polish)
- Chat Features: 6/10 (Needs JSON display)
- Theme Consistency: 7/10 (Good foundation)

**Overall:** Needs API migration before production.
