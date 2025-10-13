-- ================================================================
-- BOOKING SYSTEM MIGRATION
-- Add booking request and payment tracking tables
-- ================================================================

-- ================================================================
-- BOOKING REQUESTS TABLE
-- Note: Table already exists from previous migration
-- Additional columns added in migration 005_add_payment_columns.sql
-- ================================================================

-- ================================================================
-- PAYMENT TRANSACTIONS TABLE
-- Track all payment transactions (from Stripe, etc.)
-- ================================================================
CREATE TABLE IF NOT EXISTS payment_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Transaction details
    transaction_type TEXT NOT NULL, -- booking_payment, booking_deposit, refund, addon_payment
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    status TEXT DEFAULT 'pending', -- pending, processing, succeeded, failed, refunded

    -- Stripe integration
    stripe_payment_intent_id TEXT UNIQUE,
    stripe_charge_id TEXT,
    stripe_refund_id TEXT,
    stripe_payment_method TEXT,

    -- References
    property_id INTEGER,
    booking_request_id INTEGER,
    calendar_event_id INTEGER, -- Link to confirmed booking

    -- Additional details
    description TEXT NOT NULL,
    reference_id TEXT, -- External reference number
    payment_date TEXT,
    refund_date TEXT,
    refund_amount REAL,
    refund_reason TEXT,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE SET NULL,
    FOREIGN KEY (booking_request_id) REFERENCES booking_request(id) ON DELETE SET NULL,
    FOREIGN KEY (calendar_event_id) REFERENCES calendar_events(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_payment_trans_type ON payment_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_payment_trans_status ON payment_transactions(status);
CREATE INDEX IF NOT EXISTS idx_payment_trans_stripe_intent ON payment_transactions(stripe_payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_payment_trans_property ON payment_transactions(property_id);
CREATE INDEX IF NOT EXISTS idx_payment_trans_booking_req ON payment_transactions(booking_request_id);
CREATE INDEX IF NOT EXISTS idx_payment_trans_calendar ON payment_transactions(calendar_event_id);
CREATE INDEX IF NOT EXISTS idx_payment_trans_date ON payment_transactions(payment_date);

-- ================================================================
-- UPDATE CALENDAR_EVENTS TABLE
-- Add payment tracking fields to calendar events
-- ================================================================

-- Note: SQLite doesn't support ALTER TABLE to add columns easily,
-- so we'll handle this via the application layer for now.
-- In a future migration, we can:
-- 1. Create new table with additional columns
-- 2. Copy data
-- 3. Drop old table
-- 4. Rename new table

-- For now, we'll track payment info via payment_transactions table
-- linked by calendar_event_id

-- ================================================================
-- VIEWS FOR REPORTING
-- ================================================================

-- Booking request summary with payment status
CREATE VIEW IF NOT EXISTS booking_request_summary AS
SELECT
    br.id,
    br.property_id,
    p.name as property_name,
    p.address as property_address,
    br.guest_name,
    br.guest_email,
    br.guest_phone,
    br.check_in_date,
    br.check_out_date,
    br.num_guests,
    br.status,
    br.payment_status,
    br.estimated_total,
    br.deposit_amount,
    COALESCE(SUM(pt.amount), 0) as total_paid,
    br.created_at,
    br.updated_at,
    u.first_name || ' ' || u.last_name as approved_by_name
FROM booking_request br
JOIN property p ON br.property_id = p.id
LEFT JOIN users u ON br.approved_by_id = u.id
LEFT JOIN payment_transactions pt ON pt.booking_request_id = br.id AND pt.status = 'succeeded'
GROUP BY br.id;

-- Payment transactions summary
CREATE VIEW IF NOT EXISTS payment_summary AS
SELECT
    pt.id,
    pt.transaction_type,
    pt.amount,
    pt.status,
    pt.payment_date,
    p.name as property_name,
    br.guest_name,
    br.guest_email,
    ce.title as booking_title,
    ce.start_date as check_in_date,
    ce.end_date as check_out_date
FROM payment_transactions pt
LEFT JOIN property p ON pt.property_id = p.id
LEFT JOIN booking_request br ON pt.booking_request_id = br.id
LEFT JOIN calendar_events ce ON pt.calendar_event_id = ce.id
ORDER BY pt.created_at DESC;

-- ================================================================
-- NOTES
-- ================================================================
-- This migration adds:
-- 1. booking_request table for approval workflow
-- 2. payment_transactions table for Stripe payments
-- 3. Views for reporting and analytics
--
-- Usage:
-- - Guests submit booking requests (pending approval)
-- - Owner approves → creates calendar event + payment link
-- - Guest pays via Stripe → payment_transaction created
-- - On successful payment → booking confirmed
--
-- Payment Flow:
-- 1. Guest submits booking request
-- 2. Owner approves + generates Stripe payment link
-- 3. Link sent to guest via email
-- 4. Guest pays → Stripe webhook creates payment_transaction
-- 5. On success → calendar_event.booking_status = 'confirmed'
