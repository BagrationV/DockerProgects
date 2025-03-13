CREATE TABLE conversation_history (
    id SERIAL PRIMARY KEY,
    user_input TEXT NOT NULL,
    model_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);