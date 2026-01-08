# 🎨 Frontend Improvements & API Migration Guide

## 📋 **CRITICAL: API Migration Required**

### **Files Requiring Migration:**

1. **`src/pages/Support.jsx`** ❌
   - **Current:** Direct Supabase DB access
   - **Required:** Use `/support/tickets` API endpoints
   - **Status:** Backend APIs created ✅

2. **`src/pages/Profile.jsx`** ❌
   - **Current:** Direct Supabase DB access
   - **Required:** Use `/users/me/*` API endpoints
   - **Status:** Backend APIs created ✅

---

## 🔧 **API Endpoints Available**

### **Support Tickets:**
- `GET /support/tickets` - List user tickets
- `GET /support/tickets/{id}` - Get ticket details
- `POST /support/tickets` - Create ticket
- `PATCH /support/tickets/{id}` - Update ticket

### **User Profile:**
- `GET /users/me` - Get user profile ✅ (already exists)
- `GET /users/me/addresses` - Get addresses ✅ (new)
- `POST /users/me/addresses` - Add address ✅ (new)
- `GET /users/me/payment-methods` - Get payment methods ✅ (new)
- `GET /users/me/notifications` - Get notifications ✅ (new)

---

## 🎨 **UI/UX Improvements**

### **1. Chat Interface Enhancements**

#### **A. JSON Payload Display**
**File:** `src/pages/Chat.jsx`

**Add JSON Viewer Component:**
```jsx
// Add to Chat.jsx
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, ChevronUp } from "lucide-react";

function JSONViewer({ data, title = "Payload" }) {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="mt-2">
      <CollapsibleTrigger className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground">
        {isOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        {title} {isOpen ? "▼" : "▶"}
      </CollapsibleTrigger>
      <CollapsibleContent>
        <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-48 font-mono">
          {JSON.stringify(data, null, 2)}
        </pre>
      </CollapsibleContent>
    </Collapsible>
  );
}

// In Message component, add:
{msg.payload && (
  <JSONViewer data={msg.payload} title="Agent Payload" />
)}
```

#### **B. Enhanced Payload Rendering**
**Current:** Only shows products and order_history
**Improvement:** Add handlers for all payload types

```jsx
// Enhanced payload rendering
{msg.payload && (
  <div className="mt-2 space-y-2">
    {msg.payload.type === 'products' && (
      <ProductCarousel products={msg.payload.data} />
    )}
    {msg.payload.type === 'order_history' && (
      <OrderHistoryList orders={msg.payload.data} />
    )}
    {msg.payload.type === 'recommendations' && (
      <RecommendationCarousel items={msg.payload.data} />
    )}
    {msg.payload.type === 'cart' && (
      <CartSummary cart={msg.payload.data} />
    )}
    {/* Debug: Always show JSON */}
    <JSONViewer data={msg.payload} />
  </div>
)}
```

#### **C. Confidence Indicator** (Optional)
```jsx
{msg.confidence !== undefined && (
  <div className="mt-1 text-xs text-muted-foreground">
    Confidence: {Math.round(msg.confidence * 100)}%
    {msg.confidence < 0.4 && (
      <Badge variant="destructive" className="ml-2">Escalated</Badge>
    )}
  </div>
)}
```

---

### **2. Kiosk Interface Improvements**

#### **A. Better Product Display**
**File:** `src/modules/kiosk/page/StoreGuide.jsx`

**Improvements:**
- Larger product cards (better touch targets)
- Swipe gestures for product navigation
- Voice input button more prominent
- Better loading states

#### **B. Store Guide Navigation**
- Add breadcrumbs
- Better category filtering
- Search bar with voice input
- Recent searches

#### **C. Theme Consistency**
- Ensure Kiosk uses same theme as main app
- Consistent color scheme
- Same typography

---

### **3. Support Page Migration**

**File:** `src/pages/Support.jsx`

**Before (Direct DB):**
```javascript
const { data } = await supabase.from('support_tickets').insert(payload);
```

**After (API):**
```javascript
const { data } = await api.post('/support/tickets', {
  issue_summary: formData.issue_summary,
  conversation_summary: formData.details,
  priority: formData.priority,
  order_id: formData.order_id === "none" ? null : formData.order_id,
  ticket_type: "general"
});
```

---

### **4. Profile Page Migration**

**File:** `src/pages/Profile.jsx`

**Before (Direct DB):**
```javascript
const { data } = await supabase.from('users').select('*').eq('id', user.id).single();
const { data: addrList } = await supabase.from('user_addresses').select('*').eq('user_id', user.id);
```

**After (API):**
```javascript
const profileRes = await api.get('/users/me');
const addressesRes = await api.get('/users/me/addresses');
const paymentsRes = await api.get('/users/me/payment-methods');
const notificationsRes = await api.get('/users/me/notifications');
```

---

## 🎯 **Implementation Priority**

### **Phase 1: Critical (Immediate)**
1. ✅ Migrate Support page to API
2. ✅ Migrate Profile page to API
3. ✅ Fix human handoff schema issues (backend)

### **Phase 2: High Priority**
1. ✅ Add JSON viewer to Chat
2. ✅ Enhance payload rendering
3. ✅ Better error handling

### **Phase 3: Medium Priority**
1. ✅ Improve Kiosk interface
2. ✅ Add confidence indicators
3. ✅ Theme consistency

### **Phase 4: Low Priority**
1. ✅ Voice input improvements
2. ✅ Better loading states
3. ✅ Accessibility improvements

---

## 📝 **Notes**

- **Never use Supabase client for data operations** - Always use API
- **Supabase Auth is OK** - Auth is separate from data layer
- **WebSocket connections are OK** - Real-time features are separate
- **All writes must go through API** - No direct DB writes from frontend
