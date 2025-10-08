-- Short Term Land Lord - Initial D1 Database Schema
-- Created: 2025-10-08
-- Migration: 001_initial_schema.sql

-- ================================================================
-- USERS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    first_name TEXT,
    last_name TEXT,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    is_suspended INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER DEFAULT 1,
    last_login TEXT,
    authentik_id TEXT UNIQUE,
    signal_identity TEXT UNIQUE,
    attributes TEXT, -- JSON
    is_admin INTEGER DEFAULT 0,

    -- Profile fields
    profile_image TEXT,
    timezone TEXT DEFAULT 'UTC',
    language TEXT DEFAULT 'en',
    theme_preference TEXT DEFAULT 'light',
    default_dashboard_view TEXT DEFAULT 'tasks',
    default_calendar_view TEXT DEFAULT 'month',
    default_task_sort TEXT DEFAULT 'due_date',

    -- Notification preferences
    email_notifications INTEGER DEFAULT 1,
    sms_notifications INTEGER DEFAULT 0,
    in_app_notifications INTEGER DEFAULT 1,
    notification_frequency TEXT DEFAULT 'immediate',

    -- Security settings
    two_factor_enabled INTEGER DEFAULT 0,
    two_factor_method TEXT,
    last_password_change TEXT,

    -- Account lockout
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TEXT,
    last_failed_login TEXT,

    -- Connected services
    google_calendar_connected INTEGER DEFAULT 0,
    google_calendar_token TEXT,
    twilio_phone_verified INTEGER DEFAULT 0,
    slack_workspace_id TEXT,

    -- Guest user fields
    invitation_code_id INTEGER,
    email_verified INTEGER DEFAULT 0,
    email_verification_token TEXT,
    email_verification_sent_at TEXT,
    guest_preferences TEXT -- JSON
);

CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_phone ON users(phone);
CREATE INDEX idx_user_role ON users(role);
CREATE INDEX idx_user_created ON users(created_at);

-- ================================================================
-- PROPERTIES TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS property (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    name TEXT,
    address TEXT NOT NULL,
    description TEXT,
    property_type TEXT DEFAULT 'house',
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    -- Address components
    street_address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    country TEXT,

    -- Geographic coordinates
    latitude REAL,
    longitude REAL,

    -- Property details
    bedrooms INTEGER,
    bathrooms REAL,
    square_feet INTEGER,
    year_built INTEGER,

    -- Waste collection
    trash_day TEXT,
    trash_schedule_type TEXT,
    trash_schedule_details TEXT, -- JSON
    recycling_day TEXT,
    recycling_schedule_type TEXT,
    recycling_schedule_details TEXT, -- JSON
    recycling_notes TEXT,

    -- Utilities
    internet_provider TEXT,
    internet_account TEXT,
    internet_contact TEXT,
    electric_provider TEXT,
    electric_account TEXT,
    electric_contact TEXT,
    water_provider TEXT,
    water_account TEXT,
    water_contact TEXT,
    trash_provider TEXT,
    trash_account TEXT,
    trash_contact TEXT,

    -- Access information
    cleaning_supplies_location TEXT,
    wifi_network TEXT,
    wifi_password TEXT,
    special_instructions TEXT,
    entry_instructions TEXT,

    -- Cleaner-specific
    total_beds INTEGER,
    bed_sizes TEXT,
    number_of_tvs INTEGER,
    number_of_showers INTEGER,
    number_of_tubs INTEGER,

    -- Calendar integration
    ical_url TEXT,

    -- Guest access
    guest_access_enabled INTEGER DEFAULT 0,
    guest_access_token TEXT UNIQUE,
    guest_rules TEXT,
    guest_checkin_instructions TEXT,
    guest_checkout_instructions TEXT,
    guest_wifi_instructions TEXT,
    local_attractions TEXT,
    emergency_contact TEXT,
    guest_faq TEXT,

    -- Check-in/out times
    checkin_time TEXT,
    checkout_time TEXT,

    -- Access tokens
    guide_book_token TEXT UNIQUE,
    worker_calendar_token TEXT UNIQUE,
    booking_calendar_token TEXT UNIQUE,
    booking_calendar_enabled INTEGER DEFAULT 0,

    -- Color theme
    color TEXT,

    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE INDEX idx_property_owner ON property(owner_id);
CREATE INDEX idx_property_status ON property(status);
CREATE INDEX idx_property_type ON property(property_type);
CREATE INDEX idx_property_created ON property(created_at);
CREATE INDEX idx_property_city_state ON property(city, state);

-- ================================================================
-- PROPERTY CALENDARS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS property_calendar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    platform_name TEXT NOT NULL, -- airbnb, vrbo, booking, direct, blocked
    ical_url TEXT,
    is_active INTEGER DEFAULT 1,
    last_synced TEXT,
    sync_status TEXT,
    sync_error TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (property_id) REFERENCES property(id)
);

CREATE INDEX idx_calendar_property ON property_calendar(property_id);
CREATE INDEX idx_calendar_platform ON property_calendar(platform_name);

