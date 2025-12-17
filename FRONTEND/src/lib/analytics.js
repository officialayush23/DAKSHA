// src/lib/analytics.js
import api from "@/lib/apiClient";
import { supabase } from "@/lib/supabaseClient";

// =============================================
// CONSTANTS & STORAGE
// =============================================
const SESSION_KEY = "daksha_session_id";
const QUEUE_KEY = "daksha_analytics_queue_v3";

let queue = JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");

const FLUSH_INTERVAL_MS = 5000; // send batch every 5s
const HEARTBEAT_INTERVAL_MS = 15000; // 15s
const SCROLL_BUCKET_SIZE = 20; // scroll 0,20,40,60,80,100

let maxScrollBucket = 0;
let sessionStartTime = Date.now();
let lastHeartbeat = Date.now();


// =============================================
// SESSION ID
// =============================================
export function getSessionId() {
  let sid = localStorage.getItem(SESSION_KEY);
  if (!sid) {
    sid = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, sid);
  }
  return sid;
}


// =============================================
// USER ID (Supabase)
// =============================================
export async function getUserId() {
  try {
    const { data } = await supabase.auth.getUser();
    return data?.user?.id || null;
  } catch {
    return null;
  }
}


// =============================================
// QUEUE PUSH (SYNC, VERY FAST)
// =============================================
function pushEvent(event) {
  queue.push(event);
  localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

export async function trackEvent(event_type, event_data = {}) {
  const session_id = getSessionId();
  const user_id = await getUserId();

  pushEvent({
    event_type,
    event_data,
    session_id,
    user_id,
    captured_at: new Date().toISOString(),
  });
}


// =============================================
// FLUSH BATCH TO SERVER
// =============================================
async function tryFlush() {
  if (queue.length === 0) return;

  const payload = queue.slice();

  try {
    await api.post("/analytics/track/bulk", payload);
    queue = [];
    localStorage.setItem(QUEUE_KEY, "[]");
  } catch (err) {
    console.warn("Analytics flush failed — keeping queue:", err);
  }
}

export const flush = tryFlush;

// Auto flush loop
setInterval(tryFlush, FLUSH_INTERVAL_MS);


// =============================================
// SCROLL DEPTH TRACKING (BUCKETED)
// =============================================
function handleScroll() {
  const docHeight = document.body.scrollHeight - window.innerHeight;
  if (docHeight <= 0) return;

  const pct = Math.round((window.scrollY / docHeight) * 100);
  const bucket = Math.floor(pct / SCROLL_BUCKET_SIZE) * SCROLL_BUCKET_SIZE;

  if (bucket > maxScrollBucket) {
    maxScrollBucket = bucket;
    trackEvent("scroll_depth", { percent: bucket });
  }
}

window.addEventListener("scroll", () => {
  requestAnimationFrame(handleScroll);
});


// =============================================
// DEBOUNCED FILTER CHANGES
// =============================================
let filterTimer = null;

export function trackFilterChanged(filters) {
  clearTimeout(filterTimer);
  filterTimer = setTimeout(() => {
    trackEvent("filter_change", filters);
  }, 300);
}


// =============================================
// PAGE VISIBILITY CHANGES (TAB HIDE/RETURN)
// =============================================
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    trackEvent("page_hidden", { ts: Date.now() });
  } else {
    trackEvent("page_visible", { ts: Date.now() });
  }
});


// =============================================
// EXIT INTENT (desktop)
// =============================================
document.addEventListener("mouseleave", (e) => {
  if (e.clientY <= 0) {
    trackEvent("exit_intent", {});
  }
});


// =============================================
// BEFORE UNLOAD — sync final write
// =============================================
function handleBeforeUnload() {
  const dwellMs = Date.now() - sessionStartTime;

  // sync event (no async wait)
  pushEvent({
    event_type: "page_exit",
    event_data: {
      dwell_ms: dwellMs,
      max_scroll: maxScrollBucket,
      bounced: dwellMs < 3000,
    },
    session_id: getSessionId(),
    user_id: supabase.auth.getUser().data?.user?.id || null,
    captured_at: new Date().toISOString(),
  });

  navigator.sendBeacon(
    `${import.meta.env.VITE_API_BASE_URL}/analytics/track/bulk`,
    JSON.stringify(queue)
  );
}

window.addEventListener("beforeunload", handleBeforeUnload);


// =============================================
// HEARTBEAT (THROTTLED)
// =============================================
setInterval(() => {
  const now = Date.now();
  if (now - lastHeartbeat >= HEARTBEAT_INTERVAL_MS) {
    lastHeartbeat = now;
    trackEvent("heartbeat", { ts: new Date().toISOString() });
  }
}, 5000);


// =============================================
// PUBLIC HELPERS (CLEANED & STABLE)
// =============================================

export function trackProductImpression(p) {
  trackEvent("product_impression", {
    product_id: p.id,
    category: p.category_name,
    tags: p.tags,
    price: p.price,
  });
}

export function trackProductView(p) {
  trackEvent("product_view", {
    product_id: p.id,
    category: p.category_name,
    tags: p.tags,
    price: p.price,
  });
}

export function trackProductClick(p) {
  trackEvent("product_click", { product_id: p.id });
}

export function trackAddToCart(p) {
  trackEvent("add_to_cart", {
    product_id: p.id,
    price: p.price,
    variant_id: p.default_variant_id,
  });
}

export function trackSearch(query) {
  trackEvent("search", { query });
}

export function trackSortChanged(option) {
  trackEvent("sort_change", { option });
}

export function trackCategoryView(category) {
  trackEvent("category_view", { category });
}

export function trackPageEnter(name) {
  trackEvent("page_enter", { page: name });
}

export function trackPageExit(name) {
  trackEvent("page_exit", { page: name });
}

export function trackRecommendationClick(product, algorithm = "vector") {
  trackEvent("recommendation_click", {
    product_id: product.id,
    algorithm,
  });
}
