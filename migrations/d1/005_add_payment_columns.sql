-- ================================================================
-- ADD PAYMENT TRACKING TO BOOKING_REQUEST TABLE
-- Migration: 005_add_payment_columns.sql
-- ================================================================

-- Add payment tracking columns to existing booking_request table
ALTER TABLE booking_request ADD COLUMN estimated_total REAL;
ALTER TABLE booking_request ADD COLUMN deposit_amount REAL;
ALTER TABLE booking_request ADD COLUMN payment_status TEXT DEFAULT 'pending';
ALTER TABLE booking_request ADD COLUMN stripe_payment_link TEXT;
ALTER TABLE booking_request ADD COLUMN stripe_payment_intent_id TEXT;
ALTER TABLE booking_request ADD COLUMN approved_at TEXT;
ALTER TABLE booking_request ADD COLUMN approved_by_id INTEGER;

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_booking_request_payment_status ON booking_request(payment_status);
CREATE INDEX IF NOT EXISTS idx_booking_request_stripe_intent ON booking_request(stripe_payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_booking_request_approved_by ON booking_request(approved_by_id);
