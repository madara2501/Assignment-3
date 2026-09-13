-- ============================================================
-- Assignment 3
-- Secure Backend & Database Design
-- Authentication System
-- ============================================================

-- USERS TABLE
-- Stores application users.
-- Passwords are NEVER stored directly.
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,

    full_name VARCHAR(100) NOT NULL,

    email VARCHAR(255) NOT NULL UNIQUE,

    password_hash TEXT NOT NULL,

    role VARCHAR(20) NOT NULL DEFAULT 'student',

    is_verified BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_user_role
        CHECK (role IN ('student', 'instructor'))
);


-- OTP TABLE
-- Stores hashed OTP values.
-- The actual OTP is sent to the user's email and is never
-- stored as plain text in the database.
CREATE TABLE IF NOT EXISTS otp_codes (
    id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL,

    otp_hash TEXT NOT NULL,

    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    attempts INTEGER NOT NULL DEFAULT 0,

    used BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_otp_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


-- SESSION TABLE
-- Stores hashed session tokens instead of raw session tokens.
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL,

    session_token_hash TEXT NOT NULL UNIQUE,

    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_session_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


-- INDEXES
CREATE INDEX IF NOT EXISTS idx_otp_user
ON otp_codes(user_id);

CREATE INDEX IF NOT EXISTS idx_otp_expiry
ON otp_codes(expires_at);

CREATE INDEX IF NOT EXISTS idx_sessions_user
ON user_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_sessions_expiry
ON user_sessions(expires_at);


-- ============================================================
-- REPRESENTATIVE SQL QUERY 1
-- ============================================================
-- Find all verified students.

SELECT
    id,
    full_name,
    email,
    created_at
FROM users
WHERE role = 'student'
AND is_verified = TRUE
ORDER BY created_at DESC;


-- ============================================================
-- REPRESENTATIVE SQL QUERY 2
-- ============================================================
-- Find active sessions for each user.

SELECT
    u.full_name,
    u.email,
    u.role,
    s.created_at AS session_created_at,
    s.expires_at
FROM users u
JOIN user_sessions s
    ON u.id = s.user_id
WHERE s.expires_at > CURRENT_TIMESTAMP
ORDER BY s.created_at DESC;