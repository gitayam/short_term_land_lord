-- Migration 006: Additional Staff Management Tables
-- Add missing tables for comprehensive staff management
-- Created: 2025-10-12

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

CREATE INDEX IF NOT EXISTS idx_property_assignment_property ON property_assignment(property_id);
CREATE INDEX IF NOT EXISTS idx_property_assignment_worker ON property_assignment(worker_id);
CREATE INDEX IF NOT EXISTS idx_property_assignment_active ON property_assignment(is_active);

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

CREATE INDEX IF NOT EXISTS idx_worker_availability_worker ON worker_availability(worker_id);
CREATE INDEX IF NOT EXISTS idx_worker_availability_date ON worker_availability(specific_date);
CREATE INDEX IF NOT EXISTS idx_worker_availability_dow ON worker_availability(day_of_week);

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
        'repair_rejected',
        'repair_requested'
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

CREATE INDEX IF NOT EXISTS idx_staff_notification_worker ON staff_notification(worker_id);
CREATE INDEX IF NOT EXISTS idx_staff_notification_read ON staff_notification(is_read);
CREATE INDEX IF NOT EXISTS idx_staff_notification_type ON staff_notification(notification_type);
CREATE INDEX IF NOT EXISTS idx_staff_notification_created ON staff_notification(created_at);

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

CREATE INDEX IF NOT EXISTS idx_staff_work_log_worker ON staff_work_log(worker_id);
CREATE INDEX IF NOT EXISTS idx_staff_work_log_property ON staff_work_log(property_id);
CREATE INDEX IF NOT EXISTS idx_staff_work_log_start ON staff_work_log(start_time);
CREATE INDEX IF NOT EXISTS idx_staff_work_log_approved ON staff_work_log(is_approved);
