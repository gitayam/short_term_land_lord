-- Migration 007: Booking Request System
-- Create booking_request table for direct booking requests

CREATE TABLE IF NOT EXISTS booking_request (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    property_id TEXT NOT NULL,
    guest_name TEXT NOT NULL,
    guest_email TEXT NOT NULL,
    guest_phone TEXT,
    check_in_date TEXT NOT NULL,
    check_out_date TEXT NOT NULL,
    num_guests INTEGER NOT NULL,
    message TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'cancelled')),
    owner_response TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE
);

-- Index for property owner to view all requests for their properties
CREATE INDEX IF NOT EXISTS idx_booking_request_property ON booking_request(property_id, status);

-- Index for guest email to track their requests
CREATE INDEX IF NOT EXISTS idx_booking_request_email ON booking_request(guest_email);

-- Index for status filtering
CREATE INDEX IF NOT EXISTS idx_booking_request_status ON booking_request(status, created_at);
