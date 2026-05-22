-- v5_chat_sessions.sql
-- Chat session history: each "New Chat" click creates a new session
-- AI generates a name after the first message
-- Sessions persist across channels (web / kiosk)

CREATE TABLE IF NOT EXISTS chat_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT,                          -- AI-generated after first message
    channel         TEXT NOT NULL DEFAULT 'web',   -- web | kiosk | app
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    summary         TEXT,                          -- rolling summary of older messages
    summary_cursor  INT NOT NULL DEFAULT 0,        -- index up to which messages are summarised
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id  ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated  ON chat_sessions(user_id, updated_at DESC);

-- Store full message history per session
CREATE TABLE IF NOT EXISTS chat_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user','assistant','tool')),
    content     TEXT NOT NULL,
    tool_name   TEXT,          -- populated when role='tool'
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id, created_at ASC);

-- Trigger: keep chat_sessions.updated_at fresh
CREATE OR REPLACE FUNCTION update_chat_session_timestamp()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    UPDATE chat_sessions
    SET updated_at = NOW(), last_message_at = NOW()
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_chat_message_updated ON chat_messages;
CREATE TRIGGER trg_chat_message_updated
    AFTER INSERT ON chat_messages
    FOR EACH ROW EXECUTE FUNCTION update_chat_session_timestamp();
