-- Migration 005: Guest Stay Access System
-- Adds guest contact info to calendar_events for stay verification
-- Created: 2025-10-12

-- Add guest contact fields to calendar_events
ALTER TABLE calendar_events ADD COLUMN guest_email TEXT;
ALTER TABLE calendar_events ADD COLUMN guest_phone TEXT;

-- Create index for phone lookup (last 4 digits search)
CREATE INDEX IF NOT EXISTS idx_calendar_event_guest_phone ON calendar_events(guest_phone);
CREATE INDEX IF NOT EXISTS idx_calendar_event_guest_email ON calendar_events(guest_email);

-- Create guest_stay_sessions table to track verified guest access
CREATE TABLE IF NOT EXISTS guest_stay_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    calendar_event_id INTEGER NOT NULL,
    guest_phone_last_4 TEXT NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    verified_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    last_accessed TEXT DEFAULT (datetime('now')),
    access_count INTEGER DEFAULT 0,

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (calendar_event_id) REFERENCES calendar_events(id) ON DELETE CASCADE
);

CREATE INDEX idx_guest_session_token ON guest_stay_session(session_token);
CREATE INDEX idx_guest_session_property ON guest_stay_session(property_id);
CREATE INDEX idx_guest_session_expires ON guest_stay_session(expires_at);
