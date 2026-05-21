-- =============================================================
-- DAKSHA v2 Migration: Agent Graph Tables
-- Safe to run multiple times (IF NOT EXISTS guards)
--
-- Adds:
--   agent_actions    — per-tool-call trace log for every agent action
--   handoff_messages — real-time chat log for human-handoff sessions
-- Alters:
--   agent_handoffs   — ws_room_id, resolved_by, resolution_note, escalation_level
--   sessions         — order_mode, active_handoff_id, kiosk_store_id
-- =============================================================

-- -------------------------------------------------------------
-- 1. agent_actions
--    Fine-grained log of every tool call inside an agent run.
--    agent_runs = the whole run; agent_actions = each step.
--    Powers the admin /admin/agent-runs/:id/actions trace view.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_actions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID REFERENCES sessions(id)    ON DELETE SET NULL,
    user_id         UUID REFERENCES users(id)        ON DELETE SET NULL,
    agent_run_id    UUID REFERENCES agent_runs(id)   ON DELETE SET NULL,

    agent_name      TEXT NOT NULL,        -- "RecommendationAgent"
    tool_name       TEXT NOT NULL,        -- "find_similar_by_image"
    tool_input      JSONB,                -- arguments passed to the tool
    tool_output     JSONB,                -- result returned by the tool
    model_used      TEXT,                 -- "gemini-2.5-flash" | "llama-3.3-70b-versatile"

    latency_ms      INTEGER,              -- wall-clock ms for this single tool call
    success         BOOLEAN DEFAULT TRUE,
    error_message   TEXT,

    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_actions_session
    ON agent_actions(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_run
    ON agent_actions(agent_run_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_agent_name
    ON agent_actions(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_actions_created
    ON agent_actions(created_at DESC);

COMMENT ON TABLE agent_actions IS
  'Immutable per-tool-call trace. Each row = one LangGraph tool invocation. Powers the step-by-step admin debugger.';

-- -------------------------------------------------------------
-- 2. handoff_messages
--    Stores every message exchanged during a human-handoff
--    session (user side + admin side). WebSocket relay writes
--    here in real time. Admin joining late sees full history.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS handoff_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    handoff_id  UUID NOT NULL REFERENCES agent_handoffs(id) ON DELETE CASCADE,
    session_id  UUID REFERENCES sessions(id)  ON DELETE SET NULL,

    speaker     TEXT NOT NULL CHECK (speaker IN ('user', 'admin', 'system')),
    message     TEXT NOT NULL,
    admin_id    UUID REFERENCES users(id) ON DELETE SET NULL,  -- set when speaker='admin'

    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_handoff_messages_handoff
    ON handoff_messages(handoff_id);
CREATE INDEX IF NOT EXISTS idx_handoff_messages_session
    ON handoff_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_handoff_messages_created
    ON handoff_messages(created_at ASC);

COMMENT ON TABLE handoff_messages IS
  'Real-time chat log written by the WebSocket relay. One row per message during an agent-to-human escalation.';

-- -------------------------------------------------------------
-- 3. Alter agent_handoffs
--    Existing columns: id, session_id, user_id, from_agent_name,
--    reason, summary, assigned_to_admin_id, status, created_at,
--    resolved_at
-- -------------------------------------------------------------
ALTER TABLE agent_handoffs
    ADD COLUMN IF NOT EXISTS ws_room_id        TEXT,
    ADD COLUMN IF NOT EXISTS resolved_by       UUID REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS resolution_note   TEXT,
    ADD COLUMN IF NOT EXISTS escalation_level  INTEGER DEFAULT 1;

CREATE INDEX IF NOT EXISTS idx_handoffs_open
    ON agent_handoffs(status, created_at DESC)
    WHERE status IN ('open', 'in_progress');

-- -------------------------------------------------------------
-- 4. Alter sessions
--    Existing columns: id, user_id, primary_channel,
--    active_channel, started_at, ended_at, context, anonymous_id
-- -------------------------------------------------------------
ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS order_mode         TEXT
        CHECK (order_mode IN ('online', 'pickup')) DEFAULT 'online',
    ADD COLUMN IF NOT EXISTS active_handoff_id  UUID
        REFERENCES agent_handoffs(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS kiosk_store_id     UUID
        REFERENCES stores(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_sessions_active_handoff
    ON sessions(active_handoff_id)
    WHERE active_handoff_id IS NOT NULL;
