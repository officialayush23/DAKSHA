-- =============================================================
-- DAKSHA v4 Migration: Policy Audit Log + Missing HNSW Indexes
-- Safe to run multiple times (IF NOT EXISTS guards)
--
-- Adds:
--   policy_decisions   — immutable agent policy audit log
-- Creates HNSW indexes on embedding columns that don't have them yet:
--   conversation_summaries, user_preference_summary
--   (product_multimodal_embeddings, coupon_embeddings,
--    user_personalized_offer_embeddings already have HNSW in base schema)
-- Adds composite indexes for common agent query patterns
-- =============================================================

-- -------------------------------------------------------------
-- 1. policy_decisions
--    Every time an agent applies a policy rule (offer cap,
--    return window check, cancellation fee, loyalty cap etc.)
--    it writes one row here. Powers the admin policy audit view.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS policy_decisions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID REFERENCES sessions(id)      ON DELETE SET NULL,
    user_id             UUID REFERENCES users(id)          ON DELETE SET NULL,
    agent_run_id        UUID REFERENCES agent_runs(id)     ON DELETE SET NULL,
    agent_action_id     UUID REFERENCES agent_actions(id)  ON DELETE SET NULL,

    agent_name          TEXT NOT NULL,

    -- The policy rule that was evaluated
    rule_name           TEXT NOT NULL,      -- e.g. "MAX_OFFER_PERCENT_GOLD"
    rule_category       TEXT NOT NULL
        CHECK (rule_category IN (
            'offer', 'return', 'exchange',
            'cancellation', 'delivery', 'loyalty', 'payment'
        )),

    input_value         JSONB,              -- what the agent requested
    applied_value       JSONB,              -- what policy allowed / capped to
    was_overridden      BOOLEAN DEFAULT FALSE,
    override_by         UUID REFERENCES users(id) ON DELETE SET NULL,
    override_reason     TEXT,

    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_policy_decisions_session
    ON policy_decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_policy_decisions_user
    ON policy_decisions(user_id);
CREATE INDEX IF NOT EXISTS idx_policy_decisions_rule
    ON policy_decisions(rule_name);
CREATE INDEX IF NOT EXISTS idx_policy_decisions_category
    ON policy_decisions(rule_category);
CREATE INDEX IF NOT EXISTS idx_policy_decisions_created
    ON policy_decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_policy_decisions_overrides
    ON policy_decisions(was_overridden, created_at DESC)
    WHERE was_overridden = TRUE;

COMMENT ON TABLE policy_decisions IS
  'Immutable audit log of every policy rule evaluation by agents. Admin can review overrides.';

-- -------------------------------------------------------------
-- 2. HNSW indexes on embedding columns that lack them
--
--    Already have HNSW in base schema (skip):
--      product_multimodal_embeddings  → idx_product_multimodal_embeddings_hnsw
--      coupon_embeddings              → idx_coupon_embeddings_hnsw
--      user_personalized_offer_embeddings → idx_user_offer_embeddings_hnsw
--
--    Need HNSW (add here):
--      conversation_summaries         — semantic session context retrieval
--      user_preference_summary        — user taste profile similarity
--      user_image_embeddings          — visual search from user-uploaded photos
-- -------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_hnsw_conversation_summary
    ON conversation_summaries
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_hnsw_user_pref_summary
    ON user_preference_summary
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_hnsw_user_image_emb
    ON user_image_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- -------------------------------------------------------------
-- 3. Composite indexes for common agent query patterns
--    Cross-referenced against existing indexes to avoid duplicates.
-- -------------------------------------------------------------

-- DeliveryAgent: active orders for a user (order_status, not status)
CREATE INDEX IF NOT EXISTS idx_orders_user_active_status
    ON orders(user_id, order_status)
    WHERE order_status NOT IN ('delivered', 'cancelled');

-- CartAgent: cart lookup by session (carts has no status column)
CREATE INDEX IF NOT EXISTS idx_carts_session
    ON carts(session_id);

-- OfferAgent: unexpired personalised offers for a user
-- (idx_personal_offers_active already exists on user_personalized_offers)
-- Adding a redundancy-safe version with different name:
CREATE INDEX IF NOT EXISTS idx_personalized_offers_user_expiry
    ON user_personalized_offers(user_id, expires_at)
    WHERE is_redeemed = FALSE;

-- Loyalty: user balance queries — no volatile function in WHERE clause
CREATE INDEX IF NOT EXISTS idx_loyalty_ledger_user_time
    ON loyalty_ledger(user_id, created_at DESC);

-- Returns & exchanges: open cases per order
CREATE INDEX IF NOT EXISTS idx_returns_open
    ON returns(order_id)
    WHERE status IN ('requested', 'approved');

CREATE INDEX IF NOT EXISTS idx_exchanges_open
    ON exchanges(order_id)
    WHERE status IN ('requested', 'approved');

-- agent_actions: live feed query (recent actions across all sessions)
CREATE INDEX IF NOT EXISTS idx_agent_actions_tool_name
    ON agent_actions(tool_name, created_at DESC);

-- policy_decisions: overrides dashboard
CREATE INDEX IF NOT EXISTS idx_policy_agent_run
    ON policy_decisions(agent_run_id)
    WHERE agent_run_id IS NOT NULL;
