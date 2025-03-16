-- Create database if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_database
        WHERE datname = 'vit'
    ) THEN
        CREATE DATABASE vit;
    END IF;
END
$$;

-- Create user if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'vit'
    ) THEN
        CREATE USER vit WITH PASSWORD 'vit';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE vit TO vit;

-- Connect to the vit database
\connect vit;

-- Create conversation history table
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_input TEXT NOT NULL,
    model_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries by session_id
CREATE INDEX IF NOT EXISTS idx_session_id ON conversation_history(session_id);