export const CHANNEL_TYPE = {
  WEB: 'web',
  APP: 'app',
  KIOSK: 'kiosk',
  WHATSAPP: 'whatsapp',
  TELEGRAM: 'telegram'
};

export const CHECKOUT_STATE = {
  INIT: 'INIT',
  CART_VALIDATED: 'CART_VALIDATED',
  STOCK_RESERVED: 'STOCK_RESERVED',
  PRICE_LOCKED: 'PRICE_LOCKED',
  COUPON_APPLIED: 'COUPON_APPLIED',
  PAYMENT_PENDING: 'PAYMENT_PENDING',
  PAYMENT_FAILED: 'PAYMENT_FAILED',
  DELIVERY_SCHEDULED: 'DELIVERY_SCHEDULED',
  ORDER_CONFIRMED: 'ORDER_CONFIRMED',
  ROLLED_BACK: 'ROLLED_BACK'
};

export const EVENT_TYPE = {
  PRODUCT_VIEW: 'product_view',
  SEARCH: 'search',
  ADD_TO_CART: 'add_to_cart',
  REMOVE_FROM_CART: 'remove_from_cart',
  CHECKOUT_STARTED: 'checkout_started',
  CHECKOUT_CANCELLED: 'checkout_cancelled',
  PAYMENT_STARTED: 'payment_started',
  PAYMENT_FAILED: 'payment_failed',
  PAYMENT_SUCCESS: 'payment_success',
  ORDER_PLACED: 'order_placed'
};

// Kiosk specific configuration
export const KIOSK_CONFIG = {
  IDLE_TIMEOUT_MS: 60000,
  POLLING_INTERVAL_MS: 2000,
};