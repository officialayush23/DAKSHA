# 🧪 Testing Guide - DAKSHA Integration

## 🚀 **Quick Start**

### **1. Start Backend:**
```bash
cd BACKEND
# Activate venv
source daksha/bin/activate  # Windows: daksha\Scripts\activate
# Install dependencies (if needed)
pip install -r requirements.txt
# Start server
uvicorn app.main:app --reload
```

**Expected:** Server starts on `http://localhost:8000`

### **2. Start Frontend:**
```bash
cd FRONTEND
# Install dependencies (if needed)
npm install
# Start dev server
npm run dev
```

**Expected:** Frontend starts on `http://localhost:5173` (or similar)

---

## ✅ **Test Scenarios**

### **Test 1: Chat Agent Orchestration**

**Steps:**
1. Navigate to `/chat` in frontend
2. Send message: "Show me running shoes"
3. Verify:
   - ✅ Message appears in chat
   - ✅ Agent responds
   - ✅ If products found, product carousel appears
   - ✅ JSON viewer shows payload (collapsible)
   - ✅ No errors in console

**Expected Behavior:**
- Agent processes message
- Tool calls execute (search_products_tool)
- Products displayed in carousel
- JSON payload visible in collapsible viewer

---

### **Test 2: WebSocket Real-Time Updates**

**Steps:**
1. Open browser DevTools → Network → WS
2. Navigate to `/chat`
3. Send a message
4. Verify:
   - ✅ WebSocket connection established (`ws://localhost:8000/ws/chat/{conversation_id}`)
   - ✅ Connection status shows "Connected" badge
   - ✅ Messages stream in real-time

**Expected Behavior:**
- WebSocket connects automatically
- Real-time message updates (if multiple users)
- Connection indicator shows status

---

### **Test 3: Support Page API Migration**

**Steps:**
1. Navigate to `/support`
2. Click "New Ticket"
3. Fill form and submit
4. Verify:
   - ✅ Ticket appears in list
   - ✅ No Supabase errors in console
   - ✅ API calls visible in Network tab (`POST /support/tickets`)
   - ✅ Ticket details correct

**Expected Behavior:**
- Ticket created via API
- No direct DB access
- Ticket appears immediately
- Status badges display correctly

---

### **Test 4: Profile Page API Migration**

**Steps:**
1. Navigate to `/profile`
2. Go to "Addresses" tab
3. Click "Add Address"
4. Fill and save
5. Verify:
   - ✅ Address appears in list
   - ✅ No Supabase errors in console
   - ✅ API calls visible (`POST /users/me/addresses`)
6. Delete an address
7. Verify:
   - ✅ Address removed
   - ✅ API call visible (`DELETE /users/me/addresses/{id}`)

**Expected Behavior:**
- All data loaded via APIs
- Add/delete operations use APIs
- No direct DB access
- Data persists correctly

---

### **Test 5: Cart Operations**

**Steps:**
1. Navigate to `/cart` (or add item from product page)
2. Verify:
   - ✅ Cart loads via API (`GET /cart`)
   - ✅ Add item uses API (`POST /cart`)
   - ✅ Remove item uses API (`DELETE /cart/items/{id}`)
   - ✅ No direct Supabase access

**Expected Behavior:**
- Cart operations use APIs
- Real-time inventory updates (if WebSocket connected)
- No direct DB writes

---

### **Test 6: Conversation History**

**Steps:**
1. Send multiple messages in chat
2. Refresh page
3. Verify:
   - ✅ Previous messages load
   - ✅ Conversation history endpoint called (`GET /channels/conversations`)
   - ✅ Messages endpoint called (`GET /channels/conversations/{id}/messages`)

**Expected Behavior:**
- History loads on page refresh
- Messages displayed in chronological order
- No data loss

---

## 🔍 **Verification Checklist**

### **Backend:**
- [ ] Server starts without errors
- [ ] All endpoints accessible at `/docs` (Swagger UI)
- [ ] Agent orchestration works
- [ ] WebSocket endpoints respond
- [ ] RPC calls work (check logs)

### **Frontend:**
- [ ] No console errors
- [ ] No direct Supabase table access (check Network tab)
- [ ] All API calls return 200/201
- [ ] WebSocket connections establish
- [ ] UI renders correctly
- [ ] Loading states work
- [ ] Error messages display

### **Integration:**
- [ ] Chat sends/receives messages
- [ ] Support creates tickets
- [ ] Profile loads/updates data
- [ ] Cart operations work
- [ ] Real-time updates work
- [ ] JSON payloads display

---

## 🐛 **Common Issues & Fixes**

### **Issue 1: WebSocket Connection Failed**
**Symptom:** `WebSocket connection failed`
**Fix:** 
- Check backend is running
- Verify WebSocket endpoint exists
- Check CORS settings
- Verify Redis is running (for pub/sub)

### **Issue 2: API 401 Unauthorized**
**Symptom:** `401 Unauthorized` on API calls
**Fix:**
- Check auth token in headers
- Verify user is logged in
- Check `get_current_user_id` dependency

### **Issue 3: Conversation Not Loading**
**Symptom:** Chat history doesn't load
**Fix:**
- Check `conversation_sessions` table exists
- Verify user_id is correct
- Check API endpoint returns data

### **Issue 4: Direct DB Access Error**
**Symptom:** Frontend still accessing Supabase directly
**Fix:**
- Check all pages migrated to APIs
- Verify no `supabase.from()` calls in pages
- Check modules for direct access

---

## 📊 **Performance Checks**

- [ ] Chat messages send < 2s
- [ ] API responses < 500ms
- [ ] WebSocket latency < 100ms
- [ ] Page loads < 3s
- [ ] No memory leaks (check DevTools)

---

## ✅ **Success Criteria**

1. ✅ All frontend pages use APIs (no direct DB)
2. ✅ Chat works with agent orchestration
3. ✅ WebSocket provides real-time updates
4. ✅ Support and Profile pages fully functional
5. ✅ JSON payloads display correctly
6. ✅ No console errors
7. ✅ Beautiful, consistent UI
8. ✅ Error handling works

---

**Ready to test!** 🚀
