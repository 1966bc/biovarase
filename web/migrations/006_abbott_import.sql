-- Migration: 006_abbott_import.sql
-- Description: Create tracking table for Abbott QC file imports
-- Author: Giuseppe Costanzi
-- Date: 2026-01-09

-- Track imported Abbott files to avoid duplicates
CREATE TABLE IF NOT EXISTS abbott_imported_files (
    file_id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    records_count INT DEFAULT 0,
    UNIQUE KEY uk_filename (filename)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Index for faster lookups
CREATE INDEX idx_imported_at ON abbott_imported_files (imported_at);
