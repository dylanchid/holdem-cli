-- Holdem CLI Database Schema
-- This file contains the complete SQLite schema for Holdem CLI
-- SQLite Syntax - Not for SQL Server

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quiz_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,           -- e.g., hand-ranking, pot-odds, starting-hands
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    difficulty TEXT,              -- easy, medium, hard
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    correct_answer TEXT,
    chosen_answer TEXT,
    explanation TEXT,
    FOREIGN KEY(session_id) REFERENCES quiz_sessions(id)
);

CREATE TABLE IF NOT EXISTS sim_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    variant TEXT NOT NULL,        -- texas-holdem, omaha (future)
    ai_level TEXT,               -- easy, medium, hard
    result TEXT,                 -- win, loss, tie
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS hand_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sim_session_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY(sim_session_id) REFERENCES sim_sessions(id)
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_id ON quiz_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_type ON quiz_sessions(type);
CREATE INDEX IF NOT EXISTS idx_quiz_questions_session_id ON quiz_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_sim_sessions_user_id ON sim_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_hand_history_sim_session_id ON hand_history(sim_session_id);