-- ================================================================
-- CALENDAR EVENTS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_calendar_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,

    -- Event details
    title TEXT NOT NULL,
    start_date TEXT NOT NULL, -- ISO 8601 date
    end_date TEXT NOT NULL, -- ISO 8601 date

    -- External platform
    source TEXT NOT NULL, -- airbnb, vrbo, booking, etc.
    external_id TEXT,

    -- Booking details
    guest_name TEXT,
    guest_count INTEGER,
    booking_amount REAL,
    booking_status TEXT,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (property_calendar_id) REFERENCES property_calendar(id),
    FOREIGN KEY (property_id) REFERENCES property(id)
);

CREATE INDEX idx_calendar_event_property ON calendar_events(property_id);
CREATE INDEX idx_calendar_event_dates ON calendar_events(start_date, end_date);
CREATE INDEX idx_calendar_event_source ON calendar_events(source);

-- ================================================================
-- TASKS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'PENDING',
    priority TEXT DEFAULT 'MEDIUM',
    due_date TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    creator_id INTEGER NOT NULL,
    property_id INTEGER,
    assign_to_next_cleaner INTEGER DEFAULT 0,

    -- Recurring task fields
    is_recurring INTEGER DEFAULT 0,
    recurrence_pattern TEXT DEFAULT 'none',
    recurrence_interval INTEGER DEFAULT 1,
    recurrence_end_date TEXT,

    -- Additional fields
    notes TEXT,
    linked_to_checkout INTEGER DEFAULT 0,
    calendar_id INTEGER,
    tags TEXT,
    location TEXT,
    severity TEXT,
    photo_paths TEXT, -- JSON array

    FOREIGN KEY (creator_id) REFERENCES users(id),
    FOREIGN KEY (property_id) REFERENCES property(id),
    FOREIGN KEY (calendar_id) REFERENCES property_calendar(id)
);

CREATE INDEX idx_task_status ON task(status);
CREATE INDEX idx_task_priority ON task(priority);
CREATE INDEX idx_task_due_date ON task(due_date);
CREATE INDEX idx_task_creator ON task(creator_id);
CREATE INDEX idx_task_property ON task(property_id);
CREATE INDEX idx_task_created ON task(created_at);
CREATE INDEX idx_task_status_due ON task(status, due_date);

-- ================================================================
-- TASK ASSIGNMENTS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS task_assignment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    assigned_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,

    FOREIGN KEY (task_id) REFERENCES task(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_task_assignment_task ON task_assignment(task_id);
CREATE INDEX idx_task_assignment_user ON task_assignment(user_id);

-- ================================================================
-- TASK PROPERTIES TABLE (Many-to-Many)
-- ================================================================
CREATE TABLE IF NOT EXISTS task_property (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,

    FOREIGN KEY (task_id) REFERENCES task(id),
    FOREIGN KEY (property_id) REFERENCES property(id),
    UNIQUE(task_id, property_id)
);

-- ================================================================
-- CLEANING SESSIONS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS cleaning_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    cleaner_id INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    status TEXT DEFAULT 'in_progress',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (property_id) REFERENCES property(id),
    FOREIGN KEY (cleaner_id) REFERENCES users(id)
);

CREATE INDEX idx_cleaning_property ON cleaning_session(property_id);
CREATE INDEX idx_cleaning_cleaner ON cleaning_session(cleaner_id);
CREATE INDEX idx_cleaning_start ON cleaning_session(start_time);

-- ================================================================
-- INVENTORY CATALOG ITEMS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS inventory_catalog_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL DEFAULT 'general',
    unit TEXT NOT NULL,
    unit_price REAL NOT NULL,
    sku TEXT,
    barcode TEXT UNIQUE,
    purchase_link TEXT,
    currency TEXT DEFAULT 'USD',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (creator_id) REFERENCES users(id)
);

-- ================================================================
-- INVENTORY ITEMS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS inventory_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    catalog_item_id INTEGER,
    name TEXT NOT NULL,
    quantity INTEGER DEFAULT 0,
    min_quantity INTEGER DEFAULT 0,
    unit TEXT,
    category TEXT,
    location TEXT,
    notes TEXT,
    last_restocked TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (property_id) REFERENCES property(id),
    FOREIGN KEY (catalog_item_id) REFERENCES inventory_catalog_item(id)
);

CREATE INDEX idx_inventory_property ON inventory_item(property_id);

-- ================================================================
-- NOTIFICATIONS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    link TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_notification_user ON notification(user_id);
CREATE INDEX idx_notification_read ON notification(is_read);
CREATE INDEX idx_notification_created ON notification(created_at);

-- ================================================================
-- GUEST INVITATIONS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS guest_invitation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    property_id INTEGER,
    created_by_id INTEGER NOT NULL,
    max_uses INTEGER DEFAULT 1,
    times_used INTEGER DEFAULT 0,
    expires_at TEXT,
    is_active INTEGER DEFAULT 1,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (property_id) REFERENCES property(id),
    FOREIGN KEY (created_by_id) REFERENCES users(id)
);

CREATE INDEX idx_invitation_code ON guest_invitation(code);
CREATE INDEX idx_invitation_property ON guest_invitation(property_id);

-- ================================================================
-- SESSION CACHE TABLE (for JWT sessions)
-- ================================================================
CREATE TABLE IF NOT EXISTS session_cache (
    session_token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_data TEXT NOT NULL, -- JSON
    expires_at TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_session_user ON session_cache(user_id);
CREATE INDEX idx_session_expires ON session_cache(expires_at);
