-- =============================================================
-- DAKSHA v3 Migration: Delivery Tracking & Reschedule Columns
-- Safe to run multiple times (IF NOT EXISTS guards)
--
-- Adds:
--   delivery_tracking  — courier push-events per shipment
-- Alters:
--   reschedule_requests — adds columns the agents need
--                         (table already exists with base cols)
--   orders             — delivery meta-fields
--   shipments          — tracking_url, last_event_code, last_event_at
-- =============================================================

-- -------------------------------------------------------------
-- 1. delivery_tracking
--    Push-based courier status events (one row per event).
--    Separate from delivery_attempt_events which captures
--    agent-side attempt logging. This is the live courier feed.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS delivery_tracking (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id            UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    shipment_id         UUID REFERENCES shipments(id)       ON DELETE SET NULL,

    status              TEXT NOT NULL,
    location_text       TEXT,
    location_coords     GEOGRAPHY(POINT, 4326),
    carrier_event_code  TEXT,
    carrier_message     TEXT,
    is_exception        BOOLEAN DEFAULT FALSE,
    exception_reason    TEXT,

    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_delivery_tracking_order
    ON delivery_tracking(order_id);
CREATE INDEX IF NOT EXISTS idx_delivery_tracking_time
    ON delivery_tracking(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_delivery_tracking_exception
    ON delivery_tracking(is_exception)
    WHERE is_exception = TRUE;

COMMENT ON TABLE delivery_tracking IS
  'Live courier push-events. DeliveryAgent reads this to answer tracking questions in real time.';

-- -------------------------------------------------------------
-- 2. Extend reschedule_requests
--    Table already exists in the schema with:
--      id, order_id, fulfillment_type, requested_slot,
--      user_selected_slot, status (reschedule_status_enum),
--      expires_at, created_at, updated_at
--
--    DeliveryAgent needs: session_id, requested_by, offered_slots,
--    chosen_slot, reason, agent_run_id, confirmed_at
-- -------------------------------------------------------------
ALTER TABLE reschedule_requests
    ADD COLUMN IF NOT EXISTS session_id    UUID
        REFERENCES sessions(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS requested_by  TEXT DEFAULT 'agent'
        CHECK (requested_by IN ('user', 'agent', 'admin')),
    ADD COLUMN IF NOT EXISTS offered_slots JSONB,
    ADD COLUMN IF NOT EXISTS chosen_slot   TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS reason        TEXT,
    ADD COLUMN IF NOT EXISTS agent_run_id  UUID
        REFERENCES agent_runs(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS confirmed_at  TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_reschedule_agent_run
    ON reschedule_requests(agent_run_id)
    WHERE agent_run_id IS NOT NULL;

COMMENT ON COLUMN reschedule_requests.offered_slots IS
  'JSON array of ISO-8601 datetime strings the agent offered to the customer.';
COMMENT ON COLUMN reschedule_requests.chosen_slot IS
  'The slot the user picked. Mirrors user_selected_slot but set by the agent flow.';

-- -------------------------------------------------------------
-- 3. Extend orders — delivery meta-fields used by DeliveryAgent
--    Existing columns include: id, user_id, fulfillment_type,
--    store_id, delivery_address, order_status, total_amount,
--    feedback_requested, mutability_state, delivery_address_id,
--    last_agent_run_id, created_at
-- -------------------------------------------------------------
ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS estimated_delivery_date   DATE,
    ADD COLUMN IF NOT EXISTS last_tracking_status      TEXT,
    ADD COLUMN IF NOT EXISTS last_tracking_update      TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS delivery_attempts         INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS is_delivery_exception     BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_orders_delivery_exception
    ON orders(is_delivery_exception)
    WHERE is_delivery_exception = TRUE;

-- -------------------------------------------------------------
-- 4. Extend shipments — tracking enrichment fields
--    Existing columns: id, order_id, carrier, tracking_number,
--    status, estimated_delivery, updated_at
--    NOTE: carrier already exists — do NOT add carrier_name.
-- -------------------------------------------------------------
ALTER TABLE shipments
    ADD COLUMN IF NOT EXISTS tracking_url    TEXT,
    ADD COLUMN IF NOT EXISTS last_event_code TEXT,
    ADD COLUMN IF NOT EXISTS last_event_at   TIMESTAMPTZ;
