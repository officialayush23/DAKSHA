-- =============================================================
-- DAKSHA v7: agentic core
-- Safe to run more than once.
--
--   agent_memories      private, per-agent long-term memory
--   agent_approvals     human-in-the-loop queue (customer confirmations + staff approvals)
--   proactive_triggers  de-duplication of proactive follow-ups
--   agent_handoffs      + chat_session_id (handoffs belong to a chat thread)
-- =============================================================

CREATE TABLE IF NOT EXISTS agent_memories (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain       TEXT NOT NULL DEFAULT 'commerce',
    agent        TEXT NOT NULL,
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    kind         TEXT NOT NULL DEFAULT 'episodic' CHECK (kind IN ('episodic', 'semantic', 'preference')),
    content      TEXT NOT NULL,
    salience     REAL NOT NULL DEFAULT 0.5,
    meta         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_agent_memories_ns
    ON agent_memories (domain, agent, user_id, created_at DESC);
COMMENT ON TABLE agent_memories IS
  'Each agent reads and writes only its own namespace (domain, agent, user). Shared facts live in the unified context instead.';

CREATE TABLE IF NOT EXISTS agent_approvals (
    id             UUID PRIMARY KEY,
    thread_id      TEXT NOT NULL,
    agent_run_id   UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    user_id        UUID REFERENCES users(id) ON DELETE SET NULL,
    agent          TEXT NOT NULL,
    tool           TEXT NOT NULL,
    args           JSONB NOT NULL DEFAULT '{}'::jsonb,
    reason         TEXT,
    rule           TEXT,
    approver_role  TEXT NOT NULL CHECK (approver_role IN ('customer', 'staff')),
    summary        TEXT,
    status         TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    decided_by     UUID,
    decision_note  TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_agent_approvals_pending ON agent_approvals (approver_role, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_approvals_thread ON agent_approvals (thread_id);

CREATE TABLE IF NOT EXISTS proactive_triggers (
    key         TEXT PRIMARY KEY,               -- e.g. abandoned_cart:<cart_id>:<updated_at>
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    type        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'queued', -- queued | done | waiting_approval | failed
    result      JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE agent_handoffs ADD COLUMN IF NOT EXISTS chat_session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_agent_handoffs_chat ON agent_handoffs (chat_session_id, status);
