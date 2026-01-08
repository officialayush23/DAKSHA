# 🎯 Frontend-Backend Integration Plan

## ✅ **Backend Status Check**

### **Agent Orchestration** ✅
- ✅ LangGraph StateGraph properly configured
- ✅ Intent classification working
- ✅ Tool routing functional
- ✅ Confidence scoring implemented
- ✅ Human handoff triggers working

### **Chat System** ✅
- ✅ Conversation sessions using `conversation_sessions` table
- ✅ Messages using `conversation_messages` table
- ✅ Channel routing via `/channels/message` endpoint
- ⚠️ Need to fix `agent_runs` to use `conversation_id` instead of `session_id`

### **WebSocket** ✅
- ✅ Real-time endpoints exist (`/ws/inventory`, `/ws/notifications`)
- ⚠️ Need WebSocket endpoint for chat messages

---

## 📋 **Required APIs for Frontend**

### **1. Chat APIs** ✅ (Mostly Complete)
- ✅ `POST /channels/message` - Send message to agent
- ⚠️ `GET /channels/conversations` - Get user's conversation history
- ⚠️ `GET /channels/conversations/{id}/messages` - Get messages for a conversation
- ⚠️ `WebSocket /ws/chat/{conversation_id}` - Real-time chat updates

### **2. Support APIs** ✅ (Complete)
- ✅ `GET /support/tickets` - List user tickets
- ✅ `GET /support/tickets/{id}` - Get ticket details
- ✅ `POST /support/tickets` - Create ticket
- ✅ `PATCH /support/tickets/{id}` - Update ticket

### **3. Profile APIs** ✅ (Complete)
- ✅ `GET /users/me` - Get user profile
- ✅ `PATCH /users/me` - Update profile
- ✅ `GET /users/me/addresses` - Get addresses
- ✅ `POST /users/me/addresses` - Add address
- ✅ `GET /users/me/payment-methods` - Get payment methods
- ✅ `GET /users/me/notifications` - Get notifications

### **4. Cart APIs** ✅ (Should exist)
- ⚠️ Verify `GET /cart` - Get cart
- ⚠️ Verify `POST /cart/add` - Add item
- ⚠️ Verify `DELETE /cart/items/{id}` - Remove item

---

## 🎨 **Frontend Pages Needed**

### **1. Chat Page** ⚠️ (Needs Enhancement)
- ✅ Basic chat UI exists
- ⚠️ Add JSON viewer for debugging
- ⚠️ Better payload rendering (recommendations, cart, etc.)
- ⚠️ WebSocket integration for real-time updates
- ⚠️ Conversation history loading

### **2. Support Page** ❌ (Needs Migration)
- ❌ Currently uses direct Supabase access
- ✅ APIs exist - need to migrate
- ⚠️ Add ticket detail view
- ⚠️ Add ticket creation form

### **3. Profile Page** ❌ (Needs Migration)
- ❌ Currently uses direct Supabase access
- ✅ APIs exist - need to migrate
- ⚠️ Add address management UI
- ⚠️ Add payment method management UI

### **4. Cart Page** ⚠️ (Needs Verification)
- ⚠️ Verify API integration
- ⚠️ Add real-time inventory updates

---

## 🔧 **Implementation Tasks**

### **Backend Tasks:**
1. ✅ Fix `agent_runs` to use `conversation_id` instead of `session_id`
2. ⚠️ Add `GET /channels/conversations` endpoint
3. ⚠️ Add `GET /channels/conversations/{id}/messages` endpoint
4. ⚠️ Add `WebSocket /ws/chat/{conversation_id}` endpoint
5. ⚠️ Verify cart APIs exist and work

### **Frontend Tasks:**
1. ⚠️ Migrate `Support.jsx` to use APIs
2. ⚠️ Migrate `Profile.jsx` to use APIs
3. ⚠️ Enhance `Chat.jsx` with JSON viewer and WebSocket
4. ⚠️ Add conversation history loading
5. ⚠️ Improve payload rendering
6. ⚠️ Add loading states and error handling
7. ⚠️ Verify cart page API integration

---

## 🎨 **UI/UX Improvements**

### **Chat Interface:**
- ✅ Beautiful shadcn components
- ⚠️ Add JSON viewer (collapsible)
- ⚠️ Better product carousel
- ⚠️ Order history cards
- ⚠️ Recommendation cards
- ⚠️ Confidence indicator (optional)
- ⚠️ Handoff status indicator

### **Support Page:**
- ⚠️ Modern ticket list with filters
- ⚠️ Ticket detail modal
- ⚠️ Create ticket form
- ⚠️ Status badges

### **Profile Page:**
- ⚠️ Address cards with edit/delete
- ⚠️ Payment method cards
- ⚠️ Notification list
- ⚠️ Profile edit form

---

## 🧪 **Testing Checklist**

1. ✅ Backend agent orchestration works
2. ✅ Chat endpoint responds correctly
3. ⚠️ WebSocket connections work
4. ⚠️ Frontend can send/receive messages
5. ⚠️ Payload rendering works
6. ⚠️ Support page uses APIs
7. ⚠️ Profile page uses APIs
8. ⚠️ No direct DB access from frontend
9. ⚠️ Real-time updates work
10. ⚠️ Error handling works

---

## 📝 **Notes**

- All APIs must be RESTful
- WebSocket for real-time only
- No direct Supabase client usage for data (auth is OK)
- Use shadcn components for consistency
- Follow existing theme
- Add proper loading states
- Add error boundaries
