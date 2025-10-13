-- Workforce Management & Repair Requests Migration

-- 1. Add role to users table (for workforce management)
-- Users can be: property_owner, service_staff, property_manager, admin
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'property_owner';
ALTER TABLE users ADD COLUMN phone TEXT;
ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1;

-- 2. Property assignments - which workers can access which properties
CREATE TABLE IF NOT EXISTS property_assignment (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    property_id TEXT NOT NULL,
    worker_id TEXT NOT NULL,
    assigned_by_id TEXT NOT NULL,
    assigned_at DATETIME DEFAULT (datetime('now')),
    notes TEXT,
    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_property_assignment_property ON property_assignment(property_id);
CREATE INDEX IF NOT EXISTS idx_property_assignment_worker ON property_assignment(worker_id);

-- 3. Worker invitations
CREATE TABLE IF NOT EXISTS worker_invitation (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'service_staff',
    invited_by_id TEXT NOT NULL,
    invitation_token TEXT NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    accepted_at DATETIME,
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (invited_by_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_worker_invitation_email ON worker_invitation(email);
CREATE INDEX IF NOT EXISTS idx_worker_invitation_token ON worker_invitation(invitation_token);

-- 4. Repair Requests
CREATE TABLE IF NOT EXISTS repair_request (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    property_id TEXT NOT NULL,
    reported_by_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT,
    severity TEXT DEFAULT 'medium' CHECK(severity IN ('low', 'medium', 'high', 'urgent')),
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'converted')),
    reviewed_by_id TEXT,
    reviewed_at DATETIME,
    review_notes TEXT,
    converted_task_id TEXT,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE,
    FOREIGN KEY (reported_by_id) REFERENCES users(id),
    FOREIGN KEY (reviewed_by_id) REFERENCES users(id),
    FOREIGN KEY (converted_task_id) REFERENCES task(id)
);

CREATE INDEX IF NOT EXISTS idx_repair_request_property ON repair_request(property_id);
CREATE INDEX IF NOT EXISTS idx_repair_request_status ON repair_request(status);
CREATE INDEX IF NOT EXISTS idx_repair_request_severity ON repair_request(severity);

-- 5. Repair request images
CREATE TABLE IF NOT EXISTS repair_request_image (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    repair_request_id TEXT NOT NULL,
    image_url TEXT NOT NULL,
    uploaded_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (repair_request_id) REFERENCES repair_request(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_repair_request_image_request ON repair_request_image(repair_request_id);

-- 6. Task Templates
CREATE TABLE IF NOT EXISTS task_template (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    estimated_duration INTEGER,
    default_priority TEXT DEFAULT 'medium' CHECK(default_priority IN ('low', 'medium', 'high', 'urgent')),
    checklist_items TEXT,
    created_by_id TEXT NOT NULL,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (created_by_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_task_template_category ON task_template(category);

-- 7. Task feedback
CREATE TABLE IF NOT EXISTS task_feedback (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    comment TEXT,
    submitted_by_id TEXT NOT NULL,
    submitted_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE,
    FOREIGN KEY (submitted_by_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_task_feedback_task ON task_feedback(task_id);

-- 8. Task media (photos/videos)
CREATE TABLE IF NOT EXISTS task_media (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL,
    media_type TEXT CHECK(media_type IN ('photo', 'video')),
    media_url TEXT NOT NULL,
    caption TEXT,
    uploaded_by_id TEXT NOT NULL,
    uploaded_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_task_media_task ON task_media(task_id);

-- 9. Property images
CREATE TABLE IF NOT EXISTS property_image (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    property_id TEXT NOT NULL,
    image_url TEXT NOT NULL,
    caption TEXT,
    display_order INTEGER DEFAULT 0,
    is_primary INTEGER DEFAULT 0,
    uploaded_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_property_image_property ON property_image(property_id);

-- 10. Property rooms
CREATE TABLE IF NOT EXISTS property_room (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    property_id TEXT NOT NULL,
    room_type TEXT NOT NULL CHECK(room_type IN ('bedroom', 'bathroom', 'kitchen', 'living_room', 'other')),
    name TEXT,
    bed_type TEXT,
    bed_count INTEGER DEFAULT 0,
    has_ensuite INTEGER DEFAULT 0,
    amenities TEXT,
    notes TEXT,
    display_order INTEGER DEFAULT 0,
    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_property_room_property ON property_room(property_id);

-- 11. Guest reviews
CREATE TABLE IF NOT EXISTS guest_review (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    property_id TEXT NOT NULL,
    guest_name TEXT NOT NULL,
    guest_email TEXT,
    booking_id TEXT,
    rating TEXT CHECK(rating IN ('bad', 'ok', 'good')),
    comment TEXT,
    cleanliness_rating INTEGER CHECK(cleanliness_rating >= 1 AND cleanliness_rating <= 5),
    communication_rating INTEGER CHECK(communication_rating >= 1 AND communication_rating <= 5),
    accuracy_rating INTEGER CHECK(accuracy_rating >= 1 AND accuracy_rating <= 5),
    location_rating INTEGER CHECK(location_rating >= 1 AND location_rating <= 5),
    value_rating INTEGER CHECK(value_rating >= 1 AND value_rating <= 5),
    is_public INTEGER DEFAULT 0,
    reviewed_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_guest_review_property ON guest_review(property_id);

-- 12. Service pricing (for invoicing)
CREATE TABLE IF NOT EXISTS service_price (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    service_name TEXT NOT NULL,
    service_type TEXT,
    unit_price REAL NOT NULL,
    unit TEXT DEFAULT 'per service',
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- 13. Invoice line items
CREATE TABLE IF NOT EXISTS invoice_line_item (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    invoice_id TEXT NOT NULL,
    service_price_id TEXT,
    description TEXT NOT NULL,
    quantity REAL DEFAULT 1,
    unit_price REAL NOT NULL,
    total REAL NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoice(id) ON DELETE CASCADE,
    FOREIGN KEY (service_price_id) REFERENCES service_price(id)
);

CREATE INDEX IF NOT EXISTS idx_invoice_line_item_invoice ON invoice_line_item(invoice_id);

-- 14. Invoice comments
CREATE TABLE IF NOT EXISTS invoice_comment (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    invoice_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (invoice_id) REFERENCES invoice(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_invoice_comment_invoice ON invoice_comment(invoice_id);

-- 15. Notifications
CREATE TABLE IF NOT EXISTS notification (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('task_assignment', 'task_reminder', 'calendar_update', 'task_completed', 'inventory_low', 'repair_request')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    link_url TEXT,
    is_read INTEGER DEFAULT 0,
    sent_via_email INTEGER DEFAULT 0,
    sent_via_sms INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notification_user ON notification(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_read ON notification(is_read);

-- 16. Inventory transfers
CREATE TABLE IF NOT EXISTS inventory_transfer (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    from_property_id TEXT NOT NULL,
    to_property_id TEXT NOT NULL,
    catalog_item_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    transferred_by_id TEXT NOT NULL,
    notes TEXT,
    transferred_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (from_property_id) REFERENCES property(id),
    FOREIGN KEY (to_property_id) REFERENCES property(id),
    FOREIGN KEY (catalog_item_id) REFERENCES inventory_catalog_item(id),
    FOREIGN KEY (transferred_by_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_inventory_transfer_from ON inventory_transfer(from_property_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transfer_to ON inventory_transfer(to_property_id);

-- 17. Update task table to support templates and assigned workers
ALTER TABLE task ADD COLUMN template_id TEXT REFERENCES task_template(id);
ALTER TABLE task ADD COLUMN assigned_to_id TEXT REFERENCES users(id);
ALTER TABLE task ADD COLUMN estimated_duration INTEGER;
ALTER TABLE task ADD COLUMN actual_duration INTEGER;

CREATE INDEX IF NOT EXISTS idx_task_assigned_to ON task(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_task_template ON task(template_id);

-- 18. Update invoice table to support more fields
ALTER TABLE invoice ADD COLUMN status TEXT DEFAULT 'pending';
ALTER TABLE invoice ADD COLUMN paid_at DATETIME;
ALTER TABLE invoice ADD COLUMN notes TEXT;
ALTER TABLE invoice ADD COLUMN worker_id TEXT REFERENCES users(id);

CREATE INDEX IF NOT EXISTS idx_invoice_worker ON invoice(worker_id);
CREATE INDEX IF NOT EXISTS idx_invoice_status ON invoice(status);
