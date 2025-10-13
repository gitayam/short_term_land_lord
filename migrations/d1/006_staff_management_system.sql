-- Migration 006: Staff Management & Repair Request System
-- Comprehensive system for managing workers (handymen, cleaners, electricians, plumbers)
-- Created: 2025-10-12

-- ================================================================
-- WORKER INVITATIONS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS worker_invitation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('service_staff', 'property_manager')),
    invited_by_id INTEGER NOT NULL,
    invitation_token TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    accepted_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (invited_by_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_worker_invitation_token ON worker_invitation(invitation_token);
CREATE INDEX idx_worker_invitation_email ON worker_invitation(email);
CREATE INDEX idx_worker_invitation_expires ON worker_invitation(expires_at);

-- ================================================================
-- PROPERTY ASSIGNMENTS TABLE
-- Link workers to properties they are responsible for
-- ================================================================
CREATE TABLE IF NOT EXISTS property_assignment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    worker_id INTEGER NOT NULL,
    role_type TEXT CHECK(role_type IN ('cleaner', 'handyman', 'electrician', 'plumber', 'property_manager', 'general')),
    assigned_by_id INTEGER NOT NULL,
    assigned_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER DEFAULT 1,
    notes TEXT,

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by_id) REFERENCES users(id),
    UNIQUE(property_id, worker_id)
);

CREATE INDEX idx_property_assignment_property ON property_assignment(property_id);
CREATE INDEX idx_property_assignment_worker ON property_assignment(worker_id);
CREATE INDEX idx_property_assignment_active ON property_assignment(is_active);

-- ================================================================
-- REPAIR REQUESTS TABLE
-- Track repair and maintenance issues reported for properties
-- ================================================================
CREATE TABLE IF NOT EXISTS repair_request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    reported_by_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT,
    severity TEXT DEFAULT 'medium' CHECK(severity IN ('low', 'medium', 'high', 'urgent')),
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'converted')),
    reviewed_by_id INTEGER,
    reviewed_at TEXT,
    review_notes TEXT,
    converted_task_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (reported_by_id) REFERENCES users(id),
    FOREIGN KEY (reviewed_by_id) REFERENCES users(id),
    FOREIGN KEY (converted_task_id) REFERENCES task(id)
);

CREATE INDEX idx_repair_request_property ON repair_request(property_id);
CREATE INDEX idx_repair_request_status ON repair_request(status);
CREATE INDEX idx_repair_request_severity ON repair_request(severity);
CREATE INDEX idx_repair_request_reported_by ON repair_request(reported_by_id);
CREATE INDEX idx_repair_request_created ON repair_request(created_at);

-- ================================================================
-- REPAIR REQUEST IMAGES TABLE
-- Store images attached to repair requests
-- ================================================================
CREATE TABLE IF NOT EXISTS repair_request_image (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_request_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    caption TEXT,
    uploaded_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (repair_request_id) REFERENCES repair_request(id) ON DELETE CASCADE
);

CREATE INDEX idx_repair_request_image_request ON repair_request_image(repair_request_id);

-- ================================================================
-- WORKER AVAILABILITY TABLE
-- Track when workers are available/unavailable
-- ================================================================
CREATE TABLE IF NOT EXISTS worker_availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,
    day_of_week INTEGER CHECK(day_of_week BETWEEN 0 AND 6), -- 0=Sunday, 6=Saturday, NULL=specific date
    specific_date TEXT, -- YYYY-MM-DD format for one-time availability
    start_time TEXT NOT NULL, -- HH:MM format
    end_time TEXT NOT NULL, -- HH:MM format
    is_available INTEGER DEFAULT 1, -- 0 for blocked/unavailable time
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_worker_availability_worker ON worker_availability(worker_id);
CREATE INDEX idx_worker_availability_date ON worker_availability(specific_date);
CREATE INDEX idx_worker_availability_dow ON worker_availability(day_of_week);

-- ================================================================
-- STAFF NOTIFICATIONS TABLE
-- Specific notifications for staff about assignments, repairs, etc.
-- ================================================================
CREATE TABLE IF NOT EXISTS staff_notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL CHECK(notification_type IN (
        'repair_assigned',
        'task_assigned',
        'property_assigned',
        'schedule_change',
        'repair_approved',
        'repair_rejected'
    )),
    related_id INTEGER, -- ID of related repair_request, task, or property
    related_type TEXT CHECK(related_type IN ('repair_request', 'task', 'property')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    link TEXT,
    is_read INTEGER DEFAULT 0,
    is_emailed INTEGER DEFAULT 0,
    emailed_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_staff_notification_worker ON staff_notification(worker_id);
CREATE INDEX idx_staff_notification_read ON staff_notification(is_read);
CREATE INDEX idx_staff_notification_type ON staff_notification(notification_type);
CREATE INDEX idx_staff_notification_created ON staff_notification(created_at);

-- ================================================================
-- STAFF WORK LOG TABLE
-- Track actual work performed by staff (for payroll/invoicing)
-- ================================================================
CREATE TABLE IF NOT EXISTS staff_work_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    task_id INTEGER,
    repair_request_id INTEGER,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_minutes INTEGER,
    work_type TEXT CHECK(work_type IN ('cleaning', 'repair', 'maintenance', 'inspection', 'other')),
    description TEXT,
    notes TEXT,
    photos TEXT, -- JSON array of photo URLs
    is_approved INTEGER DEFAULT 0,
    approved_by_id INTEGER,
    approved_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES task(id),
    FOREIGN KEY (repair_request_id) REFERENCES repair_request(id),
    FOREIGN KEY (approved_by_id) REFERENCES users(id)
);

CREATE INDEX idx_staff_work_log_worker ON staff_work_log(worker_id);
CREATE INDEX idx_staff_work_log_property ON staff_work_log(property_id);
CREATE INDEX idx_staff_work_log_start ON staff_work_log(start_time);
CREATE INDEX idx_staff_work_log_approved ON staff_work_log(is_approved);
