CREATE TABLE conversation_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_input TEXT NOT NULL,
    model_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_session_id ON conversation_history(session_id);