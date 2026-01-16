-- Migration 026: Add email field to users table
-- Email required for password reset and notifications
-- NOT unique: same person may have accounts in multiple labs

ALTER TABLE users
ADD COLUMN email VARCHAR(100) NOT NULL DEFAULT 'change@me.org' AFTER nickname;

-- Set placeholder emails for existing users based on nickname
UPDATE users SET email = CONCAT(nickname, '@change.me');

-- Add index for search performance (not unique)
ALTER TABLE users ADD INDEX idx_users_email (email);
