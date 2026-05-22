-- v6_chat_message_ui_data.sql
-- Adds ui_data JSONB column to chat_messages so product cards / rich
-- UI payloads are stored alongside assistant messages and can be
-- re-rendered when loading conversation history.

ALTER TABLE chat_messages
    ADD COLUMN IF NOT EXISTS ui_data JSONB DEFAULT NULL;

COMMENT ON COLUMN chat_messages.ui_data IS
    'Structured UI payload (product cards, order summaries, etc.) '
    'returned by the agent alongside the text response. '
    'Null for user and tool messages.';
