-- ================================================================
-- FINANCIAL TRACKING MIGRATION
-- Add comprehensive expense tracking and financial analytics
-- ================================================================

-- ================================================================
-- RECURRING EXPENSES TABLE
-- Templates for recurring expenses like utilities, insurance
-- ================================================================
CREATE TABLE IF NOT EXISTS recurring_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,

    -- Expense details
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- utilities, insurance, property_taxes, etc.
    vendor TEXT,
    description TEXT,

    -- Recurring schedule
    frequency TEXT NOT NULL, -- monthly, quarterly, annually
    amount REAL,
    due_day INTEGER, -- Day of month due (1-31)

    -- Status
    is_active INTEGER DEFAULT 1,
    auto_generate INTEGER DEFAULT 1,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    created_by_id INTEGER NOT NULL,

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES users(id)
);

CREATE INDEX idx_recurring_expenses_property ON recurring_expenses(property_id);
CREATE INDEX idx_recurring_expenses_category ON recurring_expenses(category);
CREATE INDEX idx_recurring_expenses_active ON recurring_expenses(is_active);

-- ================================================================
-- EXPENSES TABLE
-- Individual expense entries - both one-time and recurring
-- ================================================================
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER, -- NULL = business expense
    recurring_expense_id INTEGER,

    -- Expense details
    category TEXT NOT NULL, -- utilities, insurance, repairs_maintenance, supplies, etc.
    vendor TEXT,
    description TEXT NOT NULL,
    amount REAL NOT NULL,

    -- Tax and accounting
    tax_deductible INTEGER DEFAULT 1,
    business_percentage INTEGER DEFAULT 100, -- % business use (for mixed-use)

    -- Dates
    expense_date TEXT NOT NULL DEFAULT (date('now')),
    due_date TEXT,
    paid_date TEXT,

    -- Payment tracking
    status TEXT DEFAULT 'draft', -- draft, submitted, approved, paid, disputed
    payment_method TEXT, -- cash, check, credit_card, bank_transfer, digital_payment
    check_number TEXT,

    -- Receipt management
    receipt_url TEXT,
    receipt_filename TEXT,

    -- Relationships
    invoice_id INTEGER,
    task_id INTEGER,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    created_by_id INTEGER NOT NULL,
    approved_by_id INTEGER,

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (recurring_expense_id) REFERENCES recurring_expenses(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_id) REFERENCES users(id),
    FOREIGN KEY (approved_by_id) REFERENCES users(id),
    FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE SET NULL
);

CREATE INDEX idx_expenses_property ON expenses(property_id);
CREATE INDEX idx_expenses_category ON expenses(category);
CREATE INDEX idx_expenses_status ON expenses(status);
CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_expenses_due_date ON expenses(due_date);
CREATE INDEX idx_expenses_created_by ON expenses(created_by_id);

-- ================================================================
-- REVENUE TABLE
-- Track all revenue streams (bookings, additional services, etc.)
-- ================================================================
CREATE TABLE IF NOT EXISTS revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,

    -- Revenue details
    source TEXT NOT NULL, -- booking, cleaning_fee, pet_fee, damage_deposit, other
    description TEXT NOT NULL,
    amount REAL NOT NULL,

    -- Dates
    revenue_date TEXT NOT NULL DEFAULT (date('now')),
    received_date TEXT,

    -- Payment tracking
    status TEXT DEFAULT 'pending', -- pending, received, refunded
    payment_method TEXT,

    -- Relationships
    booking_id INTEGER, -- Link to calendar_events if from booking

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    created_by_id INTEGER NOT NULL,

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (booking_id) REFERENCES calendar_events(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_id) REFERENCES users(id)
);

CREATE INDEX idx_revenue_property ON revenue(property_id);
CREATE INDEX idx_revenue_source ON revenue(source);
CREATE INDEX idx_revenue_status ON revenue(status);
CREATE INDEX idx_revenue_date ON revenue(revenue_date);

-- ================================================================
-- FINANCIAL REPORTS TABLE
-- Pre-computed financial reports for fast dashboard loading
-- ================================================================
CREATE TABLE IF NOT EXISTS financial_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Report scope
    property_id INTEGER, -- NULL = all properties
    report_type TEXT NOT NULL, -- monthly, quarterly, annual, ytd
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,

    -- Calculated metrics (stored as JSON)
    total_revenue REAL DEFAULT 0,
    total_expenses REAL DEFAULT 0,
    net_income REAL DEFAULT 0,
    profit_margin REAL DEFAULT 0,

    -- Category breakdowns (JSON)
    expense_by_category TEXT, -- JSON object
    revenue_by_source TEXT, -- JSON object

    -- Metadata
    generated_at TEXT DEFAULT (datetime('now')),
    generated_by_id INTEGER NOT NULL,

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (generated_by_id) REFERENCES users(id)
);

CREATE INDEX idx_financial_reports_property ON financial_reports(property_id);
CREATE INDEX idx_financial_reports_type ON financial_reports(report_type);
CREATE INDEX idx_financial_reports_period ON financial_reports(period_start, period_end);

-- ================================================================
-- EXPENSE CATEGORIES REFERENCE
-- Standard IRS-compliant expense categories
-- ================================================================

-- Standard categories:
-- - utilities: Electricity, water, gas, internet, cable
-- - insurance: Property, liability, business insurance
-- - property_taxes: Real estate taxes
-- - mortgage_interest: Loan interest (deductible portion)
-- - repairs_maintenance: Ongoing maintenance, repairs
-- - supplies: Cleaning supplies, amenities, consumables
-- - professional_services: Legal, accounting, property management
-- - marketing: Advertising, listing fees, photography
-- - travel: Property visits, business travel
-- - depreciation: Asset depreciation
-- - contractor_payments: Independent contractor payments
-- - employee_wages: W2 employee payments
-- - amenities: Welcome baskets, toiletries, coffee
-- - linens_replacement: Towels, sheets, pillows
-- - furniture_replacement: Furniture, appliances
-- - improvements: Property improvements (capitalized)
-- - equipment: Major equipment purchases

-- ================================================================
-- DATA MIGRATION NOTES
-- ================================================================
-- If migrating from existing system:
-- 1. Import historical expenses from old system
-- 2. Set up recurring expenses for ongoing costs
-- 3. Generate initial financial reports for baseline
-- 4. Link existing bookings to revenue entries
