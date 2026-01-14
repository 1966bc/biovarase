-- Migration 025: Add created_by to notes table for permission control
-- Date: 2026-01
--
-- This migration:
-- 1. Adds created_by field to track note author
-- 2. Adds created_at timestamp
-- 3. Only the creator (or admin) can modify their notes

-- Add created_by column (FK to users)
ALTER TABLE notes
ADD COLUMN created_by INT UNSIGNED NULL AFTER status,
ADD COLUMN created_at DATETIME NULL AFTER created_by;

-- Add foreign key constraint
ALTER TABLE notes
ADD CONSTRAINT fk_notes_created_by
FOREIGN KEY (created_by) REFERENCES users(user_id)
ON DELETE SET NULL ON UPDATE CASCADE;

-- Add index for efficient filtering by creator
CREATE INDEX idx_notes_created_by ON notes(created_by);

-- Update existing notes to set created_at to modified date (best effort)
UPDATE notes SET created_at = modified WHERE created_at IS NULL;
