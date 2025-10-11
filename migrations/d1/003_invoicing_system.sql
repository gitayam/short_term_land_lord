-- ================================================================
-- INVOICING SYSTEM MIGRATION
-- Add invoice management for guests and clients
-- ================================================================

-- ================================================================
-- INVOICES TABLE
-- Main invoice records
-- ================================================================
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,
    booking_id INTEGER,

    -- Invoice details
    invoice_number TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,

    -- Recipient
    recipient_name TEXT NOT NULL,
    recipient_email TEXT,
    recipient_address TEXT,

    -- Amounts
    subtotal REAL NOT NULL DEFAULT 0,
    tax_rate REAL DEFAULT 0,
    tax_amount REAL DEFAULT 0,
    discount_amount REAL DEFAULT 0,
    total_amount REAL NOT NULL,

    -- Dates
    invoice_date TEXT NOT NULL DEFAULT (date('now')),
    due_date TEXT,
    paid_date TEXT,

    -- Status
    status TEXT DEFAULT 'draft', -- draft, sent, paid, overdue, cancelled
    payment_method TEXT,

    -- Notes
    notes TEXT,
    terms TEXT,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    created_by_id INTEGER NOT NULL,

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (booking_id) REFERENCES calendar_events(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_id) REFERENCES users(id)
);

CREATE INDEX idx_invoices_property ON invoices(property_id);
CREATE INDEX idx_invoices_booking ON invoices(booking_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);
CREATE INDEX idx_invoices_date ON invoices(invoice_date);

-- ================================================================
-- INVOICE ITEMS TABLE
-- Line items for each invoice
-- ================================================================
CREATE TABLE IF NOT EXISTS invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,

    -- Item details
    description TEXT NOT NULL,
    quantity REAL DEFAULT 1,
    unit_price REAL NOT NULL,
    amount REAL NOT NULL,

    -- Optional categorization
    item_type TEXT, -- accommodation, cleaning, pet_fee, damage_deposit, etc.

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

CREATE INDEX idx_invoice_items_invoice ON invoice_items(invoice_id);

-- ================================================================
-- INVOICE PAYMENTS TABLE
-- Track payments against invoices
-- ================================================================
CREATE TABLE IF NOT EXISTS invoice_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,

    -- Payment details
    amount REAL NOT NULL,
    payment_date TEXT NOT NULL DEFAULT (date('now')),
    payment_method TEXT, -- credit_card, bank_transfer, cash, check, etc.

    -- Transaction details
    transaction_id TEXT,
    reference_number TEXT,
    notes TEXT,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    created_by_id INTEGER NOT NULL,

    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES users(id)
);

CREATE INDEX idx_invoice_payments_invoice ON invoice_payments(invoice_id);
CREATE INDEX idx_invoice_payments_date ON invoice_payments(payment_date);

-- ================================================================
-- SAMPLE DATA
-- Generate invoice numbers sequence
-- ================================================================

-- Note: Invoice numbers should be generated programmatically
-- Format: INV-YYYYMMDD-XXXX (e.g., INV-20251011-0001)

-- ================================================================
-- VIEWS FOR REPORTING
-- ================================================================

-- Invoice summary view with payment status
CREATE VIEW IF NOT EXISTS invoice_summary AS
SELECT
    i.id,
    i.invoice_number,
    i.property_id,
    p.name as property_name,
    i.recipient_name,
    i.total_amount,
    i.invoice_date,
    i.due_date,
    i.status,
    COALESCE(SUM(ip.amount), 0) as paid_amount,
    i.total_amount - COALESCE(SUM(ip.amount), 0) as balance_due,
    CASE
        WHEN i.status = 'paid' THEN 'paid'
        WHEN i.due_date < date('now') AND i.status != 'paid' THEN 'overdue'
        ELSE i.status
    END as computed_status
FROM invoices i
LEFT JOIN property p ON i.property_id = p.id
LEFT JOIN invoice_payments ip ON i.id = ip.invoice_id
GROUP BY i.id;
