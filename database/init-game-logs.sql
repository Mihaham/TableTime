-- Game Logging Database Schema
-- This script creates tables for logging game events

-- Table for game creation events
CREATE TABLE IF NOT EXISTS game_creation_logs (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    creator_user_id INTEGER NOT NULL,
    invite_code INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for game join events
CREATE TABLE IF NOT EXISTS game_join_logs (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for game action events
CREATE TABLE IF NOT EXISTS game_action_logs (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    action_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for game finish events
CREATE TABLE IF NOT EXISTS game_finish_logs (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    finished_by_user_id INTEGER NOT NULL,
    winner_user_id INTEGER,
    final_state JSONB,
    finished_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for game errors/events
CREATE TABLE IF NOT EXISTS game_event_logs (
    id SERIAL PRIMARY KEY,
    game_id INTEGER,
    game_type VARCHAR(50),
    user_id INTEGER,
    event_type VARCHAR(100) NOT NULL,
    event_message TEXT,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_game_creation_logs_game_id ON game_creation_logs(game_id);
CREATE INDEX IF NOT EXISTS idx_game_creation_logs_creator ON game_creation_logs(creator_user_id);
CREATE INDEX IF NOT EXISTS idx_game_creation_logs_game_type ON game_creation_logs(game_type);
CREATE INDEX IF NOT EXISTS idx_game_creation_logs_created_at ON game_creation_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_game_join_logs_game_id ON game_join_logs(game_id);
CREATE INDEX IF NOT EXISTS idx_game_join_logs_user_id ON game_join_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_game_join_logs_joined_at ON game_join_logs(joined_at);

CREATE INDEX IF NOT EXISTS idx_game_action_logs_game_id ON game_action_logs(game_id);
CREATE INDEX IF NOT EXISTS idx_game_action_logs_user_id ON game_action_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_game_action_logs_action_type ON game_action_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_game_action_logs_created_at ON game_action_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_game_finish_logs_game_id ON game_finish_logs(game_id);
CREATE INDEX IF NOT EXISTS idx_game_finish_logs_finished_at ON game_finish_logs(finished_at);

CREATE INDEX IF NOT EXISTS idx_game_event_logs_game_id ON game_event_logs(game_id);
CREATE INDEX IF NOT EXISTS idx_game_event_logs_event_type ON game_event_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_game_event_logs_created_at ON game_event_logs(created_at);

